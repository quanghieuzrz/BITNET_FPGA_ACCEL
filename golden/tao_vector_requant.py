"""Tạo vector kiểm thử riêng cho khối chuẩn hoá (rtl/requant.v).

Mỗi dòng của file là MỘT phép thử, 40 bit = 10 ký tự hex, gồm 3 trường (từ trái sang phải):
    bit [39:16]  Acc   24 bit có dấu (bù hai)
    bit [15:8]   S     8 bit (chỉ dùng 5 bit thấp, 1..23)
    bit [7:0]    Y     8 bit có dấu: đáp án từ golden model

Cách chạy (đứng ở thư mục golden/):
    python3 tao_vector_requant.py          -> ../vectors/requant/requant_vectors.hex
"""
import os
import random

from bitnet_golden.hang_so import ACC_BIT
from bitnet_golden.chuan_hoa import chuan_hoa

GOC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "vectors", "requant")


def dong_hex(acc, S, y):
    acc_u = acc & ((1 << ACC_BIT) - 1)          # Acc 24 bit bù hai
    return f"{acc_u:06X}{S:02X}{y & 0xFF:02X}"


def main():
    ca_thu = [
        # các ví dụ đã học ở bước 2 và bộ test biên
        (1000, 4), (-1000, 4), (5000, 4), (-5000, 4), (8, 4), (-233, 6), (0, 4),
        (24, 4), (40, 4), (2, 2), (-2, 2), (6, 2), (-6, 2),              # mốc .5
        (254, 1), (256, 1), (-254, 1), (-256, 1), (255, 1), (-255, 1),   # mốc kẹp
        (877824, 6), (-877824, 6), (877824, 13), (-877824, 13),          # Acc lớn nhất
        ((1 << 23) - 1, 1), (-(1 << 23), 1), ((1 << 23) - 1, 23), (-(1 << 23), 23),  # biên 24 bit
        (-1, 1), (1, 1), (-1, 23), (1, 23),
    ]
    rng = random.Random(11)
    for _ in range(2000):
        ca_thu.append((rng.randint(-(1 << 23), (1 << 23) - 1), rng.randint(1, 23)))
    for _ in range(1000):                                               # Acc cỡ thường gặp
        ca_thu.append((rng.randint(-20000, 20000), rng.randint(1, 10)))

    os.makedirs(GOC, exist_ok=True)
    with open(os.path.join(GOC, "requant_vectors.hex"), "w", encoding="utf-8") as f:
        for acc, S in ca_thu:
            f.write(dong_hex(acc, S, chuan_hoa(acc, S)) + "\n")
    print(f"Đã ghi vectors/requant/requant_vectors.hex: {len(ca_thu)} phép thử")


if __name__ == "__main__":
    main()
