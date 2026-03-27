"""
 Copyright (c) 2025-2026
 Karlsruhe Institute of Technology - Institute for Automation and Applied Informatics (IAI)
"""
""" Version: 2024-02-12
This module contains a Python Wrapper Template that enables the User to easily implement default code as simulators into PROOF.
The User can replace "Model logic" with his own code.
"""
import argparse
import json
from datetime import datetime
from sys import exit
from typing import Tuple, Dict, Any
import asyncio

from proofcore.base import cliargparser
from proofcore.base.basewrapper import BaseWrapper, main
from proofcore.models.BlockStatus import BlockStatus
from proofcore.models.NotifyMessage import NotifyMessage
from proofcore.models.ValueMessage import ValueMessage
from proofcore.util.proofLogging import Logger, HandlerType

options, arguments = cliargparser.parse_known_args()

if options.local_block_id is None:
    print("WARNING: local_block_id not set, setting it to 'current timestamp'")
    options.local_block_id = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

__log_file_name = "proof_WrapperTemplate_" + options.local_block_id + ".log"
# Local use of the custom PROOF logger. Each file can have its own logger.
logger = Logger('WrapperTemplateLogger', handlers = [HandlerType.FILE], logging_dir=options.loggingDir, log_file_name = __log_file_name, log_level=options.logLevel).get_logger()

class WrapperTemplate(BaseWrapper):
    def __init__(self, opt=options) -> None:
        # define and initialize the static inputs and attributes of the model
        # Values are set to zero since they are static inputs or inputs and therefore set by the Wrapper.
        # examples:
        #   self.T = 0.0  # temperature in K. -> Stepbased_Static
        #   self.myValue = 0.0  # my own value -> Output

        # The absolut path of the json file including power loss
        # self.testFileName = self.read_json_file_for_output_value_control(opt.testDataPath + "/myTestData.json")
        logger.debug("__init__() -> initializing WrapperTemplate")
        super(WrapperTemplate, self).__init__(bwoptions=opt)

    async def init(self) -> Tuple[ValueMessage, NotifyMessage]:
        # Model logic
        logger.debug("processing init()")
        try:
            logger.debug("processing init()-try: starting a init process")
        except Exception as e:
            logger.debug("processing init()-except: handling a exception")
            await super(WrapperTemplate, self).init(BlockStatus.ERROR_INIT, str(e))
        else:
            logger.debug("processing init()-else: executing the following code if no exception")
            await super(WrapperTemplate, self).init(BlockStatus.INITIALIZED)

    async def step(self) -> Tuple[ValueMessage, NotifyMessage]:
        # Model logic
        logger.debug("processing step()")
        try:
            logger.debug("processing step()-try: starting a step execution")
        except Exception as e:
            logger.debug("processing step()-except: handling a exception")
            await super(WrapperTemplate, self).step(BlockStatus.ERROR_STEP, str(e))
        else:
            logger.debug("processing step()-else: executing the following code if no exception")
            await super(WrapperTemplate, self).step(BlockStatus.EXECUTION_STEP_FINISHED)

    async def finalize(self) -> Tuple[ValueMessage, NotifyMessage]:
        # Model logic
        logger.debug("processing finalize()")
        try:
            logger.debug("processing finalize()-try: starting a finalize process")
        except Exception as e:
            logger.debug("processing finalize()-except: handling a exception")
            await super(WrapperTemplate, self).finalize(BlockStatus.ERROR_FINALIZE, str(e))
        else:
            logger.debug("processing finalize()-else: executing the following code if no exception")
            await super(WrapperTemplate, self).finalize(BlockStatus.FINALIZED)

    # overwrite the following functions when necessary:
    def get_data(self) -> Dict[Any, Any]:
        return {obj: getattr(self, obj) for obj in self.outputs}


if __name__ == '__main__':
    try:
        logger.debug("The main method of WrapperTemplate.py gets executed!")
        asyncio.run(main(wrapper=WrapperTemplate()))
    except KeyboardInterrupt:
        exit(0)
