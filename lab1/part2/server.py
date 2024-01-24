import socket
import _thread
from struct import pack, unpack
import random
from response import Response, Header
from math import ceil

HOST = "attu4.cs.washington.edu"
PORT = 12235
STEP = 2
HEADER_SIZE = 12

STAGE_A_EXPECTED_PAYLOAD_LEN = 12

# thread handler
def handle_client_handshake(req_bytes, sock, client_addr):
    #print("connection: ", client_addr)
    status_a = stage_a(req_bytes, sock, client_addr)
    if status_a:
        # print("stage a success.")
        pass
    else:
        return
    output_num, output_len, output_port, output_secret = status_a
    status_b = stage_b(output_port, output_len, output_num, output_secret)
    if status_b:
        # print("stage b success.")
        pass
    else:
        return

    tcp_port, secret_b = status_b
    status_c = stage_c(tcp_port, secret_b)

    if status_c:
        # print("stage c success")
        pass
    else:
        return
    connection, client_addr, output_num_c, output_len_c, output_secret_c, output_c = status_c

    status_d = stage_d(connection, client_addr, output_num_c, output_len_c, output_secret_c, output_c)
    if status_d:
        print("stage d success")

    return


def check_header(header, payload_len, secret, step):
    plen, psecret, step, num = unpack('!IIHH', header)

    if step != 1 or plen != payload_len or psecret != secret:
        return False
    return True

def start_server(port):

    # print("starting server:")
    sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    sock.bind((HOST, port))
    retries_allowed = 10
    while True:
        try:
            stage_a_request, client_addr = sock.recvfrom(24)
            _thread.start_new_thread(handle_client_handshake, (stage_a_request, sock, client_addr))
            retries_allowed = 10
        except:
            retries_allowed -= 1
            if retries_allowed <= 0:
                print('exiting')
                break
            sock.close()
            sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
            sock.bind((HOST, port))
    sock.close()

def stage_a(req_bytes, sock, client_addr) -> tuple[int]:

    header = req_bytes[:HEADER_SIZE]
    payload = req_bytes[HEADER_SIZE:]
    if not check_header(header, STAGE_A_EXPECTED_PAYLOAD_LEN, 0, 1):
        return None

    if len(payload) != STAGE_A_EXPECTED_PAYLOAD_LEN:
        return None

    payload_str, = unpack(f'!{STAGE_A_EXPECTED_PAYLOAD_LEN}s', payload)
    payload_str = payload_str.decode('utf-8').strip('\x00')

    if payload_str != "hello world":
        return None

    # num, len, udp_port, secretA
    output_num = random.randint(5, 30)
    output_len = random.randint(15, 50)
    output_port = random.randint(60000, 65000)
    output_secret = random.randint(1, 100)

    payload = pack("!IIII", output_num, output_len, output_port, output_secret)
    response = Response(Header(16, 0, 2), payload)

    msg = response.to_network_bytes()

    sock.sendto(msg, client_addr)
    #print("sent message A to: ", client_addr)
    return (output_num, output_len, output_port, output_secret)

def stage_b(udp_port: int, p_len_unpadded: int, num_packets: int, a_secret) -> bool:
    #print("starting stage b")
    sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    sock.bind((HOST, udp_port))
    sock.settimeout(3)
    #print("bound to udp port: ", udp_port)

    p_len_with_id = p_len_unpadded + 4

    ack_num = 0
    addr = None
    p_len_padded = int(ceil(p_len_with_id/4) * 4)
    while ack_num < num_packets:
        try:
            data, addr = sock.recvfrom(p_len_padded + HEADER_SIZE)
            header = data[:HEADER_SIZE]
            payload = data[HEADER_SIZE:]

            if not check_header(header, p_len_with_id, a_secret, 1):
                #print("bad header")
                return None

            if len(payload) != p_len_padded:
                return None

            # need to check payload
            payload_content = payload[4:]
            for i in range(len(payload_content)):
                if payload_content[i] != 0:
                    #print("bad payload content")
                    return None

            payload_id = payload[:4]
            packet_id, = unpack('!I', payload_id)
            if packet_id != ack_num:
                #print("bad packet id")
                return None

            # randomly decide to drop packet
            if random.randint(0, 5) == 0:
                continue

            # ack packet
            acked_packet_id = pack('!I', packet_id)

            ack_response = Response(Header(4, a_secret, 1), acked_packet_id)
            sock.sendto(ack_response.to_network_bytes(), addr)
            ack_num += 1
        except:
            return None


    if addr is None:
        #print("no addr...")
        return None

    output_tcp_port = random.randint(50000, 55000)
    output_secret_b = random.randint(1, 100)

    payload = pack("!II", output_tcp_port, output_secret_b)
    response = Response(Header(8, a_secret, 2), payload)
    sock.sendto(response.to_network_bytes(), addr)

    return output_tcp_port, output_secret_b


def stage_c(tcp_port, secret_b):
    # listen on tcp_port
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(3)
    sock.bind((HOST, tcp_port))
    sock.listen()
    connection, client_addr = None, None
    while True:
        try:
            connection, client_addr = sock.accept()
            connection.settimeout(3)
            break
        except:
            sock.close()
            return None

    # num2, len2, secretC, c
    output_num = random.randint(5, 30)
    output_len = random.randint(15, 50)
    output_secret = random.randint(1, 100)
    output_char_int = random.randint(ord('a'), ord('z'))
    output_char = chr(output_char_int).encode('utf-8')

    payload = pack('!IIIc', output_num, output_len, output_secret, output_char)
    header = Header(len(payload), secret_b, 2)
    res = Response(header, payload)

    # # bug in course staff's server implementation ??? or just padding
    # num2, len2, secretC, c, _c1, _c2, _c3 = unpack('!IIIcccc', response[HEADER_SIZE:])

    connection.sendto(res.to_network_bytes(), client_addr)
    return connection, client_addr, output_num, output_len, output_secret, output_char

def stage_d(conn, client_addr, num2, len2, p_secret, c):

    num_req = 0
    while num_req < num2:
        padded_len = int(ceil(len2 / 4) * 4)
        data = conn.recv(padded_len + HEADER_SIZE)
        header = data[:HEADER_SIZE]
        payload = data[HEADER_SIZE:]

        if not check_header(header, len2, p_secret, 1):
            #print("bad header")
            return None

        if len(payload) != padded_len:
            print('bad payload length')
            return None

        payload_str, = unpack(f'!{padded_len}s', payload)
        payload_str = payload_str.decode('utf-8').strip('\x00')

        # check the character
        for i in range(len(payload_str)):
            if payload_str[i] != c.decode('utf-8'):
                #print("bad payload content", payload_str[i], c.decode('utf-8'))
                return None

        num_req += 1

    output_secret = random.randint(1, 100)
    payload = pack('!I', output_secret)
    header = Header(4 , p_secret, 2)
    res = Response(header, payload)

    conn.sendto(res.to_network_bytes(), client_addr)
    return (output_secret)


def main():
    start_server(PORT)


if __name__ == "__main__":
    main()
