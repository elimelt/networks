from struct import pack, unpack
from math import ceil

STUDENT_ID = 822

class Header:

    def __init__(self, payload_len, psecret, step):
        self.payload_len = payload_len   # 4 bytes
        self.psecret = psecret   # 4 bytes
        self.step = step   # 2 bytes
        self.sid_checksum = STUDENT_ID   # 2 bytes - last 3 digits of Elijah's netid


class Request:
    def __init__(self, header=None, payload=b""):
        self.header: Header = header
        self.payload: bytes = payload

    # payload is type bytes literal
    def add_payload(self, payload: bytes):
        self.payload = payload

    def add_header(self, header):
        self.header = header

    def to_network_bytes(self):
        # ! means network byte order
        # I means unsigned int
        # H means unsigned short
        padded_len = int(ceil(self.header.payload_len/4) * 4)
        header_bytes = pack('!IIHH', self.header.payload_len, self.header.psecret, self.header.step, self.header.sid_checksum)
        payload_bytes = pack(f'!{self.header.payload_len}s', self.payload)
        padding = pack(f'!{padded_len - self.header.payload_len}s', b'\x00'* (padded_len - self.header.payload_len))
        return header_bytes + payload_bytes + padding