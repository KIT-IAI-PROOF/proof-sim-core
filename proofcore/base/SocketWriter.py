"""
 Copyright (c) 2025-2026
 Karlsruhe Institute of Technology - Institute for Automation and Applied Informatics (IAI)
"""
import socket
import logging

from proofcore.util.proofLogging import Logger, HandlerType


# WRITER is CLI
# No response expected:  commented with #NR

class SocketWriter:

    def __init__(self, port: int, local_block_id: int, loggingDir: str, logLevel: str) -> None:
        self.client = None
        self.port = port
        _log_file_name = "proof_SocketWriter_"+str(local_block_id)+"_"+str(self.port) + ".log"
        self.logger = Logger('SocketWriterLogger', logging_dir=loggingDir, log_file_name=_log_file_name, log_level=logLevel, handlers=[HandlerType.FILE]).get_logger()

        self.logger.debug("client _init_   Port: " + str(self.port))

    def start(self) -> None:
        # create a socket object
        self.logger.debug("start:: establishing connection with port " + str(self.port))
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_ip = "127.0.0.1"
        #port = 54321
        try:
            self.client.connect((server_ip, self.port))
        except Exception as e:
            self.logger.debug("-except: handling an exception" + str(e))

        self.logger.debug("start:: client connected with port " + str(self.port))

    def send(self, data: str) -> None:
        #self.logger.debug("sending data: ", data)
        try:
            #self.client.send(msg.encode("utf-8")[:1024])
            self.logger.debug("send:: sending data:: " + data) # str(data.encode("utf-8")[:1024]))
            self.client.send(data.encode("utf-8")[:1024])
            self.logger.debug("send:: data sent ...")
            #NRself.logger.debug("send:: data sent, waiting for response ...")
            #NRresponse = self.client.recv(1024)
            #response = response.decode("utf-8")   => Worker response is not encoded
            #NRself.logger.debug("send:: response " + str(response))

            #NRif response == "close\n":
                #NRself.logger.debug("close received")
                #NRself.client.close()
        except TypeError as e:
            raise TypeError(f"Error sending data with socket client") from e
            self.logger.debug("ERROR raised: " + str(e) )

    def stop(self) -> None:
        # close connection socket with the client

        self.logger.debug("closing client connection ")
        self.client.close()
        # close server socket
        self.logger.debug("client closed ")

