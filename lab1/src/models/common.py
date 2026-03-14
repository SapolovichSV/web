import struct
import socket
from enum import Enum


class Commands(Enum):
    EXIT = 0
    LIST = 1
    UPLOAD = 2
    DOWNLOAD = 3

    def serialize(self) -> bytes:
        return self.value.to_bytes(1, byteorder="big")

    @classmethod
    def deserialize(cls, val: bytes) -> "Commands":
        num: int = int.from_bytes(val, byteorder="big")
        match num:
            case 0:
                return Commands.EXIT
            case 1:
                return Commands.LIST
            case 2:
                return Commands.UPLOAD
            case 3:
                return Commands.DOWNLOAD
            case _:
                raise ValueError(f"Trying to deserealize incorrect command {val!r}")


class Payload:
    payload: bytes

    def __init__(self, data: bytes):
        self.payload = data

    def __len__(self) -> int:
        return len(self.payload)

    def __repr__(self) -> str:
        return f"ResponsePayload(len={len(self.payload)})"


def full_recv(s: socket.socket, needed_bytes: int) -> bytes:
    needed: int = needed_bytes
    data: bytearray = bytearray(needed)
    while needed != 0:
        if needed <= 0:
            raise RuntimeError("UB")
        needed -= s.recv_into(data, needed)
    return bytes(data)


class UploadHeader:
    size: int

    HEADER_FORMAT_STRING = "!I"

    def __init__(self, size_in_bytes: int) -> None:
        if size_in_bytes > (2 ** (32 - 3)) - 1:
            raise ValueError("Too big payload")
        self.size = size_in_bytes

    @classmethod
    def deserialize(cls, data: bytes) -> "UploadHeader":

        header: UploadHeader = struct.unpack(cls.HEADER_FORMAT_STRING, data)[0]
        return cls(header)


class UploadPayload:
    size: UploadHeader
    payload: bytes
    """
    Ну короче size это размер пейлоада в байтах, получается так что наш файлик
    может быть размером максимум в 2^32 - 1 бит, это 512 мегабайт нормас
    """

    def __init__(self, data: bytes) -> None:
        self.size = UploadHeader(len(data))
        self.payload = data

    def serialize(self) -> bytes:
        data: bytearray = bytearray()
        data += struct.pack(self.size.HEADER_FORMAT_STRING, self.size.size)
        data += self.payload
        return bytes(data)

    def get_header(self) -> bytes:
        return self.serialize()[0:4]

    def get_payload(self) -> bytes:
        return self.serialize()[4:]

    @classmethod
    def deserialize(cls, payload_data: bytes) -> "UploadPayload":
        return cls(payload_data[4:])
