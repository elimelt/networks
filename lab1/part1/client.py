import socket
from request import Request, Header
from util import validate_header, log
from struct import pack, unpack

HOST = "attu4.cs.washington.edu"
TIMEOUT = 0.5
UDP_PORT_A = 12235
CLIENT_STEP = 1
SERVER_STEP = 2
HEADER_SIZE = 12

STAGE_A_EXP_PAYLOAD_LEN = 16
STAGE_B1_EXP_PAYLOAD_LEN = 4
STAGE_B2_EXP_PAYLOAD_LEN = 8
STAGE_C_EXP_PAYLOAD_LEN = 16
STAGE_D_EXP_PAYLOAD_LEN = 4


def stage_a() -> tuple[int, int, int, int]:

    client_payload = b"hello world"

    req = Request(Header(12, 0, CLIENT_STEP), client_payload)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(req.to_network_bytes(), (HOST, UDP_PORT_A))
    response = sock.recv(HEADER_SIZE + STAGE_A_EXP_PAYLOAD_LEN)
    sock.close()

    # verifies that the response is long enough to unpack
    if len(response) != HEADER_SIZE + STAGE_A_EXP_PAYLOAD_LEN:
        log("bad response...exiting - stage: A")
        exit(1)

    server_header = response[:HEADER_SIZE]
    server_payload = response[HEADER_SIZE:]

    if not validate_header(server_header, SERVER_STEP):
        log("bad response...exiting - stage: A")
        exit(1)

    num_a, len_a, udp_port_a, secretA = unpack('!IIII', server_payload)
    return num_a, len_a, udp_port_a, secretA


def stage_b(num_packets, payload_len, udp_port, secret_a) -> tuple[int, int]:

    client_header = Header(payload_len + 4, secret_a, CLIENT_STEP)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # socket timeout when for when packet not acked
    sock.settimeout(TIMEOUT)

    packet_id = 0
    while packet_id < num_packets:

        client_payload = pack(f"!I{payload_len}s", packet_id, b'\x00' * payload_len)
        req = Request(client_header, client_payload)

        acked = False
        response = None

        # continues to send until acked
        while not acked:
            sock.sendto(req.to_network_bytes(), (HOST, udp_port))
            try:
                response = sock.recv(HEADER_SIZE + STAGE_B1_EXP_PAYLOAD_LEN)

                # verifies that the response is long enough to unpack
                if len(response) != HEADER_SIZE + STAGE_B1_EXP_PAYLOAD_LEN:
                    continue
                
                server_header = response[:HEADER_SIZE]
                server_payload = response[HEADER_SIZE:]

                if not validate_header(response[:HEADER_SIZE], 1):
                    continue
                if unpack('!I', server_payload)[0] == packet_id:
                    acked = True
            except socket.timeout:
                continue
        packet_id += 1

    response = sock.recv(HEADER_SIZE + STAGE_B2_EXP_PAYLOAD_LEN)
    sock.close()

    # verifies that the response is long enough to unpack
    if len(response) != HEADER_SIZE + STAGE_B2_EXP_PAYLOAD_LEN:
        log("bad response...exiting - stage: B")
        exit(1)

    server_header = response[:HEADER_SIZE]
    server_payload = response[HEADER_SIZE:]

    if not validate_header(server_header, SERVER_STEP):
        log("bad response...exiting - stage: B")
        exit(1)

    tcp_port, secret_a = unpack('!II', server_payload)

    return tcp_port, secret_a


def stage_c(tcp_port) -> tuple[int, int, int, str, socket.socket]:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, tcp_port))

    response = sock.recv(HEADER_SIZE + STAGE_C_EXP_PAYLOAD_LEN)

    # verifies that the response is long enough to unpack
    if len(response) != HEADER_SIZE + STAGE_C_EXP_PAYLOAD_LEN:
        log("bad response...exiting - stage: C")
        exit(1)

    server_header = response[:HEADER_SIZE]
    server_payload = response[HEADER_SIZE:]

    if not validate_header(server_header, SERVER_STEP):
        log("bad response...exiting - stage: C")
        exit(1)

    # last 3 bytes are padding
    num_c, len_c, secret_c, c, _, _, _ = unpack('!IIIcccc', server_payload)

    return num_c, len_c, secret_c, c, sock


def stage_d(num_packets, payload_len, secret_c, c, sock_c):
    req_payload = bytearray()
    req_payload.extend(c * payload_len)

    req = Request(Header(payload_len, secret_c, CLIENT_STEP), req_payload)
    msg = req.to_network_bytes()

    for _ in range(num_packets):
        sock_c.send(msg)

    response = sock_c.recv(HEADER_SIZE + STAGE_D_EXP_PAYLOAD_LEN)
    sock_c.close()

    # verifies that the response is long enough to unpack
    if len(response) != HEADER_SIZE + STAGE_D_EXP_PAYLOAD_LEN:
        log("bad response...exiting - stage: D")
        exit(1)

    server_header = response[:HEADER_SIZE]
    server_payload = response[HEADER_SIZE:]

    if not validate_header(server_header, SERVER_STEP):
        log("bad response...exiting - stage: D")
        exit(1)

    secret_d, = unpack('!I', server_payload)

    return secret_d


def main():

    num_a, len_a, udp_port_a, secretA = stage_a()
    log(f"finished stage a - secretA: {secretA}")

    tcp_port_b, secret_b = stage_b(num_a, len_a, udp_port_a, secretA)
    log(f"finished stage b - secretB: {secret_b}")

    num_c, len_c, secret_c, c, sock_c = stage_c(tcp_port_b)
    log(f"finished stage c - secretC: {secret_c}")

    secret_c = stage_d(num_c, len_c, secret_c, c, sock_c)
    log(f"finished stage d - secretD: {secret_c}")

if __name__ == '__main__':
    main()