from struct import pack, unpack

STUDENT_ID = 256

class Header:
    def __init__(self, payload_len, psecret, step):
        # 4 bytes
        self.payload_len = payload_len
        # 4 bytes
        self.psecret = psecret
        # 2 bytes
        self.step = step
        # 2 bytes - last 3 digits of Elijah's netid
        self.sid_checksum = STUDENT_ID
class Request:
    def __init__(self):
        self.header: Header = None
        self.payload: bytes = b""


    def add_payload(self, payload: bytes, size: int):
        self.payload = payload
        self.header.payload_len = size

    def add_header(self, header):
        self.header = header

    def to_network_bytes(self):
        # ! means network byte order
        # I means unsigned int
        # H means unsigned short
        header_bytes = pack('!IIHH', self.header.payload_len, self.header.psecret, self.header.step, self.header.sid_checksum)
        payload_bytes = pack(f'!{self.header.payload_len}s', self.payload)

        # print(list(header_bytes))
        # print(list(payload_bytes))

        ret =  header_bytes + payload_bytes

        # print(list(ret))
        return ret