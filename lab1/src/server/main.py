from typing import Annotated
import os
from os import path
import socket
import argparse
from src.models import (
    REQUEST_BYTES_SIZE,
    Request,
    Commands,
    ResponseHeader,
    NetCode,
    PayloadType,
    ResponsePayload,
    Filenames,
)

print("Starting server")
parser = argparse.ArgumentParser()

parser.add_argument("PORT", type=int, help="server port", default=8000, nargs="?")
parser.add_argument("IP", type=str, help="server ip", default="127.0.0.1", nargs="?")
args = parser.parse_args()
HOST = args.IP
PORT = args.PORT
print(f"Server on {HOST}:{PORT}")


def send_response_header(
    s: socket.socket, addr: tuple[str, int], resp: ResponseHeader
) -> None:
    print("Sending response")
    try:
        s.sendall(resp.serialize())
    except OSError as e:
        print(f"Can't send req {resp} with send error {e}")
def send_response_payload(
    s:socket.socket,addr:tuple[str,int],payload:ResponsePayload
) -> None:
    print("Sending response")
    try:
        s.sendall(payload.payload)
    except Exception as e:
        print(f"Can't send response payload, error : {e}")


Filepath = str
FILEPATH: Filepath = os.path.join("src", "server", "server_files")
Filename = str


def get_files(server_filepath: Filepath) -> list[Filename]:
    filenames: list[Filename] = []
    # print(f"Server has files on {server_filepath}")
    for entry in os.scandir(server_filepath):
        if entry.is_file():
            print(f"\n\t{entry.name}")
            filenames.append(entry.name)
    return filenames


def command_list() -> tuple[ResponseHeader, ResponsePayload]:
    filenames: list[Filename] = get_files(FILEPATH)
    filenames: Filenames = Filenames(filenames)
    payload: ResponsePayload = ResponsePayload(filenames.serialize())
    resp: ResponseHeader = ResponseHeader(NetCode.OK, PayloadType.LIST, len(payload))
    return (resp, payload)


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    while True:
        conn, addr = s.accept()
        with conn:
            print(f"Connected by {addr}")
            while True:
                try:
                    data: bytes = conn.recv(REQUEST_BYTES_SIZE)
                    if not data:
                        continue
                    data: Request = Request.deserialize(data)
                except KeyboardInterrupt:
                    print("Catched ctr+c,closing server")
                    s.close()
                    break
                except Exception as e:
                    print(f"error {e}")
                    continue
                print(data)
                match data.cmd:
                    case Commands.EXIT:
                        print(f"clossing connection with client {addr}")
                        # resp: Response = Response(NetCode.OK, PayloadType.NONE, b"")
                        # try:
                        #     send_response(conn, addr, resp)
                        # except Exception as e:
                        #     print(f"Error,can't send response {e}")
                        conn.close()
                        break
                    case Commands.LIST:
                        print("Send file list to client")
