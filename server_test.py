#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Created by Anoniji
Library made available under the terms of the license
Creative Commons Zero v1.0 Universal
https://creativecommons.org/publicdomain/zero/1.0/
"""

import base64
import zlib
from cryptography.fernet import Fernet

import socket
from logger import Logger


logger = Logger()
TCP_IP = '127.0.0.1'
TCP_PORT = 5005
BUFFER_SIZE = 1024  # Normally 1024, but we want fast response
CLIENTS = {}

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((TCP_IP, TCP_PORT))
s.listen(1)
logger.prt('success', 'Server start: OK')

while True:

    logger.prt('info', 'Waiting connexion...')
    conn, addr = s.accept()
    logger.prt('success', 'Connection address: ' + str(addr))

    while True:
        try:
            data = conn.recv(BUFFER_SIZE)
        except Exception:
            for client, data in CLIENTS.copy().items():
                if data['addr'] == addr:
                    logger.prt('info', 'remove client: ' + str(addr), 2)
                    del CLIENTS[client]

            break

        if data:
            zdata = zlib.decompress(data).decode()
            logger.prt('info', 'received data: ' + str(zdata))

            if 'connect:' in zdata:
                logger.prt('info', 'received data: ' + str(zdata), 2)
                machine_id = zdata[8:]
                if machine_id not in CLIENTS:
                    try:
                        base64.urlsafe_b64decode(machine_id)
                        CLIENTS[machine_id] = {
                            'key': Fernet(machine_id.encode()),
                            'addr': addr
                        }
                        conn.send(CLIENTS[machine_id]['key'].encrypt(b'client_valid'))
                        logger.prt('success', 'machine valided')

                    except Exception:
                        conn.send(CLIENTS[machine_id]['key'].encrypt(b'client_invalid'))
                        logger.prt('success', 'machine reject (invalid)')

                else:
                    conn.send(CLIENTS[machine_id]['key'].encrypt(b'client_exist'))
                    logger.prt('error', 'machine reject (exist)')

            else:
                conn.send(data)  # echo

        else:
            conn.send(b'empty_data')  # echo

conn.close()