#!/usr/bin/env python3

import socket

def send(message: str, address: str = "127.0.0.1", port: int = 9999):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(bytes(message, "utf-8"), (address, port))

