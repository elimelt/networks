import socket
import _thread
from random import randint
from struct import pack, unpack
from math import ceil
from typing import Optional

from util import log
from response import Response, Header

HOST = "attu4.cs.washington.edu"
UDP_INITIATE_HANDSHAKE_PORT = 12235
CLIENT_STEP = 1
SERVER_STEP = 2
HEADER_SIZE = 12
MAX_RETRIES = 10
PADDING = 4

STAGE_A_EXPECTED_PAYLOAD_LEN = 12
STAGE_B1_EXP_PAYLOAD_LEN = 4
STAGE_B2_EXP_PAYLOAD_LEN = 8
STAGE_C_EXP_PAYLOAD_LEN = 16
STAGE_D_EXP_PAYLOAD_LEN = 4


# thread handler
def handle_client_handshake(req_bytes, sock, client_addr):
    status_a = stage_a(req_bytes, sock, client_addr)
    if not status_a:
        log(f"{client_addr[0]} - stage a failed.")
        return

    log(f"{client_addr[0]} - stage a success.")

    output_num, output_len, output_port, output_secret = status_a
    status_b = stage_b(output_port, output_len, output_num, output_secret)
    if not status_b:
        log(f"{client_addr[0]} - stage b failed.")
        return

    log(f"{client_addr[0]} - stage b success.")

    secret_b, sock = status_b
    status_c = stage_c(secret_b, sock)
    if not status_c:
        log(f"{client_addr[0]} - stage c failed.")
        return

    log(f"{client_addr[0]} - stage c success.")

    sock, connection, client_addr, output_num_c, output_len_c, output_secret_c, output_c = status_c
    status_d = stage_d(sock, connection, client_addr, output_num_c, output_len_c, output_secret_c, output_c)
    if not status_d:
        log(f"{client_addr[0]} - stage d failed.")
        return

    log(f"{client_addr[0]} - stage d success.")

def check_header(header, exp_payload_len, exp_secret, exp_step):
    plen, psecret, exp_step, num = unpack('!IIHH', header)
    return exp_step == CLIENT_STEP and plen == exp_payload_len and psecret == exp_secret

def start_server(port):
    log(f"Starting server on port {port}")

    # create main handshake init socket
    handshake_init_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    handshake_init_sock.bind((HOST, port))
    retries = 0
    while True:
        try:
            # receive request
            stage_a_request, client_addr = \
                handshake_init_sock.recvfrom(HEADER_SIZE + STAGE_A_EXPECTED_PAYLOAD_LEN)
            stage_a_arguments = (stage_a_request, handshake_init_sock, client_addr)
            # start thread to handle handshake
            _thread.start_new_thread(handle_client_handshake, stage_a_arguments)
            retries = 0
        except socket.timeout:
            retries += 1
            if retries >= MAX_RETRIES:
                log("Exiting...")
                break
            handshake_init_sock.close()
            # create new socket for handshake init
            handshake_init_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            handshake_init_sock.bind((HOST, port))
    handshake_init_sock.close()

def stage_a(req_bytes, sock, client_addr) -> Optional[tuple[int]]:
    header, payload = req_bytes[:HEADER_SIZE], req_bytes[HEADER_SIZE:]

    # verify client request
    if not check_header(header, STAGE_A_EXPECTED_PAYLOAD_LEN, 0, CLIENT_STEP):
        return None

    payload_str, = unpack(f'!{STAGE_A_EXPECTED_PAYLOAD_LEN}s', payload)
    payload_str = payload_str.decode('utf-8').strip('\x00')

    if payload_str != "hello world":
        return None

    # generate response
    out_num = randint(5, 30)
    out_len = randint(15, 50)
    out_port = randint(60000, 65000)
    out_secret = randint(1, 100)

    payload = pack("!IIII", out_num, out_len, out_port, out_secret)
    res = Response(Header(16, 0, SERVER_STEP), payload)

    # send response
    sock.sendto(res.to_network_bytes(), client_addr)
    return out_num, out_len, out_port, out_secret

