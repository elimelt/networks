import socket
import _thread
from struct import pack, unpack
import random
from response import Response, Header

HOST = "attu3.cs.washington.edu"
PORT = 12235
STEP = 2
HEADER_SIZE = 12

STAGE_A_EXPECTED_PAYLOAD_LEN = 12

# thread handler
def handle_client_handshake(req_bytes, sock, client_addr):
    print("connection: ", client_addr)
    print("starting stage a:")
    status_a = stage_a(req_bytes, sock, client_addr)
    if status_a:
        print("stage a success.")
    status_b = stage_b()

def check_header(header, payload_len, secret, step):
    plen, psecret, step, num = unpack('!IIHH', header)
    if step != 1 or plen != payload_len or psecret != secret:
        return False
    return True

def start_server(port):
    
    print("starting server:")
    sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    sock.bind((HOST, port))

    while True:
        try:
            stage_a_request, client_addr = sock.recvfrom(24)
            _thread.start_new_thread(handle_client_handshake, (stage_a_request, sock, client_addr))
        except:
            sock.close()

def stage_a(req_bytes, sock, client_addr) -> tuple[int]:
    
    header = req_bytes[:HEADER_SIZE]
    payload = req_bytes[HEADER_SIZE:]
    if not check_header(header, STAGE_A_EXPECTED_PAYLOAD_LEN, 0, 1):
        return None

    # if len(payload) != STAGE_A_EXPECTED_PAYLOAD_LEN:
    #     return None

    payload_str, = unpack(f'!{STAGE_A_EXPECTED_PAYLOAD_LEN}s', payload)
    print("unpacked string", payload_str)
    if payload_str != "hello world":
        return None

    # num, len, udp_port, secretA
    output_num = random.randint(5, 30)
    output_len = random.randint(15, 50)
    output_port = random.randint(60000, 65000)
    output_secret = random.randint(1, 100)

    payload, = pack("!IIII", output_num, output_len, output_port, output_secret)
    response = Response(Header(16, 0, 1), payload)

    msg = response.to_network_bytes()

    sock.sendto(msg, client_addr)
    print("sent message A to", client_addr)
    return (output_num, output_len, output_port, output_secret)

def stage_b(udp_port: int, expected_len) -> bool:
    sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    sock.bind((HOST, udp_port))


def main():
    start_server(PORT)


if __name__ == "__main__":
    main()