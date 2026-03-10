import argparse
from sys import exit
import socket
from src.models import Commands, Request


def parse_user_commands() -> Request:
    inp = (
        input(
            "HELP:\n\t EXIT\n\t LIST\n\t UPLOAD  <filename>\n\t DOWNLOAD <filename>\n:"
        )
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


def shutdown_client(s: socket.socket) -> None:
    s.close()
    exit(0)


print("Starting client")

parser = argparse.ArgumentParser()
parser.add_argument("PORT", type=int, help="server port", default=8000, nargs="?")
parser.add_argument("IP", type=str, help="server ip", default="127.0.0.1", nargs="?")
args = parser.parse_args()
SERVER_IP = args.IP
SERVER_PORT = args.PORT
SERVER_ADDR = (SERVER_IP, SERVER_PORT)
print(f"Server on {SERVER_ADDR}")

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect(SERVER_ADDR)
    print(f"Connected to {SERVER_ADDR}")
    try:
        while True:
            try:
                req = parse_user_commands()
            except ValueError as e:
                print(f"input: bad command {e}")
                continue
            try:
                send_request(s, SERVER_ADDR, req)
                if req.cmd == Commands.EXIT:
                    print("Closing client")
                    shutdown_client(s)
            except Exception as e:
                print(f"Can't send request error: {e}")
                continue
    except KeyboardInterrupt:
        print("\nCatched ctrl+c,sending EXIT,stopping client")
        req: Request = Request(Commands.EXIT, None)
        send_request(s, SERVER_ADDR, req)
        s.close()
        exit(0)

print("Stop client")
