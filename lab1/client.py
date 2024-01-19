import socket
from request import Request, Header
from util import validate_response
from struct import pack, unpack
from math import ceil
import time
import errno
import sys
import tqdm

HOST = "attu2.cs.washington.edu"

def stage_a() -> tuple[int, int, int, int]:
    req = Request()
    header = Header(12,0,1)
    req.add_header(header)
    req.add_payload(b"hello world")

    sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    udp_port = 12235

    msg = req.to_network_bytes()

    print("header", list(msg)[:12])
    print("content", list(msg)[12:])
    print(len(msg))
    sock.sendto(msg, (HOST,udp_port))

    response = sock.recv(28)

    header = response[:12]
    payload = response[12:]
    validate_response(header)

    num, len_b, udp_port_a, secretA = unpack('!IIII', payload)

    return (num, len_b, udp_port_a, secretA)

def stage_b(num: int, length: int, udp_port: int, secretA: int) -> tuple[int, int]:
    header = Header(length + 4, secretA, 1)

    sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    sock.settimeout(.5)

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

        # print("header", list(msg)[:12])
        # print("content", list(msg)[12:])
        # print(len(msg))

        acked = False
        response = None
        while not acked:
            print(f'sending packet {packet_id}')
            try:
                sock.sendto(msg, (HOST,udp_port))
                response = sock.recv(28)
                validate_response(response[:12])
                acked = True
                print(f'packet {packet_id} acked')
            except socket.timeout:
                print("timeout")
                continue

        packet_id += 1

    #  TCP port number, secretB.
    response = sock.recv(20)
    validate_response(response[:12])
    TCP_port, secretB = unpack('!II', response[12:])

    return TCP_port, secretB

def stage_c(TCP_port: int, secretB: int):


    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, TCP_port))
    response = sock.recv(25)
    validate_response(response[:12])

    num2, len2, secretC, c = unpack('!IIIc', response[12:])

    sock.close()

    return num2, len2, secretC, c

def stage_d(num2: int, len2: int, )

if __name__ == '__main__':
    numB, lenB, udp_port_a, secretA = stage_a()
    print(numB, lenB, udp_port_a, secretA)
    print("finished stage a")

    TCP_port, secretB = stage_b(numB, lenB, udp_port_a, secretA)
    print(TCP_port, secretB)
    print("finished stage b")

    num2, len2, secretC, c = stage_c(TCP_port, secretB)
    print(num2, len2, secretC, c)
    print("finished stage c")
