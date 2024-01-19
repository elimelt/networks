import socket
from request import Request, Header
from util import validate_response
from struct import pack, unpack
from math import ceil
import time
import errno
import sys

def stage_a() -> tuple[int, int, int, int]:
    req = Request()
    header = Header(12,0,1)
    req.add_header(header)
    req.add_payload(b"hello world")

    sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    udp_host = "attu2.cs.washington.edu"
    udp_port = 12235

    msg = req.to_network_bytes()

    print("header", list(msg)[:12])
    print("content", list(msg)[12:])
    print(len(msg))
    sock.sendto(msg, (udp_host,udp_port))

    response = sock.recv(28)

    header = response[:12]
    payload = response[12:]
    validate_response(header)

    num, len_b, udp_port_a, secretA = unpack('!IIII', payload)

    return (num, len_b, udp_port_a, secretA)

def stage_b(num: int, length: int, udp_port: int, secretA: int) -> tuple[int, int]:
    header = Header(length + 4, secretA, 1)

    sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    sock.settimeout(1)
    udp_host = "attu2.cs.washington.edu"

    def create_payload_bytes(id, payload, payload_length):
        return pack(f"!I{payload_length}s", id, payload)

    print(f'sending {num} requests to {udp_port}')
    packet_id = 0
    while packet_id < num:
        req = Request()
        payload = b'\x00' * length
        req.add_header(header)
        payload = create_payload_bytes(packet_id, payload, length)
        req.add_payload(payload)
        msg = req.to_network_bytes()

        print("header", list(msg)[:12])
        print("content", list(msg)[12:])
        print(len(msg))

        acked = False
        response = None
        while not acked:
            try:
                sock.sendto(msg, (udp_host,udp_port))
                response = sock.recv(28)
                validate_response(response[:12])
                acked = True
            except socket.timeout:
                print("timeout")
                continue

        packet_id += 1

    #  TCP port number, secretB.
    response = sock.recv(20)
    validate_response(response[:12])
    TCP_port, secretB = unpack('!II', response[12:])
    print(TCP_port, secretB)
    return TCP_port, secretB


if __name__ == '__main__':
    numB, lenB, udp_port_a, secretA = stage_a()
    print("finished stage a")
    print()
    print(numB, lenB, udp_port_a, secretA)
    TCP_port, secretB = stage_b(numB, lenB, udp_port_a, secretA)
    print("finished stage b")
