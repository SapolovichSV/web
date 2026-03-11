import struct
from enum import Enum

class PayloadType(Enum):
    NONE = 0
    FILE = 1
    LIST = 2
    PAYLOAD_LEN = 3


class NetCode(Enum):
    OK = 0
    ERROR = 1

RESPONSE_BASE_SIZE_BYTES = 6
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
class Filenames:
    """
    2^26 максимальное кол-во файлов
    32 байта максимальное длина названия одного файла
    """
    filenames_count: int
    filenames: list[str]
    MAX_FILENAME_LENGHT = 32
    SEPARATOR = b"\x00"

    def __init__(self,filenames:list[str]) -> None:
        self.filenames_count  = len(filenames)
        if len(filenames) > (2**32 - 1):
            raise ValueError("Too much files")
        for name in filenames:
            if len(name) > 32:
                raise ValueError(f"File {name} have too big name")
        self.filenames = filenames
    def __repr__(self) -> str:
        return f"Filenames with lenght:{self.filenames_count}\n\tcontent:{self.filenames}"

    def serialize(self) -> bytes:
        data:bytearray = bytearray()
        data += struct.pack("!I",self.filenames_count)

        for name in self.filenames:
            encoded:bytes = name.encode()
            encoded = encoded.ljust(self.MAX_FILENAME_LENGHT,self.SEPARATOR)
            data += encoded
        return bytes(data)
    @classmethod
    def deserialize(cls,data:bytes) -> "Filenames":
        count:int = struct.unpack_from("!I",data)[0]

        offset:int = 4
        filenames:list[str] = []
        for _ in range(count):
            chunk:bytes = data[offset:offset + cls.MAX_FILENAME_LENGHT]
            offset += cls.MAX_FILENAME_LENGHT

            name:str = chunk.rstrip(cls.SEPARATOR).decode()
            filenames.append(name)
        if count != len(filenames):
            raise ValueError(f"predicted count of filenames:{count} doesnt match with having:{len(filenames)}")
        return cls(filenames)
