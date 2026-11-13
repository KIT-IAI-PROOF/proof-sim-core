"""
This module contains the PROOF wrapper for running Functional Mock-up Units (FMUs) inside a PROOF
workflow. It loads an FMU from a file, initializes it with parameters from a configuration/parameter
file or static inputs, advances it over time in each step() call, and publishes the results as
fmu_output_json / fmu_output_csv plus one attribute per FMU output variable.
"""
from sys import exit
from typing import Dict, Any
import inspect
import json
import os
import shutil

import numpy as np
import ast
import asyncio
import traceback

# FMU specific imports
from fmpy import simulate_fmu, read_model_description, extract, plot_result, instantiate_fmu
from fmpy.simulation import apply_start_values as fmpy_apply_start_values

from proofcore.base import cliargparser
from proofcore.base.basewrapper import BaseWrapper, main
from proofcore.models.BlockStatus import BlockStatus
from proofcore.util.proofLogging import Logger, HandlerType
from proofcore.util.StringHelper import StringHelper
from proofcore.models.SimulationPhase import SimulationPhase

options, arguments = cliargparser.parse_known_args()

log_file_name = "proof_BaseFmuRunner_" + str(options.local_block_id) + ".log"
# Use of the custom PROOF logger. Each file has its own logger.
logger = Logger('BaseFmuRunnerLogger', handlers = [HandlerType.FILE], logging_dir=options.loggingDir, log_file_name = log_file_name, log_level=options.logLevel).get_logger()


