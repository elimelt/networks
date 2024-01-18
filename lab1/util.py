
def print_bytes_n(b: bytes, n: int):
    for i in range(0, len(b), n):
        print(b[i:i+n])

