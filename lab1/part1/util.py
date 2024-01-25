from struct import pack, unpack

# takes in header and checks that the step is as expected.
def validate_header(header, expected_step):
    _, _, step, _ = unpack('!IIHH', header)
    if step != expected_step:
        return False
    else:
        return True
