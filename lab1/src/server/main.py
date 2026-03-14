from typing import Any
import os
import socket
import argparse

from src.models.common import Commands, Payload, UploadHeader, UploadPayload, full_recv
from src.models.response import (
    ResponseHeader,
    NetCode,
    PayloadType,
    Filenames,
)
from src.models.files import read_file, write_file
from src.models.request import REQUEST_BYTES_SIZE, Request
import inspect


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


def send_response_header(
    s: socket.socket, addr: tuple[str, int], resp: ResponseHeader
) -> None:
    debug_print("Sending response header")
    try:
        s.sendall(resp.serialize())
    except OSError as e:
        debug_print(f"Can't send req {resp} with send error {e}")


def send_response_payload(
    s: socket.socket, addr: tuple[str, int], payload: Payload
) -> None:
    debug_print("Sending response payload")
    try:
        s.sendall(payload.payload)
    except Exception as e:
        debug_print(f"Can't send response payload, error : {e}")


Filepath = str
FILEPATH: Filepath = os.path.join("src", "server", "server_files")
Filename = str


def get_files(server_filepath: Filepath) -> list[Filename]:
    filenames: list[Filename] = []
    debug_print(f"Server has files on {server_filepath}")
    for entry in os.scandir(server_filepath):
        if entry.is_file():
            # debug_print(f"\n\t{entry.name}")
            filenames.append(entry.name)
    return filenames


def command_list() -> tuple[ResponseHeader, Payload]:
    filename_list: list[Filename] = get_files(FILEPATH)
    filenames: Filenames = Filenames(filename_list)
    data = filenames.serialize()
    payload: Payload = Payload(data)
    resp: ResponseHeader = ResponseHeader(NetCode.OK, PayloadType.LIST, len(payload))
    return (resp, payload)


def handle_exit(conn: socket.socket) -> None:
    debug_print(f"clossing connection with client {addr}")
    conn.close()
    return


def handle_list(conn: socket.socket) -> None:
    debug_print("Send file list to client")
    header, payload = command_list()
    try:
        send_response_header(conn, addr, header)
        send_response_payload(conn, addr, payload)
    except Exception as e:
        debug_print(f"Can't send command list {e}")
        debug_print(f"Closing connection with {addr}")
        conn.close()


def handle_download(conn: socket.socket, data_request: Request) -> None:
    debug_print(f"Client want download {data_request.payload}")
    if not data_request.payload:
        raise ValueError("Received bad payload")

    payload = Payload(bytes())
    code = NetCode.ERROR
    payload_type = PayloadType.NONE
    payload_len = 0

    try:
        payload = Payload(read_file(os.path.join(FILEPATH, data_request.payload)))
        code = NetCode.OK
        payload_type = PayloadType.FILE
        payload_len = len(payload)
    except (IOError, ValueError) as e:
        if isinstance(e, ValueError):
            print(f"Bad file with name {data_request.payload} error:{e}")
    finally:
        resp = ResponseHeader(code, payload_type, payload_len)
        send_response_header(conn, addr, resp)
        send_response_payload(conn, addr, payload)


def handle_upload(conn: socket.socket, data_request: Request) -> None:
    debug_print("Handling Upload")
    if not data_request.payload:
        raise ValueError("Received bad payload")
    header_data: bytes = full_recv(conn, 4)
    upload_header: UploadHeader = UploadHeader.deserialize(header_data)

    payload_data: bytes = full_recv(conn, upload_header.size)
    upload_data = header_data + payload_data
    upload: UploadPayload = UploadPayload.deserialize(upload_data)
    debug_print(f"file {len(upload.payload)} bytes")
    filepath = os.path.join(FILEPATH, data_request.payload)
    write_file(filepath,upload.payload)
    debug_print(f"wrote file at {filepath}")


def serve_connection(conn: socket.socket) -> None:
    debug_print(f"Connected by {addr}")
    while True:
        debug_print("In cycle")
        try:
            data: bytes = conn.recv(REQUEST_BYTES_SIZE)
            if not data:
                print("Client disconnected")
                break
            data_request: Request = Request.deserialize(data)
        except Exception as e:
            debug_print(f"error {e}")
            continue
        try:
        # debug_print(data)
            match data_request.cmd:
                case Commands.EXIT:
                    handle_exit(conn)
                case Commands.LIST:
                    handle_list(conn)
                    continue
                case Commands.DOWNLOAD:
                    handle_download(conn, data_request)
                    continue
                case Commands.UPLOAD:
                    handle_upload(conn, data_request)
                    continue
                case _:
                    raise RuntimeError("unimplemented")
        except ValueError as e:
            print(e)
        except Exception as e:
            print(f"unexpected {e}")


debug_print("Starting server")
parser = argparse.ArgumentParser()

parser.add_argument("PORT", type=int, help="server port", default=8000, nargs="?")
parser.add_argument("IP", type=str, help="server ip", default="127.0.0.1", nargs="?")
args = parser.parse_args()
HOST = args.IP
PORT = args.PORT
debug_print(f"Server on {HOST}:{PORT}")

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen()
    while True:
        conn, addr = s.accept()
        with conn:
            try:
                serve_connection(conn)
            except KeyboardInterrupt:
                print("Cathced ctrl+c,closing server")
                s.close()
                exit(0)
