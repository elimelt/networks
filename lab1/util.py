import socket
import logging
from request import Request, Header
from datetime import datetime, timedelta
from struct import pack, unpack
import matplotlib.pyplot as plt



LOG_TO_FILE = True

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(message)s')

# Create a console handler and set level to INFO
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Check if flag is set to log to a file
if LOG_TO_FILE:
    # Create a file handler and set level to INFO
    file_handler = logging.FileHandler('log.txt')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

def log(s):
    logger.info(s)



# takes in header
def validate_header(header, silent=False):
    payload_len, psecret, step, num = unpack('!IIHH', header)
    if step != 2:
        if not silent:
            log(f"bad response: {payload_len}, {psecret}, {step}, {num}")
        return False
    else:
        if not silent:
            log("response validated")
        return True

# returns true if server is running, false otherwise
def test_and_record_if_server_running(host):
    status = "up"
    # initiate handshake to see if server is running
    req = Request(Header(12, 0, 1), b"hello world")
    sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    sock.settimeout(0.5)
    try:
        sock.sendto(req.to_network_bytes(), (host, 12235))
        response = sock.recv(12 + 4 * 4)
        print(f"{host}:12235 is up")
    except socket.timeout:
        print(f"{host}:12235 is down")
        status = "down"

    timestamp = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")

    with open('./availability.log', 'a') as f:
        f.write(f'{timestamp} - {host}:12235 is {status}\n')

    return status == "up"


def parse_logs():
    out = []
    with open('./availability.log', 'r') as f:
        lines = f.readlines()
        for line in lines:
            timestamp, message = line.split(' - ')

            time_val = datetime.strptime(timestamp, "%m/%d/%Y, %H:%M:%S")
            host = message.split(':')[0]
            status = message.split(' ')[-1].strip()

            out.append((time_val, host, status))
    return out

