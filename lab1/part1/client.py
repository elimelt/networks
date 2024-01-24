import socket
from request import Request, Header
from util import validate_header, log, test_and_record_if_server_running
from struct import pack, unpack
from math import ceil
from multiprocessing import Process
import time
import random
import sys


HOST = "attu4.cs.washington.edu"
TIMEOUT = 0.1
UDP_PORT_A = 12235
STEP = 1
HEADER_SIZE = 12

def stage_a() -> tuple[int, int, int, int]:
    req = Request(Header(12, 0, STEP), b"hello world")
    sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

    sock.sendto(req.to_network_bytes(), (HOST, UDP_PORT_A))
    log("sent packet - stage: A")
    response = sock.recv(HEADER_SIZE + 4 * 4)

    sock.close()

    if not validate_header(response[:HEADER_SIZE], silent=True):
        log("bad response...exiting - stage: A")
        exit(1)

    num, len_b, udp_port_a, secretA = unpack('!IIII', response[HEADER_SIZE:]) # payload
    return num, len_b, udp_port_a, secretA

def stage_b(num: int, length: int, udp_port: int, secretA: int) -> tuple[int, int]:
    header = Header(length + 4, secretA, STEP)

    sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    sock.settimeout(TIMEOUT)

    def create_payload_bytes(id, payload, payload_length):
        return pack(f"!I{payload_length}s", id, payload)

    packet_id = 0

    while packet_id < num:
        req = Request(header, create_payload_bytes(packet_id, b'\x00' * length, length))
        acked = False
        response = None
        while not acked:
            sock.sendto(req.to_network_bytes(), (HOST,udp_port))
            log(f"sent packet - stage: B, packet_id: {packet_id}")
            try:
                response = sock.recv(28)
                # if not validate_header(response[:HEADER_SIZE], silent=True):
                #     log(f"bad response header...try again- stage: B, packet_id: {packet_id}")
                    # continue
                if unpack('!I', response[HEADER_SIZE:])[0] == packet_id:
                    acked = True
            except socket.timeout:
                log(f"timeout on response - stage: B, packet_id: {packet_id}")
                continue

        log(f"packed acked - stage: B, packet_id: {packet_id}")
        packet_id += 1

    response = sock.recv(HEADER_SIZE + 4 * 2)
    sock.close()

    if not validate_header(response[:HEADER_SIZE], silent=True):
        log("bad response...exiting - stage: B")
        exit(1)

    TCP_port, secretB = unpack('!II', response[HEADER_SIZE:])

    return TCP_port, secretB

def stage_c(TCP_port: int, secretB: int) -> tuple[int, int, int, str]:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, TCP_port))

    # extra + 3 for padding
    response = sock.recv(HEADER_SIZE + 4 * 3 + 1 + 3)
    if not validate_header(response[:HEADER_SIZE], silent=True):
        log("bad response...exiting - stage: C")
        exit(1)

    # bug in course staff's server implementation ??? or just padding
    num2, len2, secretC, c, _c1, _c2, _c3 = unpack('!IIIcccc', response[HEADER_SIZE:])

    return num2, len2, secretC, c, sock



def stage_d(num2, len2, secretC, c, sock):
    req_payload = bytearray()
    req_payload.extend(c * len2)

    req = Request(Header(len2, secretC, STEP), req_payload)
    msg = req.to_network_bytes()

    for i in range(num2):
        sock.send(msg)
        log(f"sent tcp packet - stage: D, sequenceNumber: {i}")

    response = sock.recv(HEADER_SIZE + 4)
    sock.close()

    resp_header = response[:HEADER_SIZE]
    resp_payload = response[HEADER_SIZE:]

    if not validate_header(resp_header, silent=True):
        log("bad response...exiting - stage: D")
        exit(1)

    secretD, = unpack('!I', resp_payload)

    return secretD

def main():
    # if not test_and_record_if_server_running(HOST):
    #     log(f"server is down...exiting - host: {HOST}")
    #     exit(1)

    public_ip = socket.gethostbyname(socket.gethostname())
    log(f"starting client - client_ip: {public_ip}, host: {HOST}")

    numB, lenB, udp_port_a, secretA = stage_a()
    # log(f"numB: {numB}, lenB: {lenB}, udp_port_a: {udp_port_a}, secretA: {secretA}")
    log(f"finished stage a - secretA: {secretA}")

    TCP_port, secretB = stage_b(numB, lenB, udp_port_a, secretA)
    # log(f"TCP_port: {TCP_port}, secretB: {secretB}")
    log(f"finished stage b - secretB: {secretB}")

    num2, len2, secretC, c, sock = stage_c(TCP_port, secretB)
    # log(f"num2: {num2}, len2: {len2}, secretC: {secretC}, c: {c}")
    log(f"finished stage c - secretC: {secretC}")

    secretD = stage_d(num2, len2, secretC, c, sock)
    log(f"finished stage d - secretD: {secretD}")


if __name__ == "__main__":
    nproc = 1
    if len(sys.argv) == 2:
        if not sys.argv[1].isnumeric():
            print("Usage: python client.py <nproc (default 1)>")
            exit(1)
        else:
            nproc = int(sys.argv[1])

    processes = []
    for _ in range(nproc):
        p = Process(target=main)
        time.sleep(random.randint(1, 10)/10)
        processes.append(p)
        p.start()

    for p in processes:
        p.join()