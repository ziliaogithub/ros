#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import asyncore
import sys
import threading
import serial
from glob import glob
from settings import *


utility_names = {"SC": "Sensor Controller",
                 "BM": "Battery Management",
                 "RA": "Robotic Arm",
                 "M":  "Motor Controller",
                 "L": "LORA"}


class SerialNode(object):
    def __init__(self, server):
        self.ports = glob('/dev/ttyACM*') + glob('/dev/ttyUSB*')
        self.server = server
        self.serials = []
        self.utilities = {}
        self.msg = None
        self.msg_interval = WRITE_INTERVAL
        self.is_writing = False
        self.is_reading = False
        self.is_connected = False
        self.add_serials()
        self.add_utilities()

    def read_data(self):
        try:
            utility = self.utilities["SC"]
            self.is_reading = True
            print("reading...")
        except KeyError:
            self.is_reading = False

        while self.is_reading:
            try:
                #utility.timeout = 2
                data_array = utility.readline().split()

                try:
                    serial_data = " ".join(data_array) + "\n"
                    for handler in self.server.handlers:
                        handler.serial_data = serial_data
                except Exception:
                    pass
                
            except serial.SerialException:
                self.is_reading = False
                utility.close()
        print("reading thread ended")

    def write_data(self):
        mc, ra, sc = None, None, None

        if "M" in self.utilities:
            mc = self.utilities["M"]

        if "RA" in self.utilities:
            ra = self.utilities["RA"]

        if "SC" in self.utilities:
            sc = self.utilities["SC"]

        if mc or ra or sc:
            print("writing...")
            self.is_writing = True

        while self.is_writing:
            self.msg = None

            try:
                self.msg = self.server.handler.data
                print(self.msg)
                self.server.handler.data = None
            except AttributeError:
                self.msg = None
            except Exception as e:
                self.msg = None

            if self.msg:
                try:
                    self.msg = self.msg.split("\r\n")[0]
                    self.msg = self.msg.split("/")
                except:
                    continue                    
                try:
                    if mc:
                        mc.write(self.msg[0] + "\n")
                        print("written to mc", self.msg[0])

                    if ra:
                        ra.write(self.msg[1] + "\n")
                except serial.SerialException:
                    break

                if sc:
                    try:
                        if self.msg[2] in ('go', 'delete', 'stop') or \
                                (self.msg[2] != "0,0" and type(self.msg[2][-1]) == int):
                            sc.write(self.msg[2] + '\n')
                            print("written to sc", self.msg[2])
                    except Exception:
                        pass

            time.sleep(1)

        print("writing thread ended")

    def add_serials(self):
        for port in self.ports:
            try:
                self.serials.append(serial.Serial(port, 115200))
            except Exception as e:
                print(e)

        if not self.serials:
            print("no serials")
        
    def add_utilities(self):
        serial_no = 0
        num_serials = len(self.serials)

        while serial_no != num_serials:
            utility = self.serials[serial_no]
            #utility.timeout = 2
            utility.write("AFAF0000AF8003020000920D0A".decode("hex"))

            serial_data = utility.readline().split("\r\n")
            serial_data = serial_data[0].split(',')
            utility_name = str(serial_data[0])

            if utility_name in utility_names:
                print(utility_name + " Identified")

                self.utilities[utility_name] = utility
                
                utility.flushInput()
                utility.flushOutput()

                serial_no += 1

    def run_server(self):
        try:
            server_thread = threading.Thread(
                    target=asyncore.loop,
                    args=())
            server_thread.daemon = True
            server_thread.start()
        except Exception as e:
            print(e)
        
        self.is_connected = True

    def start_reading(self):
        try:
            reading_thread = threading.Thread(
                target=self.read_data,
                args=( ))
            reading_thread.daemon = True
            reading_thread.start()
        except Exception as e:
            print(e)

    def start_writing(self):
        try:
            writing_thread = threading.Thread(
                target=self.write_data,
                args=( ))
            writing_thread.daemon = True
            writing_thread.start()
        except Exception as e:
            print(e)

    def run(self):
        print("running")
        is_checking = True

        try:
            self.start_reading()
            self.start_writing()                
             
            if not self.is_connected:
                self.run_server()

            while is_checking:
                try:
                    print(self.server.handler.is_connected)
                except:
                    pass
                self.change_serial = False

                self.current_ports = glob('/dev/ttyACM*') + glob('/dev/ttyUSB*')

                if self.current_ports != self.ports:
                    self.ports = self.current_ports
                    self.change_serial = True

                if not self.change_serial:
                    for utility_name in self.utilities:
                        if not self.utilities[utility_name].isOpen():
                            self.change_serial = True
                            break

                if self.change_serial:
                    print("changing...")

                    self.change_serial = False
                    self.is_writing = False
                    self.is_reading = False
                    self.serials = []
                    self.utilities = {}
                    self.add_serials()
                    self.add_utilities()
                    self.run()
                time.sleep(2)
        except serial.SerialException:
            pass
        except Exception as e:
            print(e)
            print("Exiting...")
            sys.exit()