def stage_b(udp_port: int, p_len_unpadded: int, num_packets: int, a_secret):
    # create socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((HOST, udp_port))
    sock.settimeout(3)

    # need to add 4 bytes for packet id
    p_len_with_id = p_len_unpadded + 4

    # receive and ack num packets
    ack_num = 0
    addr = None
    p_len_padded = int(ceil(p_len_with_id/PADDING) * PADDING)
    while ack_num < num_packets:
        try:
            data, addr = sock.recvfrom(p_len_padded + HEADER_SIZE)
            header, payload = data[:HEADER_SIZE], data[HEADER_SIZE:]

            if not check_header(header, p_len_with_id, a_secret, CLIENT_STEP):
                sock.close()
                return None

            if len(payload) != p_len_padded:
                sock.close()
                return None

            # check payload is all 0s besides packet id
            if any(payload[4:]):
                sock.close()
                return None

            # check packet id. if sent out of order, drop client
            packet_id, = unpack('!I', payload[:4])
            if packet_id != ack_num:
                sock.close()
                return None

            # randomly decide to drop packet
            if randint(0, 5) == 0:
                continue

            # ack packet
            acked_packet_id = pack('!I', packet_id)

            # Note: Server sends response with client step in stage b1
            header = Header(STAGE_B1_EXP_PAYLOAD_LEN, a_secret, CLIENT_STEP)
            ack_response = Response(header, acked_packet_id)
            sock.sendto(ack_response.to_network_bytes(), addr)
            ack_num += 1
        except:
            sock.close()
            return None

    sock.close()

    output_tcp_port = randint(50000, 55000)
    output_secret_b = randint(1, 100)

    output_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    output_sock.settimeout(3)
    output_sock.bind((HOST, output_tcp_port))
    output_sock.listen()

    payload = pack("!II", output_tcp_port, output_secret_b)
    header = Header(STAGE_B2_EXP_PAYLOAD_LEN, a_secret, SERVER_STEP)
    response = Response(header, payload)
    sock.sendto(response.to_network_bytes(), addr)

    return output_secret_b, output_sock


def stage_c(secret_b, sock):

    connection, client_addr = None, None

    try:
        connection, client_addr = sock.accept()
        connection.settimeout(3)
    except:
        sock.close()
        return None

    # create payload and response
    output_num = randint(5, 30)
    output_len = randint(15, 50)
    output_secret = randint(1, 100)
    output_char_int = randint(ord('a'), ord('z'))
    output_char = chr(output_char_int).encode('utf-8')

    payload = pack('!IIIc', output_num, output_len, output_secret, output_char)
    header = Header(len(payload), secret_b, SERVER_STEP)
    res = Response(header, payload)

    # send response
    msg = res.to_network_bytes()
    assert len(msg) == HEADER_SIZE + STAGE_C_EXP_PAYLOAD_LEN
    connection.sendto(msg, client_addr)
    return sock, connection, client_addr, output_num, \
        output_len, output_secret, output_char

def stage_d(sock, conn, client_addr, num2, len2, p_secret, c):

    # receive num packets
    num_req = 0
    while num_req < num2:
        padded_len = int(ceil(len2 / PADDING) * PADDING)
        data = conn.recv(padded_len + HEADER_SIZE)
        header = data[:HEADER_SIZE]
        payload = data[HEADER_SIZE:]

        if not check_header(header, len2, p_secret, 1):
            sock.close()
            conn.close()
            return None

        if len(payload) != padded_len:
            sock.close()
            conn.close()
            return None

        payload_str, = unpack(f'!{padded_len}s', payload)
        payload_str = payload_str.decode('utf-8').strip('\x00')

        # check the character
        for i in range(len(payload_str)):
            if payload_str[i] != c.decode('utf-8'):
                sock.close()
                conn.close()
                return None

        num_req += 1

    output_secret = randint(1, 100)
    payload = pack('!I', output_secret)
    header = Header(STAGE_D_EXP_PAYLOAD_LEN, p_secret, SERVER_STEP)
    res = Response(header, payload)
    msg = res.to_network_bytes()
    assert len(msg) == HEADER_SIZE + STAGE_D_EXP_PAYLOAD_LEN
    conn.sendto(res.to_network_bytes(), client_addr)
    sock.close()
    conn.close()
    return (output_secret)


def main():
    start_server(UDP_INITIATE_HANDSHAKE_PORT)

if __name__ == "__main__":
    main()
