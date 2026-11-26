"""Tạo vector kiểm thử cho rtl/w_decode_v1.v.

Mỗi dòng của vectors/w_decode_v1/w_decode_vectors.hex là MỘT số 1028 bit (257 ký tự hex):
    bit [511:0]     beat W vào
    bit [767:512]   khac_0 đáp án (256 bit)
    bit [1023:768]  am đáp án (256 bit)
    bit [1024]      loi_ma đáp án
    bit [1027:1025] = 0

Đáp án lấy từ BẢNG trong đặc tả (mục 3.1 + mục 8), không dùng công thức XOR/AND của RTL, để hai bên độc lập.
Nguồn beat:
    1. mọi beat W của các bộ vector v1 có sẵn trong vectors/ (PHIEN_BAN=v1)
    2. beat ngẫu nhiên hợp lệ (đối chiếu thêm với giai_ma_w_v1 của golden model)
    3. beat ngẫu nhiên có chen mã 11 ở vị trí ngẫu nhiên
    4. beat đặc biệt: toàn 00, toàn 01, toàn 10, toàn 11, xen kẽ, một mã 11 ở bit cao nhất / thấp nhất

Cách chạy (đứng ở thư mục golden/):  python3 tao_vector_w_decode.py
"""
import glob
import os
import random

from bitnet_golden.hang_so import LAN_V1, KHUC
from bitnet_golden.ma_hoa_w_v1 import giai_ma_w_v1

GOC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "vectors")
SO_TS = LAN_V1 * KHUC                                   # 256 trọng số / beat

# Bảng đặc tả: mã -> (khac_0, am, lỗi)
BANG = {0b00: (0, 0, 0), 0b01: (1, 0, 0), 0b10: (1, 1, 0), 0b11: (0, 0, 1)}


def dap_an(beat):
    khac_0 = am = loi = 0
    for i in range(SO_TS):
        k, a, l = BANG[(beat >> (2 * i)) & 0b11]
        khac_0 |= k << i
        am |= a << i
        loi |= l
    return khac_0, am, loi


def kiem_tra_cheo(beat, khac_0, am):
    """Với beat hợp lệ: khac_0/am phải khớp giá trị giai_ma_w_v1 của golden model."""
    hang = giai_ma_w_v1(beat)
    for i in range(SO_TS):
        w = hang[i // KHUC][i % KHUC]
        assert ((khac_0 >> i) & 1) == (w != 0) and ((am >> i) & 1) == (w == -1)


def beat_tu_ma(ham):
    return sum(ham(i) << (2 * i) for i in range(SO_TS))


def main():
    rng = random.Random(2026)
    cac_beat = []
    # 1. beat W v1 có sẵn
    for cfg in sorted(glob.glob(os.path.join(GOC, "*", "config.txt"))):
        if "PHIEN_BAN=v1\n" in open(cfg, encoding="utf-8").read():
            with open(os.path.join(os.path.dirname(cfg), "w_in.hex"), encoding="utf-8") as f:
                cac_beat += [int(d, 16) for d in f if d.strip()]
    so_co_san = len(cac_beat)
    cac_beat = cac_beat[:2000]
    # 2. ngẫu nhiên hợp lệ
    cac_beat += [beat_tu_ma(lambda i: rng.choice([0, 1, 2])) for _ in range(500)]
    # 3. ngẫu nhiên có mã 11
    for _ in range(300):
        b = beat_tu_ma(lambda i: rng.choice([0, 1, 2]))
        for p in rng.sample(range(SO_TS), rng.randint(1, 4)):
            b |= 0b11 << (2 * p)
        cac_beat.append(b)
    # 4. đặc biệt
    cac_beat += [beat_tu_ma(lambda i, m=m: m) for m in (0, 1, 2, 3)]
    cac_beat += [beat_tu_ma(lambda i: 1 if i % 2 else 2), beat_tu_ma(lambda i: (i % 3))]
    cac_beat += [0b11, 0b11 << (2 * (SO_TS - 1)), beat_tu_ma(lambda i: 2) | (0b11 << 254)]

    thu_muc = os.path.join(GOC, "w_decode_v1")
    os.makedirs(thu_muc, exist_ok=True)
    so_loi = 0
    with open(os.path.join(thu_muc, "w_decode_vectors.hex"), "w", encoding="utf-8") as f:
        for b in cac_beat:
            k, a, l = dap_an(b)
            if l == 0:
                kiem_tra_cheo(b, k, a)
            so_loi += l
            f.write(f"{(l << 1024) | (a << 768) | (k << 512) | b:0257X}\n")
    print(f"Đã ghi {len(cac_beat)} beat ({min(so_co_san, 2000)} từ bộ vector v1, {so_loi} beat có mã 11) "
          f"vào {os.path.relpath(thu_muc)}/w_decode_vectors.hex")


if __name__ == "__main__":
    main()
