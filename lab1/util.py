from struct import pack, unpack

def validate_response(response):
    payload_len, psecret, step, num = unpack('!IIHH', response)
    if step != 2:
        print("bad response:", payload_len, psecret, step, num)
    else:
        print("response validated")


