import os
from typing import Any
import argparse
import inspect
import socket
from sys import exit

from src.models.common import Commands, full_recv, UploadPayload
from src.models.request import Request
from src.models.files import read_file, write_file

from src.models.response import (
    RESPONSE_BASE_SIZE_BYTES,
    Filenames,
    NetCode,
    PayloadType,
    ResponseHeader,
)


def debug_print(*args: Any) -> None:
    frame = inspect.currentframe()
    if frame is None:
        print("[unknown location]", *args)
        return
    caller = frame.f_back
    if caller is None:
        print("[unknown caller]", *args)
        return
    lineno = caller.f_lineno
    filename = caller.f_code.co_filename
    print(f"[{filename}:{lineno}]", *args)


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
                    raise ValueError(f"Incorrect user input: {inp[0]}")
        case 2:
            match inp[0]:
                case "UPLOAD":
                    req = Request(Commands.UPLOAD, inp[1])
                case "DOWNLOAD":
                    req = Request(Commands.DOWNLOAD, inp[1])
                case _:
                    raise ValueError(f"Incorrect user input: {inp[1]}")
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


def send_upload_payload(
    s: socket.socket, addr: tuple[str, int], upload_payload: UploadPayload
) -> None:
    try:
        s.sendall(upload_payload.get_header())
        s.sendall(upload_payload.get_payload())
    except Exception as e:
        print(f"Error : {e}")


def shutdown_client(s: socket.socket) -> None:
    s.close()
    exit(0)


def catch_response_header(s: socket.socket) -> ResponseHeader:
    return ResponseHeader.deserialize(full_recv(s, RESPONSE_BASE_SIZE_BYTES))


def handle_response(s: socket.socket, resp_header: ResponseHeader) -> None:
    FILEPATH = os.path.join(os.path.curdir, "downloaded")
    match resp_header.payload_type:
        case PayloadType.LIST:
            data_list: bytes = full_recv(s, resp_header.payload_len)
            filenames: Filenames = Filenames.deserialize(data_list)
            debug_print(filenames)
        case PayloadType.FILE:
            data_file: bytes = full_recv(s, resp_header.payload_len)
            write_file(FILEPATH, data_file)

        case _:
            raise RuntimeError("unimplemented")


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
                req: Request = parse_user_commands()
            except ValueError as e:
                print(f"input: bad command {e}")
                continue
            if req.cmd == Commands.UPLOAD:
                if not req.payload:
                    print(f"Bad input {req.payload}")
                    continue
                try:
                    payload = UploadPayload(read_file(req.payload))
                except (IOError, ValueError) as e:
                    print(f"Command error : {e}")
                    continue
                send_request(s, SERVER_ADDR, req)
                send_upload_payload(s, SERVER_ADDR, payload)
                continue

            try:
                debug_print(f"Sending request {req}")
                send_request(s, SERVER_ADDR, req)
                if req.cmd == Commands.EXIT:
                    print("Closing client")
                    shutdown_client(s)
                debug_print("Catching Response")
                header: ResponseHeader = catch_response_header(s)
                debug_print(f"Catching ResponseHeader {header}")
                match header.code:
                    case NetCode.OK:
                        print(f"Catched header {header}")
                        handle_response(s, header)

                    case NetCode.ERROR:
                        print(f"Catched header {header}")
                        print("Bad netcode, clossing connection")
                        shutdown_client(s)
            except Exception as e:
                print(f"Can't send request error: {e}")
                continue
    except KeyboardInterrupt:
        print("\nCatched ctrl+c,stopping client")
        shutdown_client(s)

print("Stop client")
