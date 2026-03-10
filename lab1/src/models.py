from array import array
import os
from typing import Optional, Annotated
import struct
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


class NetCode(Enum):
    OK = 0
    ERROR = 1


class PayloadType(Enum):
    NONE = 0
    FILE = 1
    LIST = 2
    PAYLOAD_LEN = 3


RESPONSE_BASE_SIZE_BYTES = 4


# 6 Bytes header
class ResponseHeader:
    """
    6-байтовый заголовок пакета:

    Byte 0      → code (NetCode, 1 byte)
    Byte 1      → payload_type (PayloadType, 1 byte)
    Bytes 2-5   → payload length (unsigned short, 4 bytes)

    Attributes:
        code (NetCode): Код ответа
        payload_type (PayloadType): Тип payload
        payload_len (int): Размер пейлоада
    В случае методов UPLOAD и DOWNLOAD,LIST мы должны сначала отправить response с
    типом PayloadType
    где в payloade укажем длину данных
    потом отправить респонс с самим ResponsePayload, уже зная его размер
    """

    code: NetCode
    payload_type: PayloadType
    payload_len: int
    FORMAT_STRING: str = "!BBI"
    SIZE: int = struct.calcsize(FORMAT_STRING)
    MAX_PAYLOAD_LENGHT_BYTES = 4

    def __init__(
        self, code: NetCode, payload_type: PayloadType, payload_len: int
    ) -> None:
        self.code = code
        self.payload_type = payload_type
        self.payload_len = payload_len

    def __repr__(self) -> str:
        return (
            f"Response("
            f"code={self.code.name}, "
            f"payload_type={self.payload_type.name}, "
            f"payload_len={self.payload_len}"
            f")"
        )

    def serialize(self) -> bytes:
        return struct.pack(
            self.FORMAT_STRING,
            self.code.value,
            self.payload_type.value,
            self.payload_len,
        )

    @classmethod
    def deserialize(cls, val: bytes) -> "ResponseHeader":
        """
        Десериализация:
        - val: байты, содержащие код, payload_type, длину пейлоада
        """
        if len(val) != 6:
            raise ValueError(f"Data has size{len(val)} ,must be {6},can't deserialize")

        code_val, payload_type_val, payload_len = struct.unpack(
            cls.FORMAT_STRING, val[: cls.SIZE]
        )
        return cls(NetCode(code_val), PayloadType(payload_type_val), payload_len)
        # Если payload_type == PAYLOAD_LEN, payload содержит просто длину следующего payload
        # Сервер/клиент должен отдельно обработать этот случай


class ResponsePayload:
    payload: bytes

    def __init__(self, data: bytes):
        self.data = data

    def __len__(self):
        return len(self.data)

    def __repr__(self):
        return f"ResponsePayload(len={len(self.data)})"


FILENAME_LEN: int = 32
Filename = Annotated[str, 32]


REQUEST_BYTES_SIZE = 1 + FILENAME_LEN


class Request:
    cmd: Commands
    payload: Optional[Filename]

    def __init__(self, cmd: Commands, payload: Optional[Filename]):
        self.cmd = cmd
        if payload is not None and (len(payload) > FILENAME_LEN or len(payload) < 0):
            raise ValueError("Bad payload size")
        self.payload = payload

    def __repr__(self) -> str:
        return f"Request(cmd={self.cmd.name}, payload={self.payload})"

    def serialize(self) -> bytes:
        b: bytes = self.cmd.serialize()
        if self.payload is not None:
            b += self.payload.encode().ljust(FILENAME_LEN, b"\0")
        else:
            b += b"\0" * 32
        return b

    @classmethod
    def deserialize(cls, data: bytes) -> "Request":
        if len(data) != (1 + FILENAME_LEN):
            raise ValueError(
                f"Incorrect data size have:{len(data)} must {1 + FILENAME_LEN}"
            )
        cmd: Commands = Commands(data[0])
        payload_bytes = data[1 : 1 + FILENAME_LEN]
        payload_str = payload_bytes.rstrip(b"\0").decode()
        return cls(cmd, payload_str if payload_str else None)


Filepath = str
FILEPATH: Filepath = os.path.join("src", "server", "server_files")
Filename = str


class Filenames:
    arr: array

    def __init__(self, filenames: list[str]):
        arr_bytes = array("B")
        for name in filenames:
            name_bytes = name.encode("utf-8")
            if len(name_bytes) > 65535:
                raise ValueError("Filename too long (>65535 bytes)")
            # 2 байта длина + сами байты
            arr_bytes.frombytes(struct.pack("!H", len(name_bytes)))
            arr_bytes.frombytes(name_bytes)

        # проверка на максимальный payload размер
        if len(arr_bytes) > 2**ResponseHeader.MAX_PAYLOAD_LENGHT_BYTES - 1:
            raise ValueError(
                f"Too much filenames: max {2**ResponseHeader.MAX_PAYLOAD_LENGHT_BYTES - 1} bytes, got {len(arr_bytes)} bytes"
            )

        self.arr = arr_bytes

    def serialize(self) -> bytes:
        """Получить payload для отправки по сети"""
        return self.arr.tobytes()

    @classmethod
    def deserialize(cls, data: bytes) -> "Filenames":
        """Преобразовать байты обратно в список строк"""
        arr_bytes = array("B")
        arr_bytes.frombytes(data)

        filenames = []
        i = 0
        while i < len(arr_bytes):
            # читаем 2 байта длину строки
            name_len = struct.unpack("!H", arr_bytes[i : i + 2].tobytes())[0]
            i += 2
            # читаем байты строки
            name_bytes = arr_bytes[i : i + name_len].tobytes()
            i += name_len
            filenames.append(name_bytes.decode("utf-8"))

        return cls(filenames)

    def get_list(self) -> list[str]:
        """Вернуть оригинальный список файлов"""
        filenames = []
        i = 0
        while i < len(self.arr):
            name_len = struct.unpack("!H", self.arr[i : i + 2].tobytes())[0]
            i += 2
            name_bytes = self.arr[i : i + name_len].tobytes()
            i += name_len
            filenames.append(name_bytes.decode("utf-8"))
        return filenames

    def __len__(self):
        return len(self.arr)

    def __repr__(self):
        return f"Filenames(list={self.get_list()})"
