class Header:
    def __init__(self):
        # 4 bytes
        self.payload_len = 0
        # 4 bytes
        self.psecret = 0  
        # 2 bytes
        self.step = 0
        # 2 bytes
        self.sid_checksum = 822

class Request:
    def __init__(self):
        self.header = Header()
        self.payload = []
        
    def with_payload(self, payload):
        self.payload = payload
        self.header.payload_len = len(payload)
        return self

    def with_header(self, header):
        self.header = header
        return self
        
    def to_network_bytes(self):
        print("Request::to_network_bytes not implemented")
        exit(1)


