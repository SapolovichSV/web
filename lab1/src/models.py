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
# 4 Bytes header
class Response:
    """
    4-байтовый заголовок пакета:

    Byte 0      → code (NetCode, 1 byte)
    Byte 1      → payload_type (PayloadType, 1 byte)
    Bytes 2-3   → payload length (unsigned short, 2 bytes)
    Bytes 4..N  → payload (payload_len bytes)

    Attributes:
        code (NetCode): Код ответа
        payload_type (PayloadType): Тип payload
        payload (bytes): Сами данные
    В случае методов UPLOAD и DOWNLOAD мы должны сначала отправить response с
    типом PayloadType.Payload_LEN
    где в payloade укажем длину файла
    потом отправить респонс с самим файлом, уже зная его размер
    """

    code: NetCode
    payload_type: PayloadType
    payload: bytes

    FORMAT_STRING: str = "!B B H"

    def __init__(
        self, code: NetCode, payload_type: PayloadType, payload: bytes = b""
    ) -> None:
        self.code = code
        self.payload_type = payload_type
        self.payload = payload

    def serialize(self) -> bytes:
        length = len(self.payload)
        return (
            struct.pack(
                Response.FORMAT_STRING, self.code.value, self.payload_type.value, length
            )
            + self.payload
        )

    @classmethod
    def deserialize(cls, val: bytes) -> "Response":
        """
        Десериализация:
        - val: байты, содержащие код, payload_type, длину и payload
        """
        if len(val) < 4:
            raise ValueError("Data too short to deserialize Response")

        code_val, payload_type_val, length = struct.unpack(
            Response.FORMAT_STRING, val[:4]
        )
        payload = val[4 : 4 + length]

        try:
            code = NetCode(code_val)
        except ValueError:
            raise ValueError(f"Invalid NetCode: {code_val}")

        try:
            payload_type = PayloadType(payload_type_val)
        except ValueError:
            raise ValueError(f"Invalid PayloadType: {payload_type_val}")

        # Если payload_type == PAYLOAD_LEN, payload содержит просто длину следующего payload
        # Сервер/клиент должен отдельно обработать этот случай
        return cls(code, payload_type, payload)


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
