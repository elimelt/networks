import socket
from request import Request, Header
from util import validate_header, log
from struct import pack, unpack
from math import ceil

HOST = "attu2.cs.washington.edu"
TIMEOUT = 0.5
UDP_PORT_A = 12235
STEP = 1
HEADER_SIZE = 12

def stage_a() -> tuple[int, int, int, int]:
    header = Header(12,0,STEP)
    req = Request(header, b"hello world")

    sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    sock.sendto(req.to_network_bytes(), (HOST, UDP_PORT_A))
    response = sock.recv(HEADER_SIZE + 4 * 4)
    sock.close()

    validate_header(response[:HEADER_SIZE]) # header
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
            try:
                sock.sendto(req.to_network_bytes(), (HOST,udp_port))
                response = sock.recv(28)
                validate_header(response[:HEADER_SIZE], silent=True)
                acked = True
            except socket.timeout:
                log(f"timeout on packet {packet_id}")
                continue

        log(f"sent packet {packet_id}")
        packet_id += 1

    response = sock.recv(HEADER_SIZE + 4 * 2)
    sock.close()

    validate_header(response[:HEADER_SIZE])
    TCP_port, secretB = unpack('!II', response[HEADER_SIZE:])

    return TCP_port, secretB

def stage_c(TCP_port: int, secretB: int) -> tuple[int, int, int, str]:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, TCP_port))

    # extra + 3 for padding
    response = sock.recv(HEADER_SIZE + 4 * 3 + 1 + 3)
    validate_header(response[:HEADER_SIZE])

    log('c raw:', response[24:])

    # bug in course staff's server implementation ??? or just padding
    num2, len2, secretC, c, _c1, _c2, _c3 = unpack('!IIIcccc', response[HEADER_SIZE:])

    return num2, len2, secretC, c, sock



def stage_d(num2, len2, secretC, c, sock):
    req_payload = bytearray()
    req_payload.extend(c * (ceil(len2 / 4) * 4))

    req = Request(Header(len2, secretC, STEP), req_payload)

    for i in range(num2):
        sock.send(req.to_network_bytes())
        log(f"sent packet {i}")

    response = sock.recv(28)
    sock.close()

    resp_header = response[:HEADER_SIZE]
    resp_payload = response[HEADER_SIZE:]

    validate_header(resp_header)

    secretD = unpack('!I', resp_payload)

    return secretD

if __name__ == '__main__':
    numB, lenB, udp_port_a, secretA = stage_a()
    # log(f"numB: {numB}, lenB: {lenB}, udp_port_a: {udp_port_a}, secretA: {secretA}")
    log(f"finished stage a - secretA: {secretA}")

    TCP_port, secretB = stage_b(numB, lenB, udp_port_a, secretA)
    # log(f"TCP_port: {TCP_port}, secretB: {secretB}")
    log("finished stage b - secretB:", secretB)

    num2, len2, secretC, c, sock = stage_c(TCP_port, secretB)
    # log(f"num2: {num2}, len2: {len2}, secretC: {secretC}, c: {c}")
    log("finished stage c - secretC:", secretC)

    secretD = stage_d(num2, len2, secretC, c, sock)
    log("finished stage d - secretD:", secretD)
