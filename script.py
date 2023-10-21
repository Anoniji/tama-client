#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Created by Anoniji
Library made available under the terms of the license
Creative Commons Zero v1.0 Universal
https://creativecommons.org/publicdomain/zero/1.0/
"""

import os

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
import sys
import time

import uuid
import base64
import zlib
from cryptography.fernet import Fernet

import socket
import struct
from io import BytesIO
from logger import Logger

import pygame


class Client:
    def __init__(self):
        self.version = "20231021.1"

        self.logger = Logger()
        self.logger.log_nms = "Client"

        self.TCP_IP = "192.168.1.92"
        self.TCP_PORT = 5005
        self.BUFFER_SIZE = 1024
        self.SOCKET = False
        self.Tclient_KEY = False

        pygame.mixer.init(11025)  # 44100

    def machine_id(self):
        try:
            self.logger.prt("info", "machine_id", 2)
            if os.path.isfile("./.uuid"):
                self.logger.prt("info", "machine_id: exist", 2)
                with open("./.uuid") as fdata:
                    uuid_key = fdata.readlines()[0].strip()
            else:
                self.logger.prt("info", "machine_id: create", 2)
                print("0")
                uuid_key = base64.urlsafe_b64encode(
                    (str(uuid.uuid4())[0:32]).encode()
                ).decode()
                with open("./.uuid", "w") as fdata:
                    fdata.write(uuid_key)

            self.logger.prt("info", "uuid_key: " + str(uuid_key), 3)
            self.Tclient_KEY = Fernet(uuid_key)
            return uuid_key
        except Exception as e:
            print(e)
            sys.exit(0)

    def connect(self):
        self.logger.prt("info", "Connecting to Server...")
        try:
            self.SOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.SOCKET.connect((self.TCP_IP, self.TCP_PORT))

            # init
            machine_id = self.machine_id()
            if not machine_id:
                return False

            compress_id = zlib.compress(b"connect:" + machine_id.encode())
            self.SOCKET.send(compress_id)
            data = self.SOCKET.recv(self.BUFFER_SIZE)
            check = self.Tclient_KEY.decrypt(data).decode()

            if check == "client_valid":
                self.logger.prt("success", "Connected")
                return True

            elif check == "client_invalid" or check == "client_exist":
                self.logger.prt("error", "Eject by server (" + check + ")")
                sys.exit(0)

            self.SOCKET = False
            return False

        except Exception:
            self.SOCKET = False
            return False


if __name__ == "__main__":
    Tclient = Client()
    Tclient.logger.prt("info", "Init Connexion")
    if Tclient.connect():
        while True:
            try:
                # data:{R/A/N}{V/T}:{lang}:{text}
                msg = input("msg> ")
                data_msg = (
                    b"timestamp:" + str(time.time()).encode() + b";data:" + msg.encode()
                )
                Tclient.SOCKET.send(
                    zlib.compress(Tclient.Tclient_KEY.encrypt(data_msg))
                )
                Tclient.logger.prt("warning", 'Sending "' + msg + '"...')

                print("wait size")
                data_size = struct.unpack(">Q", Tclient.SOCKET.recv(8))[0]
                RECV_PAYLOAD = b""
                reamining_payload_size = data_size

                print("wait buffer", reamining_payload_size)
                while reamining_payload_size > 0:
                    RECV_PAYLOAD += Tclient.SOCKET.recv(reamining_payload_size)
                    reamining_payload_size = data_size - len(RECV_PAYLOAD)
                data = RECV_PAYLOAD

                print("read>")
                zdata = Tclient.Tclient_KEY.decrypt(zlib.decompress(data)).decode()

                if "voice:" in zdata:
                    Tclient.logger.prt("warning", "Reveive voice")
                    voice = zdata.split("voice:")[-1]
                    vdata = (
                        voice.encode()
                        .decode("unicode_escape")
                        .encode("raw_unicode_escape")
                    )

                    voice_data = BytesIO(vdata)
                    voice_data.name = "data.mp3"
                    voice_data.seek(0)

                    pygame.mixer.music.load(voice_data)
                    pygame.mixer.music.play()
                if "text:" in zdata:
                    Tclient.logger.prt("warning", "Receive text")
                    text = zdata.split("text:")[-1]
                    Tclient.logger.prt("info", "Text: " + text)
                else:
                    Tclient.logger.prt("warning", "Reveive: " + zdata)

            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(e)
                print(exc_type, fname, exc_tb.tb_lineno)

                while not Tclient.SOCKET:
                    Tclient.logger.prt("info", "Reconnection in 3 secs...")
                    time.sleep(3)
                    Tclient.connect()

    else:
        Tclient.logger.prt("error", "Eject by server")

    if Tclient.SOCKET:
        Tclient.SOCKET.close()
