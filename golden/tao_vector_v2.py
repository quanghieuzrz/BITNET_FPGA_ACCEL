"""Bước 8: tạo vector v2a, v2b và vector v1 ĐỐI CHIẾU (cùng X, W, S).

Cách chạy (đứng ở thư mục golden/):
    python3 tao_vector_v2.py
    python3 tao_vector_v2.py --K 2560 --so-hang 120 --S 8 --seed 3

Số hàng mặc định 60 = bội chung của 4 (v1), 5 (v2b), 6 (v2a).

Tạo ra trong ../vectors/:
    v2a_mac_dinh/      W đúng 2:4 (đúng 2 phần tử khác 0 / nhóm), đóng gói v2a
    v2a_doi_chieu_v1/  CÙNG W đó, đóng gói v1  -> y_expected.hex phải giống hệt
    v2b_mac_dinh/      W tối đa 2:4 (0, 1 hoặc 2 phần tử khác 0 / nhóm), đóng gói v2b
    v2b_doi_chieu_v1/  CÙNG W đó, đóng gói v1  -> y_expected.hex phải giống hệt
"""
import argparse
import filecmp
import os
import random

from bitnet_golden.hang_so import NHOM
from bitnet_golden.bo_vector import ghi_bo_vector, ma_hoa_luong

GOC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "vectors")


def nhom_dung_2(rng):
    """Một nhóm 4 trọng số có ĐÚNG 2 phần tử khác 0 (cho v2a)."""
    nhom = [0] * NHOM
    for p in rng.sample(range(NHOM), 2):
        nhom[p] = rng.choice([-1, +1])
    return nhom


def nhom_toi_da_2(rng):
    """Một nhóm 4 trọng số có 0, 1 hoặc 2 phần tử khác 0 (cho v2b)."""
    so_khac_0 = rng.choices([0, 1, 2], weights=[1, 3, 6])[0]
    nhom = [0] * NHOM
    for p in rng.sample(range(NHOM), so_khac_0):
        nhom[p] = rng.choice([-1, +1])
    return nhom


def tao_W(K, so_hang, rng, ham_nhom):
    return [sum((ham_nhom(rng) for _ in range(K // NHOM)), []) for _ in range(so_hang)]


def main():
    p = argparse.ArgumentParser(description="Tạo vector v2a, v2b và v1 đối chiếu")
    p.add_argument("--K", type=int, default=128)
    p.add_argument("--so-hang", type=int, default=60)
    p.add_argument("--S", type=int, default=6)
    p.add_argument("--seed", type=int, default=2)
    a = p.parse_args()

    rng = random.Random(a.seed)
    X = [rng.randint(-127, 127) for _ in range(a.K)]
    W_2a = tao_W(a.K, a.so_hang, rng, nhom_dung_2)
    W_2b = tao_W(a.K, a.so_hang, rng, nhom_toi_da_2)

    for ten, W, pb in [("v2a", W_2a, "v2a"), ("v2b", W_2b, "v2b")]:
        tm_v2 = os.path.join(GOC, f"{ten}_mac_dinh")
        tm_v1 = os.path.join(GOC, f"{ten}_doi_chieu_v1")
        ghi_bo_vector(tm_v2, X, W, a.S, pb, f"seed={a.seed}")
        ghi_bo_vector(tm_v1, X, W, a.S, "v1", f"doi chieu cua {ten}, seed={a.seed}")
        cung_y = filecmp.cmp(os.path.join(tm_v2, "y_expected.hex"),
                             os.path.join(tm_v1, "y_expected.hex"), shallow=False)
        so_beat_v2 = len(ma_hoa_luong(X, W, pb)[1])
        so_beat_v1 = len(ma_hoa_luong(X, W, "v1")[1])
        print(f"{ten}: {so_beat_v2} beat W (so với v1: {so_beat_v1} beat, "
              f"gọn hơn {so_beat_v1 / so_beat_v2:.2f} lần) | Y giống v1: {cung_y}")
        assert cung_y


if __name__ == "__main__":
    main()
