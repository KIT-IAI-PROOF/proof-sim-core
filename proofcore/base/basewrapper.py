"""
 Copyright (c) 2025-2026
 Karlsruhe Institute of Technology - Institute for Automation and Applied Informatics (IAI)
"""
import argparse
import traceback
from datetime import datetime
from json import loads
from sys import stdin
from sys import stdout
from typing import List, Dict

from proofcore.models.BlockStatus import BlockStatus
from proofcore.models.MessageType import MessageType
from proofcore.models.NotifyMessage import NotifyMessage
from proofcore.models.SyncMessage import SyncMessage
from proofcore.models.ValueMessage import ValueMessage
from proofcore.models.SimulationPhase import SimulationPhase
from proofcore.util.proofLogging import Logger, HandlerType

from proofcore.base.SocketWriter import SocketWriter
from proofcore.base.SocketReader import SocketReader
import asyncio

HOST = "127.0.0.1"  # Standard loopback interface address (localhost)

"""
BaseWrapper class for PROOF python models.
Each PROOF model must extend this class and implement the necessary methods.
"""
class BaseWrapper:
    """
    The base class for all PROOF python models. All command line arguments must be loaded in the extending class.
    For a simplified creation of PROOF model class, a template class is provided which lists all necessary arguments
    """

    def __init__(self, bwoptions: argparse.Namespace) -> None:
        self.use_sockets = False
        # if there are ports given:  the logging must be performed using log files
        if bwoptions.ports:   # ports may not be given => empty list
            self.ports: List[int] = loads(bwoptions.ports)
            if self.ports:
                self.use_sockets = True
                self.portWrite = self.ports[0]
                self.portRead = self.ports[1]
                log_file_name = "proof_BaseWrapper_" + str(bwoptions.local_block_id) + "_" + str(self.portRead) + "_" + str( self.portWrite) + ".log"
                self.logger = Logger('BaseWrapperLogger', handlers = [HandlerType.FILE], logging_dir= bwoptions.loggingDir, log_file_name =log_file_name,
                                     log_level=bwoptions.logLevel).get_logger()
                self.logger.debug("__init__(bw) :  Ports: " + str(self.portRead) + " (READ), " + str(self.portWrite) + " (WRITE)" )
            else:
                log_file_name = "proof_BaseWrapper_" + str(bwoptions.local_block_id)  + ".log"
                self.logger = Logger('BaseWrapperLogger', handlers = [HandlerType.FILE], logging_dir= bwoptions.loggingDir, log_file_name =log_file_name, log_level=bwoptions.logLevel).get_logger()
                self.logger.debug("__init__(bw) :  logging to stdout ..." )

        self.userdata_directory = bwoptions.userdata_directory

        self.logger.debug("processing __init__")

        # communication point and step size will be set by the syncMessage
        self.communication_point = 0  # only one value for whole Workflow and set by a syncMessage in sync_function()
        self.communication_step_size = 0  # separate value for each Worker and set by a syncMessage in sync_function()

        # self.inputs and self.outputs are two lists of dictionaries
        self.inputs: List[str] = loads(bwoptions.inputs)
        self.outputs: List[str] = loads(bwoptions.outputs)

        try:
            if self.use_sockets:
                self.socket_reader = SocketReader(self.portRead, bwoptions.local_block_id, bwoptions.loggingDir, bwoptions.logLevel)
                self.socket_writer = SocketWriter(self.portWrite, bwoptions.local_block_id, bwoptions.loggingDir, bwoptions.logLevel)
                self.logger.debug("__INIT__::   Reader (server) and Writer (client) established")
                self.socket_writer.start()
                self.logger.debug("__INIT__::   Writer (client) started")
                self.socket_reader.start()
                self.logger.debug("__INIT__::   Reader (server) started")
        except Exception as e:
            err_txt = "An error occurred in __init__: " + str(e) + "\n" + str(traceback.format_exc())
            self.logger.debug(err_txt)
            self.send_init_notify(block_status=BlockStatus.ERROR_INIT, error_text=err_txt)

        self.do_reading = True
        # Default to True if waitForSync is not set (None), otherwise parse the value
        if bwoptions.waitForSync is not None:
            self.wait_for_sync = bwoptions.waitForSync.lower() == "true"
            self.logger.debug("waitForSync: " + str(self.wait_for_sync))
        else:
            err_txt = "Error in __init__: --waitForSync not provided!" + "\n" + str(traceback.format_exc())
            self.logger.debug(err_txt)
            self.send_init_notify(block_status=BlockStatus.ERROR_INIT, error_text=err_txt)

        self.logger.debug("__init__ passed, use sockets: " + str(self.use_sockets))
        self.send_init_notify(block_status=BlockStatus.CREATED, error_text='')

    async def init(self, status=None, error_text="") -> None:
        """
        Create and send an init message with parameters from Wrapper.
        Init is commonly used to initialize the Wrapper Model.
        Details must be implemented in the respective wrapper subclass.
        :param error_text: error message
        :param status: BlockStatus.INITIALIZED or BlockStatus.ERROR_INIT
        :return:
        """
        self.logger.debug("processing INIT")

        try:
            if status == BlockStatus.INITIALIZED or status is None:
                status = BlockStatus.INITIALIZED
                error_text = ""
                self.logger.debug(
                    "BaseWrapper init entered and initialized, sending NOTIFY with status=BlockStatus.INITIALIZED")
            elif status == BlockStatus.ERROR_INIT:
                error_text = "init error: " + error_text + "\n" + str(traceback.format_exc())
                self.logger.debug(
                    "BaseWrapper init entered and an error occurred, sending NOTIFY with status=BlockStatus.ERROR_INIT "
                    "and errorText=%s", error_text)
            else:
                error_text = "init error: wrong BlockStatus" + str(status) + ("! Use either "
                                                                              "BlockStatus.INITIALIZED or "
                                                                              "BlockStatus.ERROR_INIT")
                status = BlockStatus.ERROR_INIT
                self.logger.debug("An error occurred, sending NOTIFY with status=%s and errorText=%s", status, error_text)

            await self.send_notify(SimulationPhase.INIT, block_status=status, error_text=error_text)
        except Exception as e:
            err_txt = "An error occurred in init: " + str(e) + "\n" + str(traceback.format_exc())
            self.logger.debug(err_txt)
            await self.send_notify(SimulationPhase.INIT, BlockStatus.ERROR_INIT, error_text=err_txt)
        return

    async def step(self, status=None, error_text="") -> None:
        """
        Create and send a step message with parameters from Wrapper.
        step is commonly used to advance the Wrapper Model by one time step.
        Details must be implemented in the respective wrapper subclass.
        :param error_text:
        :param status: BlockStatus.EXECUTION_STEP_FINISHED or BlockStatus.EXECUTION_FINISHED
        :return:
        """
        self.logger.debug("processing STEP, outputs: " + str(self.outputs))
        try:
            # check whether outputs exist and are not empty:
            if self.outputs:
                self.logger.debug("=====> BaseWrapper::step(): STEP executed, outputs exist -> sending VALUE Message!")
                value = await self.send_value(phase=SimulationPhase.EXECUTE)
            else:
                self.logger.debug(
                    "\n=====> BaseWrapper::step(): STEP executed, outputs do not exist -> NOT sending VALUE Message!")

            if status == BlockStatus.EXECUTION_STEP_FINISHED or status is None:
                status = BlockStatus.EXECUTION_STEP_FINISHED
                error_text = ""
                self.logger.debug("Sending NOTIFY with status=BlockStatus.EXECUTION_STEP_FINISHED")
            elif status == BlockStatus.EXECUTION_FINISHED:
                self.logger.debug("Sending NOTIFY with status=BlockStatus.EXECUTION_FINISHED")
            elif status == BlockStatus.ERROR_STEP:
                error_text = "step error: " + error_text + "\n" + str(traceback.format_exc())
                self.logger.debug("An error occurred, sending NOTIFY with status=%s and errorText=%s", status, error_text)
            else:
                error_text = "step error: wrong BlockStatus " + str(status) + ("! Use one of "
                                                                               "BlockStatus.EXECUTION_STEP_FINISHED, "
                                                                               "BlockStatus.EXECUTION_FINISHED or "
                                                                               "BlockStatus.ERROR_STEP")
                status = BlockStatus.ERROR_STEP
                self.logger.debug("An error occurred, sending NOTIFY with status=%s and errorText=%s", status, error_text)

            await self.send_notify(SimulationPhase.EXECUTE, block_status=status, error_text=error_text)
            self.logger.debug("NOTIFY Message sent ...")
        except Exception as e:
            err_txt = "An error occurred in step: " + str(e) + "\n" + str(traceback.format_exc())
            self.logger.debug(err_txt)
            await self.send_notify(SimulationPhase.EXECUTE, BlockStatus.ERROR_STEP, error_text=err_txt)
        return

    async def finalize(self, status=None, error_text="") -> None:
        """
        Create and send a finalize message with parameters from Wrapper.
        Finalize is commonly used to delete temporary files and free memory after the simulation is finished.
        Details must be implemented in the respective wrapper subclass.
        :param status: should be BlockStatus.FINALIZED
        :param error_text: error message
        :return: None
        """
        """
            strategische Entscheidung: sollen abschließende Werte gesendet werden oder nicht
        """
        self.logger.debug("processing FINALIZE")
        try:
            # value = self.send_value(phase=SimulationPhase.FINALIZED)
            if status == BlockStatus.FINALIZED or status is None:
                status = BlockStatus.FINALIZED
                error_text = ""
                self.logger.debug("Sending NOTIFY with status=BlockStatus.FINALIZED")
            elif status == BlockStatus.ERROR_FINALIZE:
                error_text = "finalize error: " + error_text + "\n" + str(traceback.format_exc())
                self.logger.debug("An error occurred, sending NOTIFY with status=%s and errorText=%s", status, error_text)
            else:
                error_text = "finalize error: wrong BlockStatus " + str(status) + ("! Use either "
                                                                                   "BlockStatus.FINALIZED or "
                                                                                   "BlockStatus.ERROR_FINALIZE")
                status = BlockStatus.ERROR_FINALIZE
                self.logger.debug(
                    "An error occurred, sending NOTIFY with status=%s and errorText=%s", status, error_text)

            await self.send_notify(SimulationPhase.FINALIZE, block_status=status, error_text=error_text)
        except Exception as e:
            err_txt = "An error occurred in finalize: " + str(e) + "\n" + str(traceback.format_exc())
            self.logger.debug(err_txt)
            await self.send_notify(SimulationPhase.FINALIZE, BlockStatus.ERROR_FINALIZE, error_text=err_txt)

    async def shut_down(self, status=None, error_text="") -> None:
        """
        Shut down the Wrapper and send a notify message.
        Finalize is commonly used to shut down and exit the Wrapper.
        Details must be implemented in the respective wrapper subclass.
        :param status: should be BlockStatus.SHUTDOWN
        :param error_text: error message
        :return: None
        """
        """
            strategische Entscheidung: soll ein abschließende Werte gesendet werden oder nicht
        """
        self.logger.info("shutting down after waiting for 2 seconds to be able to send a NotifyMessage to the Controller)")
        await self.send_notify(SimulationPhase.SHUTDOWN, block_status=BlockStatus.SHUT_DOWN, error_text=error_text)
        self.logger.info("now shutting down in 2 seconds")
        self.do_reading = False
        if self.use_sockets:
            self.socket_reader.stop()
            self.socket_writer.stop()

        await asyncio.sleep(2)
        exit(0)


    async def get_data(self) -> Dict:
        """
        Get data from the wrapper class.
        :return: Dict
        """
        result = {}
        for obj in self.outputs:
            if hasattr(self, obj):
                result[obj] = getattr(self, obj)
            else:
                pass

        return result

    async def set_variables(self, variables: Dict, phase: SimulationPhase) -> None:
        """
        set attributes of the respective wrapper class according to the variables' dictionary.
        local variables are set to the incoming variables dictionary.
        :param variables: values coming from the ValueMessage.data
        :return: None
        """
        for key, value in variables.items():
            setattr(self, key, value)
        
        if phase == SimulationPhase.EXECUTE:
            if self.wait_for_sync:
                self.logger.debug(f"waiting for SYNC, then sending value, CP " + str(self.communication_point))
            else:
                self.logger.info( "Do not wait for a SYNC, performing step directly ..." )
                await self.step()


    async def send_value(self, phase: SimulationPhase) -> ValueMessage:
        """
        Create and send a value message with parameters from Wrapper.
        :param phase: may be SimulationPhase.EXECUTE or SimulationPhase.FINALIZE
        :return: ValueMessage
        """
        try:
            value = ValueMessage(
                time=round(datetime.now().timestamp() * 1000), #int(datetime.now().timestamp() * 1000),
                type=MessageType.VALUE,
                phase=phase,
                data=await self.get_data(),
                communicationPoint=self.communication_point
            )
            self.logger.debug("BaseWrapper.send_value() valueMessage to be sent: " + str(value))
            if self.use_sockets:
                self.socket_writer.send(value.model_dump_json() + '\n')
                self.logger.debug("BaseWrapper.send_value() valueMessage sent via Sockets")
            else:
                stdout.write(value.model_dump_json() + '\n')
                stdout.flush()
                self.logger.debug("BaseWrapper.send_value() valueMessage sent via STDOUT")

            return value
        except Exception as e:
            err_txt = "An error occurred in send_value: " + str(e) + "\n" + str(traceback.format_exc())
            self.logger.debug(err_txt)
            await self.send_notify(phase, BlockStatus.ERROR_STEP, error_text=err_txt)

    async def send_notify(self, phase: SimulationPhase, block_status: BlockStatus, error_text: str) -> None:
        """
        Create and send a notify message with parameters from Wrapper.
        :param phase: SimulationPhase of the notify message, e.g. SimulationPhase.INIT, SimulationPhase.EXECUTE, SimulationPhase.FINALIZE, SimulationPhase.SHUTDOWN
        :param block_status: BlockStatus of the notify messag
        :return: NotifyMessage
        """
        self.logger.debug("BaseWrapper.send_notify() entered ... CP=" + str(self.communication_point))
        try:
            notify = NotifyMessage(
                time=round(datetime.now().timestamp() * 1000), #int(datetime.now().timestamp() * 1000),
                type=MessageType.NOTIFY,
                phase=phase,
                status=block_status,
                communicationPoint=self.communication_point,
                errorText=error_text
            )
            self.logger.debug("BaseWrapper.send_notify() notify message: " + str(notify))

            if self.use_sockets:
                self.logger.debug("BaseWrapper:: sending notify to socket ..." + str(notify.model_dump_json()))
                self.socket_writer.send(notify.model_dump_json() + '\n')
            else:
                self.logger.debug("BaseWrapper:: sending notify to stdout ..." + str(notify.model_dump_json()))
                stdout.write(notify.model_dump_json() + '\n')
                stdout.flush()

            self.logger.debug("BaseWrapper.send_notify() passed, returning ...")
            return #notify
        except Exception as e:
            err_txt = "An error occurred in send_notify: " + str(e) + "\n" + str(traceback.format_exc())
            self.logger.debug(err_txt)
            await self.send_notify(phase, BlockStatus.ERROR_STEP, error_text=err_txt)


    def send_init_notify(self, block_status: BlockStatus, error_text: str) -> None:
        """
        Create and send a notify message with parameters from Wrapper at initialization.
        :param block_status : BlockStatus of the notify message
        :param error_text: error message
        """
        notify = NotifyMessage(
            time=round(datetime.now().timestamp() * 1000),  # int(datetime.now().timestamp() * 1000),
            type=MessageType.NOTIFY,
            phase=SimulationPhase.INIT,
            status=block_status,
            communicationPoint=self.communication_point,
            errorText=error_text
        )
        self.logger.debug("init notify message: " + str(notify))

        if self.use_sockets:
            self.logger.debug("sending notify to socket ..." + str(notify.model_dump_json()))
            self.socket_writer.send(notify.model_dump_json() + '\n')
        else:
            self.logger.debug("sending notify to stdout ..." + str(notify.model_dump_json()))
            stdout.write(notify.model_dump_json() + '\n')
            stdout.flush()


