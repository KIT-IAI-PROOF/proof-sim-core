"""
 Copyright (c) 2025-2026
 Karlsruhe Institute of Technology - Institute for Automation and Applied Informatics (IAI)
"""
import logging
import sys
from datetime import datetime
from enum import Enum
import os

class HandlerType(Enum):
    STDOUT = 1
    FILE = 2
class Logger(object):
    def __init__(self, name, log_level = "INFO", handlers = [HandlerType.STDOUT], logging_dir ="/tmp", log_file_name ="proof.log"):
        #hostname = socket.gethostname()
        self.formatter = logging.Formatter('[%(asctime)s.%(msecs)03d]-[%(levelname)s]-[%(name)s] (%(filename)s:%(lineno)d)::%(message)s', '%Y-%m-%d %H:%M:%SZ')
#        log_format = '[%(asctime)s]-[%(levelname)s]-[%(name)s] (%(threadName)s:%(filename)s:%(lineno)d)::%(message)s'
#        log_format = '[%(asctime)s]-[%(levelname)s]-[%(name)s] (%(filename)s:%(lineno)d)::%(message)s'
        self.log_format = '[%(asctime)s.%(msecs)03d]-[%(levelname)s]-[%(name)s] (%(filename)s:%(lineno)d)::%(message)s'
        logging.basicConfig(format=self.log_format,
                            datefmt= '%Y-%m-%dT%H:%M:%SZ')

        self._logger = logging.getLogger(name)
        # Ensure that the logger is set up properly
        # Remark für level in basicConfig: 
        # "This function [basiConfig] does nothing if the root logger already has handlers configured for it."
        # Therefore we're setting the log level here.
        self._logger.setLevel(log_level)

        log_str = "loggers defined for:  [STDOUT] "
        for htypes in handlers:
            if htypes == HandlerType.STDOUT:
                # always STDOUT!
                #self.addConsoleHandler()
                #logStr = logStr + " [STDOUT] "
                pass
            elif htypes == HandlerType.FILE:
                if not os.path.exists(logging_dir):
                    os.makedirs(logging_dir)
                self.add_file_handler(logging_dir, log_file_name)
                log_str = log_str + " [FILE] "

        self._logger.info(log_str)

    def get_logger(self):
        return self._logger

    '''
    add a handler to the logger to write to STDOUT
    '''
    def add_console_handler(self):
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(self.formatter)
        self._logger.addHandler(handler)

    '''
    add a file handler to the logger.
        loggingDir: the directory where the loggingfile should reside
        filename: the logging file name
        filemode: 'w' ((new) create the file and write)
                  'a' ((create the file if not yet exist and) append to it) => Default
    '''
    def add_file_handler(self, logging_dir ="/tmp", log_file_name ="/proof.log", filemode ='w+'):
        # current_date = datetime.now()
        current_date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S_")
        log_file_name = logging_dir + '/' + current_date + log_file_name
        handler = logging.FileHandler(filename = log_file_name, mode = filemode)
        handler.setFormatter(self.formatter)
        self._logger.addHandler(handler)

if __name__ == "__main__":
    for level in ["INFO", logging.DEBUG, "ERROR"]:
        logger = Logger('MyLogger', log_level = level, handlers=[HandlerType.STDOUT, HandlerType.FILE]).get_logger()
        #logger = Logger('MyLogger').get_logger()
        effective_level = logger.getEffectiveLevel()
        print(f"== Logging test for level '{str(level)}': effective: {effective_level} ")
        print(f"Debug:    {logger.isEnabledFor(logging.DEBUG)}")
        print(f"Info:     {logger.isEnabledFor(logging.INFO)}")
        print(f"Warning:  {logger.isEnabledFor(logging.WARNING)}")
        print(f"Error:    {logger.isEnabledFor(logging.ERROR)}")
        print(f"Critical: {logger.isEnabledFor(logging.CRITICAL)}")
        logger.debug('This is a debug message')
        logger.info('This is an info message')
        logger.warning('This is a warning message')
        logger.error('This is an error message')
        logger.critical('This is a critical message')
        print("==")
