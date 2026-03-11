from typing import TypeAlias, Annotated, Optional
from src.models.common import Commands

FILENAME_LEN_REQUEST: int = 32
Filename: TypeAlias = Annotated[str, FILENAME_LEN_REQUEST]


REQUEST_BYTES_SIZE = 1 + FILENAME_LEN_REQUEST


class Request:
    cmd: Commands
    payload: Optional[Filename]

    def __init__(self, cmd: Commands, payload: Optional[Filename]):
        self.cmd = cmd
        if payload is not None and (
            len(payload) > FILENAME_LEN_REQUEST or len(payload) < 0
        ):
            raise ValueError("Bad payload size")
        self.payload = payload

    def __repr__(self) -> str:
        return f"Request(cmd={self.cmd.name}, payload={self.payload})"

    def serialize(self) -> bytes:
        b: bytes = self.cmd.serialize()
        if self.payload is not None:
            b += self.payload.encode().ljust(FILENAME_LEN_REQUEST, b"\0")
        else:
            b += b"\0" * FILENAME_LEN_REQUEST
        return b

    @classmethod
    def deserialize(cls, data: bytes) -> "Request":
        if len(data) != (1 + FILENAME_LEN_REQUEST):
            raise ValueError(
                f"Incorrect data size have:{len(data)} must {1 + FILENAME_LEN_REQUEST}"
            )
        cmd: Commands = Commands(data[0])
        payload_bytes = data[1 : 1 + FILENAME_LEN_REQUEST]
        payload_str = payload_bytes.rstrip(b"\0").decode()
        return cls(cmd, payload_str if payload_str else None)