class BaseFmuRunner(BaseWrapper):
    """
    The BaseFmuRunner class runs an FMU in PROOF.

    The FMU is advanced in each step() call, and each execution exposes the results as the
    fmu_output_json and fmu_output_csv attributes as well as one attribute per FMU output variable
    (whose names must be registered in the workflow descriptor outputs).
    A list of values can be used for a dynamic input (fmu_input_values) to simulate multiple FMU time
    steps in a single PROOF step() execution. The FMU communication step size can be provided either
    as a static input (fmu_step_size) or via the configuration file's metadata.
    """
    def __init__(self, options=options) -> None:
        # Static inputs
        self.fmu_name = None
        self.fmu_file_path = ""
        self.fmu_step_size = ""  # in minutes
        self.fmu_output_interval = None  # output interval in minutes; defaults to fmu_step_size if not set
        # FMU Configuration:
        # Either from static inputs or config file
        self.parameter_dict = {}
        self.input_dict = {}
        self.output_list = []
        self.license_file_name = None
        self.config_file_name = None
        # Values of the dynamic inputs
        self.fmu_input_values = None
        # Dynamic outputs
        self.fmu_output_json = ""
        self.fmu_output_csv = ""

        # additional variables
        self.fmu_instance = None
        self.unzipdir = None
        self.model_description = None
        self.current_fmu_time = 0.0
        self._variables_map = {}  # variable name -> (valueReference, type)
        self._string_helper = StringHelper(logger=logger, header_requested=False)
        super(BaseFmuRunner, self).__init__(bwoptions=options)
        # Output attribute names are fixed for this wrapper; not user-configurable via -o.
        #self.outputs = ["fmu_output_json", "fmu_output_csv"]

    async def _notify_error(self, phase: SimulationPhase, status: BlockStatus, message: str) -> None:
        logger.error(message)
        await self.send_notify(phase, status, error_text=message)

    # Build file path:
    # 1. Search for the file in userdata_directory
    # 2. Else search in the directory of the file defining the (child) wrapper class
    def _resolve_file_path(self, file_name: str) -> str:
        """Return the path for file_name, checking userdata_directory first and falling back to the child wrapper's directory."""
        primary_path = os.path.abspath(os.path.join(self.userdata_directory, file_name))
        if os.path.exists(primary_path):
            logger.debug(f"Found '{file_name}' in userdata: {primary_path}")
            return primary_path
        file_path = os.path.dirname(os.path.abspath(inspect.getfile(type(self))))
        fallback_path = os.path.join(file_path, file_name)
        logger.debug(f"'{file_name}' not found in provided userdata path '{primary_path}', using file location fallback: {fallback_path}")
        return fallback_path

    def _apply_start_values_direct(self, input_dict: dict) -> None:
        """Set FMU variables directly via value references, bypassing fmpy's cached shape validation.
        Needed when array variable dimensions changed due to a structural parameter update."""
        _PYTHON_TYPE = {
            'Float32': float, 'Float64': float,
            'Int8': int, 'Int16': int, 'Int32': int, 'Int64': int,
            'UInt8': int, 'UInt16': int, 'UInt32': int, 'UInt64': int,
            'Boolean': bool, 'String': str,
        }
        for name, value in input_dict.items():
            entry = self._variables_map.get(name)
            if entry is None:
                logger.warning(f"Input parameter '{name}' not found in FMU, skipping.")
                continue
            vr, type_name = entry
            setter = getattr(self.fmu_instance, f'set{type_name}', None)
            if setter is None:
                logger.warning(f"No setter for type '{type_name}' (variable '{name}'), skipping.")
                continue
            py_type = _PYTHON_TYPE.get(type_name, float)
            if isinstance(value, str):
                values = [py_type(x) for x in value.split()]
            elif isinstance(value, (list, tuple)):
                values = [py_type(x) for x in value]
            else:
                values = [py_type(value)]
            setter([vr], values)
            logger.debug(f"Applied input parameter '{name}' = {values}")

    def _parse(self, io_definition):
        """Parse io_definition if it's a string, otherwise return as-is.
        
        Returns:
            [parsed_value, True] on success
            [error_message, False] on parse failure
        """
        try:
            # Transform to dict, resp. list.
            if isinstance(io_definition, str):
                parsed = ast.literal_eval(io_definition)
                return [parsed, True]
            else:
                return [io_definition, True]

        except Exception as e:
            err_txt = f"Error parsing string '{io_definition}': {e}\n{traceback.format_exc()}"
            return [err_txt, False]

    async def init(self, **kwargs) -> None:
        # Import the parameters for the FMU
        if (self.config_file_name != None):
            try:
                config_file_path = self._resolve_file_path(self.config_file_name)
                with open(config_file_path) as f:
                    self.parameters = json.load(f)
                if self.fmu_name not in self.parameters:
                    raise ValueError(f"FMU name '{self.fmu_name}' not found in configuration file '{self.config_file_name}'. Available keys: {list(self.parameters.keys())}")
                self.parameters = self.parameters[self.fmu_name]
            except (FileNotFoundError, KeyError, json.JSONDecodeError, ValueError) as e:
                err_txt = f"Error reading configuration file: {e}\n{traceback.format_exc()}"
                await self._notify_error(SimulationPhase.INIT, BlockStatus.ERROR_INIT, err_txt)
                return

            try:
                # Set the license environment variable from metadata if not provided
                if (self.license_file_name == None and "License" in self.parameters["metadata"]):
                    self.license_file_name = self.parameters["metadata"]["License"]

                # Prefer inputs, as backup extract from the parameters 
                if (self.fmu_file_path == ""):
                    self.fmu_file_path = self.parameters["metadata"]["fmu_directory"]
                if (self.fmu_step_size == ""):
                    if "fmu_step_size" in self.parameters["metadata"]:
                        self.fmu_step_size = self.parameters["metadata"]["fmu_step_size"]
            except KeyError as e:
                err_txt = f"Required metadata missing in configuration: {e}\n{traceback.format_exc()}"
                await self._notify_error(SimulationPhase.INIT, BlockStatus.ERROR_INIT, err_txt)
                return

            # Extract parameters (static inputs), in- and outputs 
            if (self.parameter_dict == {}):
                self.parameter_dict = self.parameters['parameter_dict']
            if (self.input_dict == {}):
                self.input_dict = self.parameters['input_dict']
            if (self.output_list == []):
                self.output_list = self.parameters['output_list']

        fmu_name = "" if (self.fmu_name == None) else self.fmu_name
        logger.info(f"Initializing FMU '{fmu_name}' with\nparameters: {self.parameter_dict},\ninputs: {self.input_dict},\noutputs: {self.output_list}")

        if (self.fmu_step_size == ""):
            logger.debug("fmu_step_size not provided, using default of 15 minutes")
            self.fmu_step_size = 15  # default step size in minutes

        [parsed_param, param_parse_success] = self._parse(self.parameter_dict)
        [parsed_input, input_parse_success] = self._parse(self.input_dict)
        [parsed_output, output_parse_success] = self._parse(self.output_list)
        if (not param_parse_success or not input_parse_success or not output_parse_success) :
            err_txt = parsed_param if not param_parse_success else ""
            err_txt += parsed_input if not input_parse_success else ""
            err_txt += parsed_output if not output_parse_success else ""
            await self._notify_error(SimulationPhase.INIT, BlockStatus.ERROR_INIT, err_txt)
            return

        self.parameter_dict = parsed_param
        self.input_dict = parsed_input
        self.output_list = parsed_output

        # There must be at least one in- or output!
        if (len(self.input_dict)==0 and len(self.output_list)==0):
            err_txt = f"Neither in- nor outputs given for FMU {fmu_name}!"
            await self._notify_error(SimulationPhase.INIT, BlockStatus.ERROR_INIT, err_txt)
            return

        # Set the license file.
        try:
            # Set the license file if provided
            if (self.license_file_name != None):
                os.environ['TLKLICENSE'] = self._resolve_file_path(self.license_file_name)
        except Exception as e:
            err_txt = f"Error setting license file from path '{self.license_file_name}': {e}\n{traceback.format_exc()}"
            await self._notify_error(SimulationPhase.INIT, BlockStatus.ERROR_INIT, err_txt)
            return

        # Read the FMU model description
        try:
            # Get absolute fmu file path
            abs_fmu_file_path = self._resolve_file_path(self.fmu_file_path)
            if not os.path.isfile(abs_fmu_file_path):
                err_txt = f"Please provide the fmu file path. Provided path '{self.fmu_file_path}' (resolved to {abs_fmu_file_path})' is not a file!"
                logger.error(err_txt)
                await self._notify_error(SimulationPhase.INIT, BlockStatus.ERROR_INIT, err_txt)
                return
            self.unzipdir = extract(abs_fmu_file_path)
            self.model_description = read_model_description(self.unzipdir)
            self.fmu_instance = instantiate_fmu(unzipdir=self.unzipdir, model_description=self.model_description)
            self._variables_map = {
                v.name: (v.valueReference, v.type)
                for v in self.model_description.modelVariables
            }
            logger.debug(f"Built variable reference map with {len(self._variables_map)} entries")
        except Exception as e:
            err_txt = f"Error reading FMU model description from fmu_file_path '{self.fmu_file_path}': {e}\n{traceback.format_exc()}"
            await self._notify_error(SimulationPhase.INIT, BlockStatus.ERROR_INIT, err_txt)
            return

        # Initialize the FMU with parameters.
        try:
            if self.model_description.fmiVersion.startswith('2'):
                self.fmu_instance.setupExperiment(startTime=0.0)
                self.fmu_instance.enterInitializationMode()
                fmpy_apply_start_values(self.fmu_instance, self.model_description, self.parameter_dict)
            else:
                # FMI 3.0+: structural parameters must be set in configuration mode BEFORE enterInitializationMode
                structural_names = {
                    v.name for v in self.model_description.modelVariables
                    if v.causality == 'structuralParameter'
                }
                structural_input = {k: v for k, v in self.parameter_dict.items()
                                    if k in structural_names}
                non_structural_input = {k: v for k, v in self.parameter_dict.items()
                                        if k not in structural_names}
                if structural_input:
                    self.fmu_instance.enterConfigurationMode()
                    fmpy_apply_start_values(self.fmu_instance, self.model_description, structural_input)
                    self.fmu_instance.exitConfigurationMode()
                    logger.debug(f"Structural parameters applied in configuration mode: {list(structural_input.keys())}")
                self.fmu_instance.enterInitializationMode(startTime=0.0)
                # Apply non-structural start values directly to avoid fmpy's stale
                # shape cache when array dimensions changed via structural parameters.
                self._apply_start_values_direct(non_structural_input)
            self.fmu_instance.exitInitializationMode()
            logger.debug("FMU initialized successfully")
        except Exception as e:
            err_txt = f"Error initializing FMU: {e}\n{traceback.format_exc()}"
            await self._notify_error(SimulationPhase.INIT, BlockStatus.ERROR_INIT, err_txt)
            return

        # Call the parent class's init method
        try:
            await super(BaseFmuRunner, self).init(BlockStatus.INITIALIZED)
        except Exception as e:
            err_txt = f"An error occurred in init: {e}\n{traceback.format_exc()}"
            await self._notify_error(SimulationPhase.INIT, BlockStatus.ERROR_INIT, err_txt)

    def _parse_input_values(self, fmu_input_values: str, all_input_keys) -> list:
        """
        Parse fmu_input_values into a list of rows for the FMU input signal.

        Dispatches on the last line's leading character:
        - Starts with '[' or '{': a Python literal, e.g. "[1.0, 2.0]", "[[1,2],[3,4]]",
          "[{'a': 1}]" - parsed with ast.literal_eval (only the last line is used).
        - Otherwise: a headerless CSV line, e.g. "0,1,2" - fields are mapped positionally
          onto all_input_keys, in order (1st field -> 1st key, etc.).
        Falls back to the configured input_dict start values when fmu_input_values is empty.
        """
        rows = fmu_input_values.splitlines() if fmu_input_values else []
        input_values = rows[-1] if rows else ""
        logger.debug(f"input_values: {input_values}")

        if input_values:
            if input_values.lstrip().startswith(("[", "{")):
                parsed = ast.literal_eval(input_values)
                return parsed if isinstance(parsed, list) else [parsed]
            logger.debug(f"'{input_values}' is not a Python literal, parsing '{fmu_input_values}' as CSV instead")
            if not all_input_keys:
                logger.warning("fmu_input_values is set but no input keys are configured; parsed values will not be applied to the FMU.")
            # For the base_fmu_runner we assume all values always to be given!
            fields = self._string_helper.parse_row(input_values)
            if len(fields) != len(all_input_keys):
                logger.debug(f"Field count {len(fields)} does not match input key count {len(all_input_keys)} for row '{input_values}'")
            return [dict(zip(all_input_keys, fields))]
        elif isinstance(self.input_dict, dict) and len(self.input_dict) > 0:
            # Use start values provided for inputs
            return [list(self.input_dict.values())]
        return []

    async def step(self, **kwargs) -> None:
        logger.debug("step() -> FMU_runnerWrapper executed the step method")

        logger.debug(f"Communication_point {self.communication_point}: fmu_input_values:\n{self.fmu_input_values}")

        string_keys = []
        numeric_keys = []
        input_data = None
        input_values = None

        try:
            all_input_keys = []
            if isinstance(self.input_dict, dict):
                all_input_keys = list(self.input_dict.keys())
            elif isinstance(self.input_dict, list):
                all_input_keys = self.input_dict

            logger.debug(f"input keys: {all_input_keys}")

            input_values = self._parse_input_values(self.fmu_input_values, all_input_keys)
            logger.debug(f"Parsed input_values: {input_values}")
            logger.debug(f"input_dict: {self.input_dict}")

            if input_values: 

                # Separate String variables — simulate_fmu does not support them in the signal array
                string_keys = [k for k in all_input_keys if self._variables_map.get(k, (None, ''))[1] == 'String']
                numeric_keys = [k for k in all_input_keys if k not in string_keys]

                logger.debug(f"Numeric input variables: {numeric_keys}")
                if string_keys:
                    logger.debug(f"String input variables (set via setString, not signal array): {string_keys}")

                # Use explicit computation instead of np.arange to avoid floating-point
                # accumulation errors (e.g. np.arange(0.032, 0.036, 0.004) returns [0.032, 0.036])
                times = np.array([self.current_fmu_time + i * self.fmu_step_size
                                    for i in range(len(input_values))])
                logger.debug("times: " + str(times))

                # Map FMI 3.0 variable types to numpy dtypes to preserve integer precision
                _FMI_DTYPE = {
                    'Float32': np.float32, 'Float64': np.float64,
                    'Int8': np.int8,   'Int16': np.int16,  'Int32': np.int32,  'Int64': np.int64,
                    'UInt8': np.uint8, 'UInt16': np.uint16, 'UInt32': np.uint32, 'UInt64': np.uint64,
                    'Boolean': np.uint8, 'Enumeration': np.int32,
                }

                # Detect array-valued inputs (e.g. FMI 3.0 vector variables passed as lists)
                array_sizes: dict = {}
                first_row = input_values[0]
                if isinstance(first_row, dict):
                    for key in numeric_keys:
                        v = first_row.get(key)
                        if isinstance(v, (list, tuple)):
                            array_sizes[key] = len(v)
                elif isinstance(first_row, (list, tuple)):
                    for col_idx, key in enumerate(numeric_keys):
                        if col_idx < len(first_row):
                            v = first_row[col_idx]
                            if isinstance(v, (list, tuple)):
                                array_sizes[key] = len(v)

                dtype = [('time', np.float64)] + [
                    (key, _FMI_DTYPE.get(self._variables_map.get(key, (None, 'Float64'))[1], np.float64),
                        (array_sizes[key],)) if key in array_sizes
                    else (key, _FMI_DTYPE.get(self._variables_map.get(key, (None, 'Float64'))[1], np.float64))
                    for key in numeric_keys
                ]
                input_data = np.zeros(len(input_values), dtype=dtype)
                input_data['time'] = times
                if numeric_keys:
                    if isinstance(input_values[0], dict):
                        # Dict rows: each row is {key: value}; missing keys fall back to input defaults.
                        defaults = self.input_dict
                        for key in numeric_keys:
                            if isinstance(defaults, dict):
                                default_val = defaults.get(key, 0)
                            else:
                                default_val = 0
                            col_vals = [row.get(key, default_val) for row in input_values]
                            base_dt = _FMI_DTYPE.get(self._variables_map.get(key, (None, 'Float64'))[1], np.float64)
                            input_data[key] = np.array(col_vals, dtype=base_dt)
                    elif isinstance(input_values[0], (list, tuple)):
                        # Legacy positional rows ordered by all_inputs_keys.
                        for key in numeric_keys:
                            col_idx = all_input_keys.index(key)
                            col_vals = [row[col_idx] for row in input_values]
                            base_dt = _FMI_DTYPE.get(self._variables_map.get(key, (None, 'Float64'))[1], np.float64)
                            input_data[key] = np.array(col_vals, dtype=base_dt)
                    else:
                        input_data[numeric_keys[0]] = np.array(
                            input_values, dtype=input_data.dtype[numeric_keys[0]])
                logger.debug("Input_data for the FMU: " + str(input_data))

        except Exception as e:
            raise ValueError(f"Error parsing input '{input_values}' and creating fmu input_signal: {e}")

        try:
            if input_values:
                stop_time = times[-1] + self.fmu_step_size
            else:
                stop_time = self.current_fmu_time + self.fmu_step_size
            num_time_steps = int((stop_time - self.current_fmu_time) / self.fmu_step_size)
            logger.debug(f"Simulating {num_time_steps} steps of the FMU from {self.current_fmu_time} to {stop_time} with step size {self.fmu_step_size}")

            # fmpy requires >= 2 time points in the input signal array for its interpolation to work
            # correctly (it returns the full 2D table when t.size < 2, causing a shape mismatch).
            # When input_data has only one row, duplicate it at stop_time (same values, constant hold).
            if input_data is not None and len(input_data) == 1:
                extra = np.copy(input_data)
                extra['time'] = stop_time
                input_data = np.concatenate([input_data, extra])
                logger.debug("Duplicated single-row input_data to satisfy fmpy's >= 2 time-point requirement")

            # Apply String inputs directly before simulate_fmu (not supported in signal array)
            if string_keys:
                vrs = [self._variables_map[k][0] for k in string_keys]
                if input_values and isinstance(input_values[0], dict):
                    # Dict rows: look up by key name, fall back to input default.
                    defaults = self.input_dict
                    values = [str(input_values[0].get(k, defaults.get(k, ''))) for k in string_keys]
                elif input_values and isinstance(input_values[0], (list, tuple)):
                    # Legacy positional rows.
                    values = [
                        str(input_values[0][all_input_keys.index(k)])
                        for k in string_keys
                    ]
                else:
                    values = [self.input_dict.get(k, '') for k in string_keys]
                self.fmu_instance.setString(vrs, values)
                logger.debug(f"String inputs applied: {dict(zip(string_keys, values))}")

            logger.debug(f"==MM Input_data: {input_data}")
            result = simulate_fmu(filename=self.unzipdir,
                                model_description=self.model_description,
                                fmu_instance=self.fmu_instance,
                                start_time=self.current_fmu_time,
                                stop_time=stop_time,
                                output_interval=float(self.fmu_output_interval) if self.fmu_output_interval is not None else self.fmu_step_size,
                                start_values={},
                                input=input_data if numeric_keys else None,
                                output=self.output_list,
                                initialize=False,
                                terminate=False  # keep the FMU instance alive
                                )
            self.current_fmu_time = stop_time
            # Convert to a list of dictionaries
            list_of_dicts = [dict(zip(result.dtype.names, row)) for row in result]

            ## Prepare the output:
            # Take the last entry
            fmu_result = list_of_dicts[-1]
            
            # Convert to JSON using FMI convention: arrays as space-separated strings, scalars as native types
            def _serialize(v):
                if isinstance(v, np.ndarray):
                    return " ".join(str(x) for x in v.tolist())
                if isinstance(v, np.generic):
                    return v.tolist()
                return v

            # 1. Json
            self.fmu_output_json = json.dumps(fmu_result, default=_serialize)
            logger.info(f"FMU result: {self.fmu_output_json}")
            
            # 2. Csv
            csv_header = ""
            # only add header once
            if self.communication_point == 1:
                csv_header = ",".join(fmu_result.keys()) + "\n"
            csv_values = [_serialize(fmu_result[key]) for key in fmu_result.keys()]
            self.fmu_output_csv = csv_header + ",".join(str(v) for v in csv_values)

            # 3. Publish each FMU output variable onto self.<name> so the VALUE
            #    message (sent by BaseWrapper.step below via get_data()) carries the
            #    actual value instead of None. Only variables declared in self.outputs
            #    are relevant, but we map any FMU result column (excluding 'time').
            for name, value in fmu_result.items():
                if name == 'time':
                    continue
                setattr(self, name, _serialize(value))

            logger.debug("FMU output (json): " + str(self.fmu_output_json))
            logger.debug("FMU output (csv):  " + str(self.fmu_output_csv))

            
        except Exception as e:  # KeyError
            err_txt = f"An error occurred in step: {e}\n{traceback.format_exc()}"
            await self._notify_error(SimulationPhase.EXECUTE, BlockStatus.ERROR_STEP, err_txt)
       
        try:
            await super(BaseFmuRunner, self).step(BlockStatus.EXECUTION_STEP_FINISHED)
        except Exception as e:
            err_txt = f"An error occurred in step: {e}\n{traceback.format_exc()}"
            await self._notify_error(SimulationPhase.EXECUTE, BlockStatus.ERROR_STEP, err_txt)

    async def finalize(self, **kwargs) -> None:
        logger.debug("finalize() -> FMUExecutor executed the finalize method")
        try:

            self.fmu_instance.terminate()
            self.fmu_instance.freeInstance()
            shutil.rmtree(self.unzipdir)

            await super(BaseFmuRunner, self).finalize(BlockStatus.FINALIZED)
        except Exception as e:
            err_txt = f"An error occurred in finalize: {e}\n{traceback.format_exc()}"
            await self._notify_error(SimulationPhase.FINALIZE, BlockStatus.ERROR_FINALIZE, err_txt)

if __name__ == '__main__':
    try:
        asyncio.run(main(wrapper=BaseFmuRunner()))
    except KeyboardInterrupt:
        exit(0)
