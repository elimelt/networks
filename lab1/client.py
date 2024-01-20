import socket
from request import Request, Header
from util import validate_response
from struct import pack, unpack
from math import ceil
import time
import errno
import sys

HOST = "attu3.cs.washington.edu"

def stage_a() -> tuple[int, int, int, int]:
    req = Request()
    header = Header(12,0,1)
    req.add_header(header)
    req.add_payload(b"hello world")

    sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    udp_port = 12235

    msg = req.to_network_bytes()

    # print("header", list(msg)[:12])
    # print("content", list(msg)[12:])
    # print(len(msg))
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

    packet_id = 0

    while packet_id < num:
        req = Request()
        payload = b'\x00' * length
        req.add_header(header)
        payload = create_payload_bytes(packet_id, payload, length)
        req.add_payload(payload)
        msg = req.to_network_bytes()

        acked = False
        response = None
        while not acked:
            try:
                sock.sendto(msg, (HOST,udp_port))
                response = sock.recv(28)
                validate_response(response[:12], silent=True)
                acked = True
            except socket.timeout:
                print(f"timeout on packet {packet_id}")
                continue

        print(f"sent packet {packet_id}")
        packet_id += 1


    response = sock.recv(20)
    validate_response(response[:12])
    TCP_port, secretB = unpack('!II', response[12:])

    return TCP_port, secretB

def stage_c(TCP_port: int, secretB: int) -> tuple[int, int, int, str]:


    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, TCP_port))
    response = sock.recv(25)
    validate_response(response[:12])

    num2, len2, secretC, c, c1, c2, c3 = unpack('!IIIcccc', response[12:])
    print('c', c)
    print('c1', c1)
    print('c2', c2)
    print('c3', c3)


    # sock.close()

    return num2, len2, secretC, c, sock

# def stage_d(num2: int, len2: int, secretC: int, c: str) -> int:
#     sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     sock.connect((HOST, TCP_port))
#     response = sock.recv(25)
#     header = Header(len2, secretC, 1)

#     # send num2 packets of len2 filled with char c
#     validate_response(response[:12])

#     secretD = unpack('!I', response[12:])
#     sock.close()

#     return secretD

def stage_d(num2, len2, secretC, c, sock):
    req = Request()

    header = Header(len2, secretC, 1)
    req.add_header(header)

    len_byte_aligned = ceil(len2 / 4) * 4

    #payload should be len2 bytes of c
    payload = bytes(c, 'utf-8') * len_byte_aligned
    print(payload)
    print(len(payload))

    req.add_payload(payload)

    # sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # sock.connect((HOST, port))

    for i in range(num2):
        sock.send(req.to_network_bytes())
        print(f"sent packet {i}")

    response = sock.recv(28)
    print('resp', response)

    resp_header = response[:12]
    resp_payload = response[12:]

    print('resp header len', len(resp_header))
    print('resp payload len', len(resp_payload))

    # validate_response(resp_header)

    secretD = unpack('!I', resp_payload)

    return secretD

if __name__ == '__main__':
    numB, lenB, udp_port_a, secretA = stage_a()

    print(f"numB: {numB}, lenB: {lenB}, udp_port_a: {udp_port_a}, secretA: {secretA}")
    print("finished stage a")

    TCP_port, secretB = stage_b(numB, lenB, udp_port_a, secretA)
    print(f"TCP_port: {TCP_port}, secretB: {secretB}")
    print("finished stage b")

    num2, len2, secretC, c, sock = stage_c(TCP_port, secretB)
    print(f"num2: {num2}, len2: {len2}, secretC: {secretC}, c: {c}")
    print("finished stage c")
    print('recieved', c)

    secretD = stage_d(num2, len2, secretC, c, sock)
    print(secretD)
    print("finished stage d")
