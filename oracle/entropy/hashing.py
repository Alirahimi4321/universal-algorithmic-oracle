"""Hashing utilities for entropy generation."""
import hashlib
import struct
import time


def hash_text(text: str, algorithm: str = "sha256") -> bytes:
    h = hashlib.new(algorithm)
    h.update(text.encode("utf-8"))
    return h.digest()


def hash_combined(*args, algorithm: str = "sha256") -> bytes:
    h = hashlib.new(algorithm)
    for arg in args:
        if isinstance(arg, str):
            h.update(arg.encode("utf-8"))
        elif isinstance(arg, (int, float)):
            h.update(struct.pack("!d", arg))
        elif isinstance(arg, bytes):
            h.update(arg)
    return h.digest()


def hash_to_int(hash_bytes: bytes) -> int:
    return int.from_bytes(hash_bytes, byteorder="big")


def hash_to_range(hash_bytes: bytes, low: int, high: int) -> int:
    val = hash_to_int(hash_bytes)
    return low + (val % (high - low + 1))


def generate_seed(question: str, timestamp: float | None = None) -> int:
    if timestamp is None:
        timestamp = time.time()
    combined = f"{question}|{timestamp}"
    h = hash_text(combined)
    return hash_to_int(h)


def text_to_numeric_vector(text: str) -> list[int]:
    return [ord(c) for c in text]


def text_to_bitstream(text: str) -> list[int]:
    bits = []
    for byte in text.encode("utf-8"):
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)
    return bits


def hash_timestamp(timestamp: float) -> bytes:
    """Hash a timestamp value."""
    return hash_combined(str(timestamp))
