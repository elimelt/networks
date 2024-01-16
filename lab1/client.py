from request import Request, Header



if __name__ == '__main__':

    req = Request()\
        .with_payload([1,2,3,4,5,6,7,8,9,10])\
        .with_header(Header())

    print(req.to_network_bytes())
