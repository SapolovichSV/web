import socket
from src.models import Commands, Request


def parse_user_commands() -> Request:
    inp = (
        input("HELP:\n\t EXIT\n\t LIST\n\t UPLOAD  <filename>\n\t DOWNLOAD <filename>")
        .strip()
        .split()
    )

    req: Request = Request(Commands.EXIT, None)
    match len(inp):
        case 1:
            match inp[0]:
                case "EXIT":
                    req = Request(Commands.EXIT, None)
                case "LIST":
                    req = Request(Commands.LIST, None)
                case _:
                    pass
        case 2:
            match inp[0]:
                case "UPLOAD":
                    req = Request(Commands.UPLOAD, inp[1])
                case "DOWNLOAD":
                    req = Request(Commands.DOWNLOAD, inp[1])
                case _:
                    pass
        case _:
            raise ValueError(f"Incorrect user input: {len(inp)}")
    return req


def send_request(s: socket.socket, addr: tuple[str, int], req: Request) -> None:

    print("Closing connection and exit")
    print(f"Sending requst {req}")

    try:
        s.sendall(req.serialize())

    except OSError as e:
        print(f"Can't send req {req} with send error {e}")
    # print("Getting response")

    # try:
    #     data: Response = Response.deserialize(s.recv(4, 0))
    # except ValueError as e:
    #     raise ValueError(f"Invalid respone: {e}")
    # return data


print("Starting client")
SERVER_IP = "127.0.0.1"
SERVER_PORT = 8000
SERVER_ADDR = (SERVER_IP, SERVER_PORT)
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect(SERVER_ADDR)
    print(f"Connected to {SERVER_ADDR}")
    while True:
        try:
            req = parse_user_commands()
        except ValueError as e:
            print(f"input: bad command {e}")
            continue
        try:
            send_request(s, SERVER_ADDR, req)
        except Exception as e:
            print(f"Can't send request error: {e}")
            continue

print("Stop client")
