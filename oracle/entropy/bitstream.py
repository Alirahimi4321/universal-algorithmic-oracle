"""Bitstream generation from entropy sources."""
import struct
from .hashing import hash_text, hash_combined


def text_to_bitstream(text: str) -> list[int]:
    bits = []
    for byte in text.encode("utf-8"):
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)
    return bits


def int_to_bitstream(value: int, length: int = 32) -> list[int]:
    bits = []
    for i in range(length - 1, -1, -1):
        bits.append((value >> i) & 1)
    return bits


def hash_to_bitstream(data: str, length: int = 256) -> list[int]:
    digest = hash_text(data)
    bits = []
    for byte in digest:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)
    return bits[:length]


def generate_pseudo_random_bitstream(seed: int, length: int = 256) -> list[int]:
    stream = []
    current = seed
    for _ in range(length):
        current = (current * 1103515245 + 12345) & 0x7FFFFFFF
        stream.append(current % 2)
    return stream


def bitstream_to_ints(bits: list[int], chunk_size: int = 8) -> list[int]:
    result = []
    for i in range(0, len(bits), chunk_size):
        chunk = bits[i : i + chunk_size]
        val = 0
        for b in chunk:
            val = (val << 1) | b
        result.append(val)
    return result


def generate_bitstream(data: str, length: int = 256) -> list[int]:
    """Generate a bitstream from string data."""
    bits = []
    for byte in data.encode("utf-8"):
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)
    return bits[:length]