async def value_function(message: ValueMessage, wrapper: BaseWrapper) -> None:
    """
    Uses wrapper and ValueMessage to set variables in Model.
    ValueMessage.data is a dictionary with the variables as keys.
    :param message: ValueMessage received from the Worker/Orchestrator
    :param wrapper: Instance of the respective Wrapper class
    :return: None
    """
    wrapper.communication_point = message.communicationPoint
    wrapper.logger.debug("value_function: " + str(message.data) + ", CP=" + str(wrapper.communication_point))

    try:
        type(message.data) == Dict
    except TypeError as e:
        raise TypeError(f"Message.data must be of type dict, but is {type(message.data)}") from e
    await wrapper.set_variables(variables=message.data, phase=message.phase)


async def sync_function(message: SyncMessage, wrapper: BaseWrapper) -> None:
    """
    Function to call one of the three phases of a step: init, step, finalize.
    Each function is performed in a separate thread.
    :param message: SyncMessage received from the Worker/Orchestrator
    :param wrapper: Instance of the respective Wrapper class
    :return: None
    """
    wrapper.logger.debug("sync_function(1): message " + str(message))
    try:
        wrapper.logger.debug("sync_function: communicationPoint " + str(message.communicationPoint))
        wrapper.communication_point = message.communicationPoint
        wrapper.communication_step_size = message.communicationStepSize

        workflow_phase_actions = {
            SimulationPhase.INIT.value: wrapper.init,
            SimulationPhase.EXECUTE.value: wrapper.step,
            SimulationPhase.FINALIZE.value: wrapper.finalize,
            SimulationPhase.SHUTDOWN.value: wrapper.shut_down
        }

        step_function = workflow_phase_actions.get(message.phase.value)
        #wrapper.logger.debug("Function to perform: " + str(step_function))

        if step_function == wrapper.init:
            wrapper.logger.debug("performing wrapper.init() ")
            await wrapper.init()
            wrapper.logger.debug("wrapper.init() awaited ")
        elif step_function == wrapper.step:
            # Only perform step here if wait_for_sync is active, else it is performed directly 
            # when values arrive (in set_variables())
            if wrapper.wait_for_sync:
                wrapper.logger.debug("performing wrapper.step() ")
                await wrapper.step()
                wrapper.logger.debug("wrapper.step() awaited ")
            else:
                wrapper.logger.debug("Skipping wrapper.step() because wait_for_sync is False ")
        elif step_function == wrapper.finalize:
            wrapper.logger.debug("performing wrapper.finalize() ")
            await wrapper.finalize()
            wrapper.logger.debug("wrapper.finalize() awaited ")
        elif step_function == wrapper.shut_down:
            await wrapper.shut_down()

    except (OSError, Exception) as e:
        wrapper.logger.debug(f"ERROR performing {step_function}!" + str(e) )
        await wrapper.send_notify(message.phase, BlockStatus.ERROR_STEP, str(e))

    #RL
    # wrapper.logger.debug("creating SYNC Thread ...")
    # try:
    #     x = Thread(target=step_function, args=())
    #     wrapper.logger.debug("starting SYNC Thread ... running threads: " + str(threading.active_count()))
    #     x.start()
    #     wrapper.logger.debug("joining SYNC Thread ... ")
    #     x.join()
    # except Exception as e:
    #     wrapper.logger.debug("-except: handling an exception" + str(e))
    # RL

