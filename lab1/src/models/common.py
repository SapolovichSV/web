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
