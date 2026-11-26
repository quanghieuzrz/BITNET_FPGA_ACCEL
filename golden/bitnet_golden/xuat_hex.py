"""Ghi file .hex theo định dạng $readmemh của Verilog.

Mỗi dòng một beat 512 bit = 128 ký tự hex, ký tự đầu tiên bên trái là bit 511..508.
"""
from .hang_so import BEAT_BIT


def beat_sang_hex(beat):
    return f"{beat:0{BEAT_BIT // 4}X}"


def ghi_cac_beat(duong_dan, cac_beat):
    with open(duong_dan, "w", encoding="utf-8") as f:
        for beat in cac_beat:
            f.write(beat_sang_hex(beat) + "\n")


def ghi_int8(duong_dan, cac_so):
    """Mỗi dòng một số INT8, 2 ký tự hex (bù hai)."""
    with open(duong_dan, "w", encoding="utf-8") as f:
        for y in cac_so:
            f.write(f"{y & 0xFF:02X}\n")
