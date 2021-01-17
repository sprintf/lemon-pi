#!/usr/bin/env python3

import sys
import os
import glob
import time
import random
import serial
import logging
import subprocess
from queue import Queue
from threading import Thread
from serial.threaded import LineReader, ReaderThread

from shared.radio_message import *
from shared.message_encoder import MessageEncoder
from shared.message_decoder import (
    MessageDecoder,
    NoiseException,
    LPiNoiseException
)

from google.protobuf.message import Message
from shared.generated import ping_pb2

#
# Radio Logic
#
# It takes around 4s to transmit any message with Lora
# During that time the radio has to be disabled from receive mode, so this
# creates a large window for transmissions not being received for this reason:
#  1. tranmissions should be limited
#  2. the ping protocol only runs when nothing else is happening
#  3. mechanisms that transmit based on a coordinated event (such as the car crossing the line)
#     should be offset accordingly
#
# The Ping Protocol
#  When nothing else is being transmitted, each device sends out a ping every 45s +- 10s
#  The +- 10s is randomized so that it's unlikely two radios will ever stay in sync
#  The ping includes the identity of the sender, so it is possible to display all the
#  radios that are talking in a group

logger = logging.getLogger(__name__)


class RadioMetrics:

    def __init__(self):
        self.received = 0
        self.send_attempt = 0
        self.sent = 0
        self.errors = 0
        self.recognized_noise = 0
        self.noise = 0

    def reset(self):
        self.__init__()

    def __repr__(self):
        return "RX:{} TX:{} TX-ERR:{} ERR:{} NOISE-LPi:{} NOISE-OTHER:{}".format(
            self.received,
            self.sent,
            self.send_attempt - self.sent,
            self.errors,
            self.recognized_noise,
            self.noise
        )


