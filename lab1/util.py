from struct import pack, unpack

# takes in header
def validate_response(header):
    payload_len, psecret, step, num = unpack('!IIHH', header)
    if step != 2:
        print("bad response:", payload_len, psecret, step, num)
    else:
        print("response validated")


