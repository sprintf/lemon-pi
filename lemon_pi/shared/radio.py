#!/usr/bin/env python3

import time
import os
import random
import serial
from zlib import adler32
import logging
from queue import Queue
from threading import Thread
from serial.threaded import LineReader, ReaderThread
from serial.serialutil import PARITY_NONE, STOPBITS_ONE, EIGHTBITS
from python_settings import settings

from lemon_pi.shared.message_encoder import MessageEncoder
from lemon_pi.shared.message_decoder import (
    MessageDecoder,
    NoiseException,
    LPiNoiseException
)

from lemon_pi.shared.generated.messages_pb2 import ToCarMessage, ToPitMessage

from google.protobuf.message import Message

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
from lemon_pi.shared.usb_detector import UsbDetector, UsbDevice

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

    # frequencies we can use
    FREQ = [9233, 9239, 9245, 9251, 9257, 9263, 9269, 9275]

    def __init__(self, sender:str, key:str, base_message, ping_freq=45, **kwargs):
        Thread.__init__(self, daemon=True)
        self.encoder = MessageEncoder(sender, key)
        self.decoder = MessageDecoder(key)
        self.base_message = base_message
        self.frequency = self.__pick_radio_freq__(key)
        self.transmitting = False
        self.protocol = None
        self.metrics = RadioMetrics()
        self.last_transmit = 0
        self.ping_freq = ping_freq
        self.send_queue = Queue()
        self.send_thread = Thread(target=self.__send_outbound_messages__, daemon=True)
        self.receive_queue = Queue()

    def __pick_radio_freq__(self, key:str) -> int:
        index = adler32(key.encode("UTF8")) % len(Radio.FREQ)
        return Radio.FREQ[index] * 100000

    def run(self):
        try:
            self.receive_loop()
        except:
            logger.error("radio not connected")
            time.sleep(10)

    def choose_port(self) -> str:
        return UsbDetector.get(UsbDevice.LORA)

    def __radio_ready__(self):
        logger.info("radio is ready!")
        logger.info("using frequency {}".format(self.frequency))
        if not self.send_thread.is_alive():
            self.send_thread.start()
            logger.info("send thread started")

    class PrintLines(LineReader):

        def __init__(self):
            LineReader.__init__(self)
            self.radio = None
            self.transmitting = False
            self.initialized = False
            self.disconnected = False

        def set_radio(self, radio):
            self.radio = radio
            if self.transport and not self.initialized:
                self.__configure__()

        def connection_made(self, transport):
            logger.info("connection made")
            self.transport = transport
            if self.radio and not self.initialized:
                self.__configure__()

        def __configure__(self):
            logger.info("configuring radio")
            self.send_cmd('sys get ver')
            # default frequency is 923300000
            # bandwidth (bw) can be 125 250 or 500
            # we are using 500 bandwidth, and then picking a frequency
            # based on the hash of the secret (which has to be shared between tx and rx)
            self.send_cmd('radio set bw 500')
            self.send_cmd('radio set freq {}'.format(self.radio.frequency))
            self.send_cmd('radio get freq')
            self.send_cmd('radio get sf')
            # wait for up to a minute on commands : this creates few errors on read
            self.send_cmd('radio set wdt 60000')
            self.send_cmd('mac pause')
            self.send_cmd('radio set pwr 12')
            self.send_cmd('sys set pindig GPIO10 0')
            # this responds with 'lora' when we get this we mark ourselves as initialized
            self.send_cmd('radio get mod')

        def handle_line(self, data):
            logger.debug("got data %s" % data)

            # special response from 'radio get mod' which is the last response to the
            # initialization sequence
            if data == "lora":
                self.initialized = True
                self.send_cmd('radio rx 0')
                self.radio.__radio_ready__()
                return

            # we see invalid_param messages when there is insufficient delay between
            # commands we send to the radio
            if data == "ok" or data == 'busy' or data == 'invalid_param':
                return

            if data == "radio_err":
                self.radio.metrics.errors += 1
                self.transmitting = False
                self.send_cmd('radio rx 0')
                return

            if data == "radio_tx_ok":
                self.radio.metrics.sent += 1
                self.transmitting = False
                logger.debug("turning on radio receive after tx")
                self.send_cmd('radio rx 0')
                return

            # turn on the blue light ... we're getting data
            self.send_cmd("sys set pindig GPIO10 1")
            # 4c5069 is "LPi" our prefix
            if data.startswith("radio_rx  4C50"):
                try:
                    message:Message = self.radio.decoder.decode(bytearray.fromhex(data[10:]), self.radio.base_message)
                    logger.info("lag = {:.1f}s".format(time.time() - message.timestamp))
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
            self.send_cmd("sys set pindig GPIO10 0")

            if self.initialized and not self.transmitting:
                logger.debug("turning on rx after recieve")
                self.send_cmd('radio rx 0')

        def connection_lost(self, exc):
            if exc:
                logger.exception(exc)
            logger.info("port closed")
            self.disconnected = True

        def send_cmd(self, cmd, delay=0):
            if delay == 0:
                delay = settings.RADIO_CMD_COMPLETION_TIME
            logger.debug("sending cmd {}".format(cmd))
            self.transport.write(('%s\r\n' % cmd).encode('UTF-8'))
            time.sleep(delay)

    def receive_loop(self):

        serial_connection = None

        while True:

            if serial_connection:
                # if we have a serial connection then we're reinitializing it
                UsbDetector.init()

            if UsbDetector.detected(UsbDevice.LORA):
                serial_connection = serial.Serial(self.choose_port(), baudrate=57600,
                                         stopbits=STOPBITS_ONE, parity=PARITY_NONE, bytesize=EIGHTBITS)
            else:
                logger.info("No LORA device connected, waiting 30s")
                time.sleep(30)

            with ReaderThread(serial_connection, self.PrintLines) as protocol:

                self.protocol = protocol
                protocol.set_radio(self)

                last_status_log_time = time.time()
                while not protocol.disconnected:
                    sleep = random.randint(-10, 10)
                    time.sleep(self.ping_freq + sleep)
                    if time.time() - self.last_transmit > (self.ping_freq / 2):
                        if isinstance(self.base_message, ToCarMessage):
                            ping = ToPitMessage()
                        else:
                            ping = ToCarMessage()
                        ping.ping.timestamp = 1
                        self.send_message(protocol, ping)
                    if time.time() - last_status_log_time > 60:
                        logger.info("Status : {}".format(self.metrics.__repr__()))
                        self.metrics.reset()
                        last_status_log_time = time.time()
                logger.warning("disconnect detected")

    def send_async(self, msg:Message):
        self.send_queue.put(msg)

    def __send_outbound_messages__(self):
        while True:
            msg = self.send_queue.get()
            self.send_message(self.protocol, msg)
            self.send_queue.task_done()
            logger.info("awaiting TX completion")
            while self.protocol.transmitting:
                time.sleep(0.1)
            logger.info("TX complete")

    def send_message(self, protocol, msg:Message):
        try:
            logger.debug("turning off receive")
            protocol.send_cmd("radio rxstop")
            protocol.transmitting = True
            protocol.send_cmd("sys set pindig GPIO11 1")
            payload = self.encoder.encode(msg).hex()
            logger.info("sending {}".format(type(msg)))
            protocol.send_cmd("radio tx %s" % payload)
            self.metrics.send_attempt += 1
            self.last_transmit = time.time()
            protocol.send_cmd("sys set pindig GPIO11 0")
            logger.debug("message sent")
        except Exception as e:
            logger.exception("something went wrong")


if __name__ == "__main__":

    if not "SETTINGS_MODULE" in os.environ:
        os.environ["SETTINGS_MODULE"] = "lemon_pi.config.local_settings_pit"

    logging.basicConfig(format='%(asctime)s %(name)s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.INFO)
    UsbDetector.init()
    radio = Radio("car-181", "abracadabra", ToCarMessage(), ping_freq=30)
    radio.receive_loop()