class Radio(Thread):

    def __init__(self, sender:str, key:str, ping_freq=45, **kwargs):
        Thread.__init__(self, daemon=True)
        self.encoder = MessageEncoder(sender, key)
        self.decoder = MessageDecoder(key)
        self.transmitting = False
        self.protocol = None
        self.metrics = RadioMetrics()
        self.last_transmit = 0
        self.ping_freq = ping_freq
        if kwargs.get("port"):
            self.ser = serial.Serial(kwargs['port'], baudrate=57600)
        else:
            self.ser = serial.Serial(self.choose_port(), baudrate=57600)
        self.send_queue = Queue()
        self.send_thread = Thread(target=self.__send_outbound_messages__, daemon=True).start()
        self.receive_queue = Queue()

    def init(self):
        # generate the necessary protobufs
        # -I=$SRC_DIR --python_out=$DST_DIR $SRC_DIR/addressbook.proto
        logger.info("running in {}".format(os.getcwd()))
        if os.getcwd().endswith("shared"):
            os.chdir("../")
        if not os.path.isdir("shared/generated"):
            os.mkdir("shared/generated")
        # todo check genstamp / mod time of output dir
        logger.info("running in {}".format(os.getcwd()))
        logger.info("generating protobufs")
        result = subprocess.run(["protoc",
                                 "--python_out=shared/generated",
                                 "-I=shared/protos",
                                 "ping.proto"], stdout=subprocess.PIPE)
        print(result.stdout)
        print(result.returncode)
        print(result.stderr)
        logger.info("done")


    def run(self):
        try:
            self.receive_loop()
        except:
            logger.error("radio not connected")
            time.sleep(10)

    def choose_port(self) -> str:
        possible_ports = []
        if sys.platform.startswith('darwin'):
            possible_ports += [port for port in glob.glob('/dev/tty.usbserial*')]
        if len(possible_ports) == 0:
            raise Exception("no serial port found for Lora")
        elif len(possible_ports) == 1:
            logger.info("choosing {}".format(possible_ports))
            return possible_ports[0]
        else:
            choice = possible_ports[random.randint(0, len(possible_ports) - 1)]
            logger.warning("randomly/hopefully choosing {} for Lora device".format(choice))
            return choice

    class PrintLines(LineReader):

        def __init__(self):
            LineReader.__init__(self)
            self.radio = None
            self.transmitting = False

        def set_radio(self, radio):
            self.radio = radio

        def connection_made(self, transport):
            logger.info("connection made")
            self.transport = transport
            self.send_cmd('sys get ver')

            self.send_cmd('radio get mod')
            self.send_cmd('radio get freq')
            self.send_cmd('radio get sf')
            self.send_cmd('mac pause')
            self.send_cmd('radio set pwr 10')
            self.send_cmd('radio rx 0')
            self.send_cmd("sys set pindig GPIO10 0")

        def handle_line(self, data):
            logger.debug("got data %s" % data)

            if data == "ok" or data == 'busy':
                return
            if data == "radio_err":
                self.radio.metrics.errors += 1
                self.transmitting = False
                self.send_cmd('radio rx 0')
                return

            if data == "radio_tx_ok":
                self.radio.metrics.sent += 1
                self.transmitting = False
                self.send_cmd('radio rx 0')
                return

            # turn on the blue light ... we're getting data
            self.send_cmd("sys set pindig GPIO10 1", delay=0)
            # 4c5069 is "LPi" our prefix
            if data.startswith("radio_rx  4C50"):
                try:
                    message:RadioMessageBase = self.radio.decoder.decode(bytearray.fromhex(data[10:]))
                    logger.info("lag = {:.1f}s".format(time.time() - message.ts))
                    logger.info("received " + message.__repr__())
                    self.radio.metrics.received += 1
                    # put this message onto a queue to go to the
                    # rest of the system
                    self.radio.receive_queue.put(message)
                except LPiNoiseException:
                    logger.info("received RPi noise : {}".format(data))
                    self.radio.metrics.recognized_noise += 1
                except NoiseException:
                    logger.info("received noise")
                    self.radio.metrics.noise += 1
            # turn off the blue light
            self.send_cmd("sys set pindig GPIO10 0", delay=0)

            if not self.transmitting:
                logger.debug("turning on receive")
                self.send_cmd('radio rx 0')

        def connection_lost(self, exc):
            if exc:
                logger.exception(exc)
            logger.info("port closed")

        def send_cmd(self, cmd, delay=.5):
            self.transport.write(('%s\r\n' % cmd).encode('UTF-8'))
            time.sleep(delay)

    def receive_loop(self):
        with ReaderThread(self.ser, self.PrintLines) as protocol:

            self.protocol = protocol
            protocol.set_radio(self)

            last_status_log_time = time.time()
            while (1):
                sleep = random.randint(-10, 10)
                time.sleep(self.ping_freq + sleep)
                if time.time() - self.last_transmit > (self.ping_freq / 2):
                    self.send_message(protocol, ping_pb2.Ping())
                if time.time() - last_status_log_time > 60:
                    logger.info("Status : {}".format(self.metrics.__repr__()))
                    self.metrics.reset()
                    last_status_log_time = time.time()

    def send_async(self, msg:RadioMessageBase):
        self.send_queue.put(msg)

    def __send_outbound_messages__(self):
        msg = self.send_queue.get()
        self.send_message(self.protocol, msg)
        self.send_queue.task_done()

    def send_message(self, protocol, msg:Message):
        logger.debug("turning off receive")
        protocol.write_line("radio rxstop")
        protocol.transmitting = True
        protocol.write_line("sys set pindig GPIO11 1")
        payload = self.encoder.encode(msg).hex()
        logger.info("sending {}".format(payload))
        protocol.write_line("radio tx %s" % payload)
        self.metrics.send_attempt += 1
        self.last_transmit = time.time()
        protocol.write_line("sys set pindig GPIO11 0")
        logger.debug("message sent")


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s %(name)s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.INFO)
    radio = Radio("car-181", "", ping_freq=15)
    radio.init()
    radio.receive_loop()




