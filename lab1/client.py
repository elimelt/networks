import socket
from request import Request, Header
from struct import pack, unpack
from math import ceil
import time
def stage_a() -> tuple[int, int, int, int]:
    req = Request()
    header = Header(12,0,1)
    req.add_header(header)
    req.add_payload(b"hello world", 12)

    sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    udp_host = "attu2.cs.washington.edu"
    udp_port = 12235

    msg = req.to_network_bytes()
    sock.sendto(msg, (udp_host,udp_port))

    response = sock.recv(28)

    header = response[:12]
    payload = response[12:]
    a, b, c, d = unpack("!IIHH", header)
    print(a, b, c, d)

    num, len_b, udp_port_a, secretA = unpack('!IIII', payload)

    return (num, len_b, udp_port_a, secretA)

def stage_b(num: int, length: int, udp_port: int, secretA: int) -> tuple[int, int]:
    # byte aligned length by 4
    len_byte_aligned = int(ceil(length / 4) * 4)
    header = Header(len_byte_aligned + 4, secretA, 1)

    sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    # socket.settimeout(1)
    udp_host = "attu2.cs.washington.edu"

    def create_payload_bytes(id, payload, payload_length):
        return pack(f"!I{payload_length}s", id, payload)

    print(f'sending {num} requests to {udp_port}')

    for packet_id in range(num):
        req = Request()
        payload = b'\x00' * len_byte_aligned
        req.add_header(header)
        payload = create_payload_bytes(packet_id, payload, len_byte_aligned)
        req.add_payload(payload, len_byte_aligned + 4)
        msg = req.to_network_bytes()
        sock.sendto(msg, (udp_host, udp_port))
        ack_response = sock.recv(16)
        unpacked_ack_response = unpack('!I', ack_response[12:])

    #  TCP port number, secretB.
    response = sock.recv(20)
    TCP_port, secretB = unpack('!II', response[12:])

    return TCP_port, secretB


if __name__ == '__main__':
    numB, lenB, udp_port_a, secretA = stage_a()
    print(numB, lenB, udp_port_a, secretA)
    # print(f'found port {udp_port_a}')
    TCP_port, secretB = stage_b(numB, lenB, udp_port_a, secretA)
