"""
 Copyright (c) 2025-2026
 Karlsruhe Institute of Technology - Institute for Automation and Applied Informatics (IAI)
"""
import logging as log
import os.path


"""
The logger can be used by each app and all logs will be saved in the file "dev.log"
"""
class Logger(object):
    def __init__(self, name):
        filename = "/tmp/proof/logs.txt"
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        log_format = '[%(asctime)s]-[%(levelname)s]-[%(name)s] (%(filename)s:%(lineno)d)::%(message)s'
        log.basicConfig(level=log.INFO,
                            format=log_format,
                            filename=os.path.join(filename),
                            filemode='w',
                            datefmt= '%Y-%m-%dT%H:%M:%SZ')
        fh = log.FileHandler(filename)
        fh.setLevel(log.DEBUG)
        fh.setFormatter(log.Formatter(log_format))
        log.getLogger(name).addHandler(fh)
        self._logger = log.getLogger(name)

    def get_logger(self):
        return self._logger