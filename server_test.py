#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Created by Anoniji
Library made available under the terms of the license
Creative Commons Zero v1.0 Universal
https://creativecommons.org/publicdomain/zero/1.0/
"""

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

conn, addr = s.accept()
logger.prt('success', 'Connection address: ' + str(addr))

while True:
    try:
        data = conn.recv(BUFFER_SIZE)
    except Exception:
        break

    if data:
        data = zlib.decompress(data).decode()
        print('received data:', data)
        logger.prt('info', 'received data: ' + str(data))

        if 'connect:' in data:
            logger.prt('info', 'received data: ' + str(data), 2)
            machine_id = data[8:]
            if machine_id not in CLIENTS:
                CLIENTS[machine_id] = {
                    'key': Fernet(machine_id.encode())
                }
                conn.send(CLIENTS[machine_id]['key'].encrypt(b'client_valid'))
                logger.prt('success', 'machine valided')
            else:
                conn.send(CLIENTS[machine_id]['key'].encrypt(b'client_exist'))
                logger.prt('error', 'machine reject (exist)')



    conn.send(b'ping')  # echo

conn.close()