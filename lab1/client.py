import socket
from request import Request, Header
from struct import pack, unpack
from math import ceil
import time
from collections import deque
from util import print_bytes_n
HOST = 'attu3.cs.washington.edu'

sid = 256

def stage_a() -> tuple[int, int, int, int]:
    p_secret = 0
    step = 1

    msg = ('hello world' + '\0').encode('utf-8')
    header = create_header_bytes(len(msg), p_secret, step)
    req = header + msg

    sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    udp_port = 12235

    sock.sendto(req, (HOST,udp_port))
    print('sent request')
    response = sock.recv(28)
    print('got response')

    payload_len, psecret, step, sid, num, length, udp_port_a, secretA = unpack('!IIHHIIII', response)

    return (num, payload_len, udp_port_a, secretA)

    # sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    # udp_host = "attu2.cs.washington.edu"
    # udp_port = 12235

    # msg = req.to_network_bytes()
    # sock.sendto(msg, (udp_host,udp_port))

    # response = sock.recv(28)

    # header = response[:12]
    # payload = response[12:]
    # a, b, c, d = unpack("!IIHH", header)
    # print(a, b, c, d)

    # num, len_b, udp_port_a, secretA = unpack('!IIII', payload)

    # return (num, len_b, udp_port_a, secretA)

# returns a 4-byte aligned payload
def create_payload_bytes(id, payload_length):
    byte_aligned_length = int(ceil(payload_length / 4) * 4)
    zeros = b'\x00' * byte_aligned_length
    payload = pack(f"!I", id) + zeros
    return payload

def create_header_bytes(msg_length, secretA, step):
    return pack('!IIHH', msg_length, secretA, step, sid)


def stage_b(num: int, length: int, udp_port: int, secretA: int) -> tuple[int, int]:
    # byte aligned length by 4
    len_byte_aligned = int(ceil(length / 4) * 4)

    packet_queue = deque(range(num))
    sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    sock.settimeout(1)

    while packet_queue:
        packet_id = packet_queue.popleft()
        header = create_header_bytes(len_byte_aligned + 4, secretA, 1)
        # print('header: ', len_byte_aligned + 4, secretA, 1, 256)
        # print_bytes_n(header, 4)
        # payload = packet_id.to_bytes(4, 'big') + b'\x00' * len_byte_aligned
        payload = create_payload_bytes(packet_id, len_byte_aligned)
        # print('payload: ', packet_id, len_byte_aligned, 'zeros')
        # print_bytes_n(payload, 4)
        msg = header + payload

        try:
            sock.sendto(msg, (HOST, udp_port))
            ack_response = sock.recv(4)
            unpacked_ack_response = unpack('!I', ack_response[12:])
            print(unpacked_ack_response)
        except socket.timeout:
            print('timeout')
            packet_queue.appendleft(packet_id)





    # byte aligned length by 4
    # len_byte_aligned = int(ceil(length / 4) * 4)
    # header = Header(len_byte_aligned + 4, secretA, 1)

    # sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    # # socket.settimeout(1)
    # udp_host = "attu2.cs.washington.edu"

    # def create_payload_bytes(id, payload, payload_length):
    #     return pack(f"!I{payload_length}s", id, payload)

    # print(f'sending {num} requests to {udp_port}')

    # for packet_id in range(num):
    #     req = Request()
    #     payload = b'\x00' * len_byte_aligned
    #     req.add_header(header)
    #     payload = create_payload_bytes(packet_id, payload, len_byte_aligned)
    #     req.add_payload(payload, len_byte_aligned + 4)
    #     msg = req.to_network_bytes()
    #     sock.sendto(msg, (udp_host, udp_port))
    #     ack_response = sock.recv(16)
    #     unpacked_ack_response = unpack('!I', ack_response[12:])

    # #  TCP port number, secretB.
    # response = sock.recv(20)
    # TCP_port, secretB = unpack('!II', response[12:])

    # return TCP_port, secretB


if __name__ == '__main__':
    numB, lenB, udp_port_a, secretA = stage_a()
    print(numB, lenB, udp_port_a, secretA)
    # print(f'found port {udp_port_a}')
    TCP_port, secretB = stage_b(numB, lenB, udp_port_a, secretA)





    # test_payload = create_payload_bytes(0, 8)
    # assert len(test_payload) == 12
    # id, payload = unpack('!I8s', test_payload)
    # assert id == 0
    # assert payload == b'\x00\x00\x00\x00\x00\x00\x00\x00'

    # # test padding from 1
    # test_payload = create_payload_bytes(0, 9)
    # assert len(test_payload) == 16
    # id, payload = unpack('!I12s', test_payload)
    # assert id == 0
    # assert payload == b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'

    # # test padding from 2
    # test_payload = create_payload_bytes(0, 10)
    # assert len(test_payload) == 16
    # id, payload = unpack('!I12s', test_payload)
    # assert id == 0
    # assert payload == b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'

    # # test padding from 3
    # test_payload = create_payload_bytes(0, 11)
    # assert len(test_payload) == 16
    # id, payload = unpack('!I12s', test_payload)
    # assert id == 0


