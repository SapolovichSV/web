import os


def is_file_existing(filepath: str) -> bool:
    return os.path.exists(filepath)


def read_file(filepath: str) -> bytes:
    if not os.path.exists(filepath):
        raise IOError(f"No such filepath:{filepath}")
        return bytes()

    if os.path.getsize(filepath) <= 0:
        raise ValueError(f"Too small file with filepath{filepath}")
        return bytes()

    if os.path.getsize(filepath) > 2**32 - 1:
        raise ValueError(f"Too big file with filepath{filepath}")
        return bytes()

    with open(filepath, "rb") as file:
        return file.read()


def write_file(path: str, data: bytes) -> None:

    with open(path, "wb") as f:
        written: int = f.write(data)
        print(f"wrote {written} bytes")
        f.flush()

    if len(data) != written:
        raise IOError("len of input bytes != len of written bytes")
