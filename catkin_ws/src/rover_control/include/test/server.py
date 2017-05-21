#!/usr/bin/env python
# -*- coding: utf-8 -*-

import asyncore
import logging
import socket
import time
from settings import *


class EchoHandler(asyncore.dispatcher_with_send):
    is_connected = True
    data = None
    serial_data = None

    def writable(self):
        return True

    def handle_write(self):
        if self.serial_data:
            print("sending", self.serial_data)
            self.send(self.serial_data)
            self.serial_data = None


    def handle_read(self):
        self.data = self.recv(50)

    def handle_close(self):
        self.is_connected = False
        self.close()


class EchoServer(asyncore.dispatcher):
    def __init__(self, host, port):
        asyncore.dispatcher.__init__(self)
        self.handlers = []
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((host, port))
        self.listen(5)
        #print("listening")

    def handle_accept(self):
        for handler in self.handlers:
            if not handler.is_connected:
                print("deleted")
                self.handlers.remove(handler)

        pair = self.accept()
        if pair is not None:
            sock, addr = pair
            print('Incoming connection from %s' % repr(addr))
            self.handler = EchoHandler(sock)
            self.handlers.append(self.handler)
            print(self.handlers)


if __name__ == "__main__":
    server = EchoServer(HOST, PORT)
    asyncore.loop()
