"""
 Copyright (c) 2025-2026
 Karlsruhe Institute of Technology - Institute for Automation and Applied Informatics (IAI)
"""
import socket
import logging
import struct

from proofcore.util.proofLogging import Logger, HandlerType

#   READER is SERVER
# No response expected:  commented with #NR

class SocketReader:

    def __init__(self, port: int, local_block_id: int, loggingDir: str, logLevel: str) -> None:
        self.msg_size = 1024
        self.server = None
        self.connection = None
        self.port = port
        _log_file_name = "proof_SocketReader_"+str(local_block_id)+"_"+str(self.port) + ".log"
        self.logger = Logger('SocketReaderLogger', logging_dir=loggingDir, log_file_name=_log_file_name,
                             log_level=logLevel, handlers=[HandlerType.FILE]).get_logger()
        self.logger.debug("server _init_   Port: " + str(port))

    def start(self) -> None:
        # create a socket object
        self.logger.debug("start:: establishing connection")
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_ip = "127.0.0.1"
            self.server.bind((server_ip, self.port))
            self.logger.debug("server (reader) started, now listening ...")
            self.server.listen(0)
            self.connection, client_address = self.server.accept()
            self.logger.debug("start:: Accepted connection")
        except Exception as e:
            self.logger.debug("\n\nERROR: handling an exception: " + str(e))


    def listen(self) -> str:
        # receive data from the client
        self.logger.debug("LISTENING... to port " + str(self.port))

        try:
            while True:
                self.logger.debug("reading with msg_size: " + str(self.msg_size))
                request = self.connection.recv(self.msg_size).decode("utf-8")
                self.logger.debug("received data: \n" + str(request))
                #request = self.recvall(2048)
                #request = self.recv_msg()
                #request = request.decode("utf-8") # convert bytes to string
                #print("request: ", request)
                # if we receive "close" from the client, then we break
                # out of the loop and close the conneciton
                if request.lower() == "close\n":
                    self.logger.debug("CLOSING")
                    # send response to the client which acknowledges that the
                    # connection should be closed and break out of the loop
                    #NRself.client.send("closed".encode("utf-8"))
                    self.stop()
                    break

                #NRresponse = "ok\n".encode("utf-8") # convert string to bytes

                # convert and send accept response to the client
                #NRself.client.send(response)
                self.logger.debug("respond (ok) sent")
                if self.msg_size > 1024:
                    self.msg_size = 1024
                return request
        except Exception as e:
            self.logger.debug("\n\nERROR: handling an exception: " + str(e) + "\n")
            self.stop()
            return None

    def set_msg_size(self, size=1024):
        self.msg_size = size

    def stop(self) -> None:
        # close connection socket with the client
        # self.client.close()
        self.logger.debug("closing server connection ")
        # close server socket
        self.server.close()
        self.logger.debug("server closed ")


