"""
MIT License

Copyright (c) 2025 Mosquito

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import io
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import IO, Iterator, Union


class ARFileError(Exception):
    pass


class EmptyHeaderError(ARFileError):
    pass


class TruncatedHeaderError(ARFileError):
    pass


class TruncatedDataError(ARFileError):
    pass


@dataclass
class ArFile:
    name: str
    size: int
    content: bytes

    uid: int = 0
    gid: int = 0
    mode: int = 0o100644
    mtime: int = field(default_factory=lambda: int(time.time()))

    @classmethod
    def from_file(cls, path: Union[str, Path], arcname: str = "") -> "ArFile":
        path = Path(path)
        name = str(arcname) if arcname else str(path.name)
        stat = path.stat()
        size = stat.st_size
        mtime = int(stat.st_mtime)
        return cls(name=name, size=size, mtime=mtime, content=path.open("rb").read())

    @classmethod
    def from_bytes(cls, data: bytes, name: str, **kwargs) -> "ArFile":
        name = str(name)
        size = len(data)
        return cls(name=name, size=size, content=data, **kwargs)

    @classmethod
    def from_fp(cls, fp: IO[bytes], name: Union[str, Path], **kwargs) -> "ArFile":
        return cls.from_bytes(fp.read(), name, **kwargs)

    @classmethod
    def parse_from_fp(cls, fp: IO[bytes]) -> "ArFile":
        header_size = 60

        hdr = fp.read(header_size)

        if not hdr:
            raise EmptyHeaderError(f"Header is empty: {hdr!r}")

        if len(hdr) < header_size:
            raise TruncatedHeaderError(f"Expected {header_size} bytes, got {len(hdr)}")

        name = hdr[:16].decode("utf-8").rstrip(" ")
        mtime = int(hdr[16:28].decode("utf-8").strip())
        uid = int(hdr[28:34].decode("utf-8").strip())
        gid = int(hdr[34:40].decode("utf-8").strip())
        mode = int(hdr[40:48].decode("utf-8").strip(), 8)
        size = int(hdr[48:58].decode("utf-8").strip())

        data = fp.read(size)
        if len(data) < size:
            raise TruncatedDataError(f"Expected {size} bytes, got {len(data)}")

        if size % 2 != 0:
            fp.read(1)

        return cls(name=name, size=size, mtime=mtime, content=data, uid=uid, gid=gid, mode=mode)

    @property
    def fp(self) -> IO[bytes]:
        return io.BytesIO(self.content)

    def dump(self) -> bytes:
        with io.BytesIO() as f:
            name = self.name.encode("utf-8")
            name = name[:16].ljust(16, b" ")

            mtime = str(self.mtime).encode("utf-8").ljust(12, b" ")
            uid = b"0".ljust(6, b" ")
            gid = b"0".ljust(6, b" ")
            mode = b"100644".ljust(8, b" ")
            size = str(self.size).encode("utf-8").ljust(10, b" ")

            f.write(name + mtime + uid + gid + mode + size + b"\x60\x0A")
            f.write(self.content)

            if self.size % 2 != 0:
                f.write(b"\n")
            return f.getvalue()


def pack_ar_archive(*files: ArFile) -> bytes:
    with io.BytesIO() as fp:
        fp.write(b"!<arch>\n")
        for ar_file in files:
            fp.write(ar_file.dump())
        return fp.getvalue()


def unpack_ar_archive(fp: IO[bytes]) -> Iterator[ArFile]:
    if fp.read(8) != b"!<arch>\n":
        raise ValueError("Invalid ar archive")

    while True:
        try:
            yield ArFile.parse_from_fp(fp)
        except (EmptyHeaderError, TruncatedHeaderError):
            return