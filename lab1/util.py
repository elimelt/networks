from struct import pack, unpack

# takes in header
def validate_response(header, silent=False):
    payload_len, psecret, step, num = unpack('!IIHH', header)
    if step != 2:
        if not silent:
            print("bad response:", payload_len, psecret, step, num)
        return False
    else:
        if not silent:
            print("response validated")
        return True

