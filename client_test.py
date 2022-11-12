#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Created by Anoniji
Library made available under the terms of the license
Creative Commons Zero v1.0 Universal
https://creativecommons.org/publicdomain/zero/1.0/
"""

import os
import sys
import time

import uuid
import base64
import zlib
from cryptography.fernet import Fernet

import socket
import struct
import pickle
from logger import Logger

logger = Logger()
TCP_IP = '127.0.0.1'
TCP_PORT = 5005
BUFFER_SIZE = 1024
MESSAGE = b"Hello, World!"
SOCKET = False
CLIENT_KEY = False


def machine_id():
    global CLIENT_KEY

    try:
        logger.prt('info', 'machine_id', 2)
        if os.path.isfile('./.uuid'):
            logger.prt('info', 'machine_id: exist', 2)
            with open('./.uuid') as fdata:
                uuid_key = fdata.readlines()[0].strip()
        else:
            logger.prt('info', 'machine_id: create', 2)
            print('0')
            uuid_key = base64.urlsafe_b64encode(
                (str(uuid.uuid4())[0:32]).encode()
            ).decode()
            with open('./.uuid', 'w') as fdata:
                fdata.write(uuid_key)

        logger.prt('info', 'uuid_key: ' + str(uuid_key), 3)
        CLIENT_KEY = Fernet(uuid_key)
        return uuid_key
    except Exception as e:
        print(e)
        sys.exit(0)


def connect():
    global SOCKET
    logger.prt('info', 'Connecting to Server...')
    try:
        SOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        SOCKET.connect((TCP_IP, TCP_PORT))

        # init
        compress_id = zlib.compress(b'connect:' + machine_id().encode())
        SOCKET.send(compress_id)
        data = SOCKET.recv(BUFFER_SIZE)
        check = CLIENT_KEY.decrypt(data).decode()
        if check == 'client_valid':
            logger.prt('success', 'Connected')
            return True

        elif check == 'client_invalid' or check == 'client_exist' :
            logger.prt('error', 'Eject by server (' + check + ')')
            sys.exit(0)

        SOCKET = False
        return False

    except Exception:
        SOCKET = False
        return False


buffer_stk = {}
count = 0
splited = False


logger.prt('info', 'Init Connexion')
if connect():
    while True:
        try:
            msg = input('msg> ')
            data_msg = b'timestamp:' + str(time.time()).encode() + b';data:' + msg.encode()
            SOCKET.send(zlib.compress(CLIENT_KEY.encrypt(data_msg)))
            logger.prt('warning', 'Sending "' + msg + '"...')

            print('wait size')
            data_size = struct.unpack('>I', SOCKET.recv(4))[0]
            RECV_PAYLOAD = b""
            reamining_payload_size = data_size

            print('wait buffer')
            while reamining_payload_size != 0:
                RECV_PAYLOAD += SOCKET.recv(reamining_payload_size)
                reamining_payload_size = data_size - len(RECV_PAYLOAD)
            data = pickle.loads(RECV_PAYLOAD)

            print('read>')
            print(str(data))
            zdata = CLIENT_KEY.decrypt(zlib.decompress(data)).decode()
            logger.prt('warning', 'Reveive: ' + zdata)

        except Exception as e:

            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(e)
            print(exc_type, fname, exc_tb.tb_lineno)

            while not SOCKET:
                logger.prt('info', 'Reconnection in 3 secs...')
                time.sleep(3)
                connect()

else:
    logger.prt('error', 'Not connect...')

if SOCKET:
    SOCKET.close()