# Action maps possible incoming values (as a string) to the respective Dataclass.
# Listed in the Dict are all possible Message Types that the basewrapper can receive or send.
# Once received, the Messages are initialized as Objects of respective Dataclass for more convenient usage.
message_interpretation_actions = {
    MessageType.VALUE.value: ValueMessage,
    MessageType.SYNC.value: SyncMessage,
    MessageType.NOTIFY.value: None
}

# Action maps possible incoming values (as a string) to the respective Dataclass.
# Listed in the Dict are all possible Message Types that the basewrapper can receive or send.
# Once received, the Messages are initialized as Objects of respective Dataclass for more convenient usage.
message_function_actions = {
    MessageType.VALUE.value: value_function,
    MessageType.SYNC.value: sync_function
}

"""
Main is looking for the messages coming from the worker.
"""


async def main(wrapper) -> None:
    """
    read the input message and decide, which function should be executed
    """
    wrapper.logger.debug("BaseWrapper: The main method gets executed, waiting for input ... ")
    message = ""
    if wrapper.use_sockets:
        wrapper.logger.debug("MAIN::   reading from and writing to SOCKETS")
        while True:
            response = wrapper.socket_reader.listen()

            if not response:
                wrapper.logger.debug("MAIN::   no response")
                break
            if not response.strip():
                wrapper.logger.debug("MAIN::   no response.strip()")
                continue
            wrapper.logger.debug("MAIN::   loading JSON message ... >>" + str(response) + "<<")
            message = loads(response)
            wrapper.logger.debug("MAIN::   JSON message loaded ... ")

            try:
                wrapper.logger.debug("message arrived: " + str( message) + "\ntype: " + str(type(message)))
                if "MSGSIZE" in message:
                    size = message["MSGSIZE"]
                    wrapper.logger.debug("setting new READ size forSocketReader to " + str(size))
                    wrapper.socket_reader.set_msg_size(int(size))
                    #continue
                elif message['type'] == "SYNC":
                    sync_msg = SyncMessage(**message)
                    wrapper.logger.debug("type of message:" + str(type(sync_msg)))
                    wrapper.logger.debug("starting sync_function ... ")
                    await sync_function(message=sync_msg,wrapper=wrapper)
                    wrapper.logger.debug("sync_function awaited ")

                elif message['type'] == "VALUE":
                    value_msg = ValueMessage(**message)
                    wrapper.logger.debug("BaseWrapper: type of message:" + str(type(value_msg)))
                    wrapper.logger.debug("BaseWrapper: starting value_function ... ")
                    await value_function(message=value_msg,wrapper=wrapper)
                    wrapper.logger.debug("value_function awaited ")
                else:
                    wrapper.logger.debug("BaseWrapper: unknown message type")
                    wrapper.logger.debug("BaseWrapper: unknown message type: " + str(message['type']))
                    continue
            except Exception as e:
                wrapper.logger.debug("Error in main: " + str(e))
                continue

            # if "MSGSIZE" in message:
            #     size = message["MSGSIZE"]
            #     wrapper.logger.debug("BaseWrapper: setting new READ size forSocketReader to " + str(size))
            #     wrapper.socket_reader.set_msg_size(int(size))
            #     continue
            # else:
            #     incoming_message = message_interpretation_actions.get(message["type"])(**message)
            #     wrapper.logger.debug("BaseWrapper: Action: " + str(incoming_message.type.value) )
            #     await message_function_actions.get(incoming_message.type.value)(message=incoming_message, wrapper=wrapper)

    else:  # use stdin as communication platform
        wrapper.logger.debug("MAIN::   reading from and writing to STDIN")
        wrapper.logger.debug("MAIN::   do_reading is: " + str(wrapper.do_reading))
        while True and wrapper.do_reading:
            # check whether the input has unexpected contents
            wrapper.logger.debug("MAIN::   reading from STDIN... ")
            try:
                line = stdin.readline()
            except ValueError:
                print( "IO Error occured")
                return
            #ignore empty lines (mainly for testing with test messages)
            if not line.strip():
                wrapper.logger.debug("MAIN::   empty line, continuing ... ")
                continue
            # JSON parsing
            wrapper.logger.debug("reading input (line): " + str(line) )
            message = loads(line)
            if message['type'] == "SYNC":
                sync_msg = SyncMessage(**message)
                wrapper.logger.debug("type of message:" + str(type(sync_msg)))
                wrapper.logger.debug("starting sync_function ... ")
                await sync_function(message=sync_msg,wrapper=wrapper)
                wrapper.logger.debug("sync_function awaited ")
            elif message['type'] == "VALUE":
                value_msg = ValueMessage(**message)
                wrapper.logger.debug("type of message:" + str(type(value_msg)))
                wrapper.logger.debug("starting value_function ... ")
                await value_function(message=value_msg,wrapper=wrapper)
                wrapper.logger.debug("value_function awaited ")
