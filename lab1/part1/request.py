from struct import pack, unpack
from math import ceil

# Elijah's student id
STUDENT_ID = 822

# Initialize a Header for each client packet to be sent
class Header:

    def __init__(self, payload_len, psecret, step):
        self.payload_len = payload_len   # 4 bytes
        self.psecret = psecret   # 4 bytes
        self.step = step   # 2 bytes
        self.sid_checksum = STUDENT_ID   # 2 bytes

# Initialize and process a client packet to be sent
class Request:
    def __init__(self, header=None, payload=b""):
        self.header: Header = header
        self.payload: bytes = payload

    # add a payload of type bytes literal
    def add_payload(self, payload: bytes):
        self.payload = payload

    # add a header of type Header
    def add_header(self, header: Header):
        self.header = header

    # pack request to network bytes with the below format specifiers: 
    # ! means network byte order
    # I means unsigned int
    # H means unsigned short
    def to_network_bytes(self):
        # calculate length of padding for payload
        padded_len = int(ceil(self.header.payload_len/4) * 4)

        # pack and return the header, payload, padding
        header_bytes = pack('!IIHH', self.header.payload_len, self.header.psecret, self.header.step, self.header.sid_checksum)
        payload_bytes = pack(f'!{self.header.payload_len}s', self.payload)
        padding = pack(f'!{padded_len - self.header.payload_len}s', b'\x00'* (padded_len - self.header.payload_len))
        return header_bytes + payload_bytes + padding