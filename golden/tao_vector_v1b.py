"""Tạo vector v1b (kiểu TQ1_0, 5 trọng số / byte) và vector v1 ĐỐI CHIẾU (cùng X, W, S).

Cách chạy (đứng ở thư mục golden/):
    python3 tao_vector_v1b.py
    python3 tao_vector_v1b.py --K 2560 --so-hang 40 --S 8 --seed 4

Số hàng mặc định 20 = bội chung của 4 (v1) và 5 (v1b).
W ngẫu nhiên thường (không cần 2:4): v1b dùng được mọi mô hình BitNet.

Tạo ra trong ../vectors/:
    v1b_mac_dinh/      đóng gói v1b
    v1b_doi_chieu_v1/  CÙNG X, W, S, đóng gói v1 -> y_expected.hex phải giống hệt
"""
import argparse
import filecmp
import os
import random

from bitnet_golden.bo_vector import ghi_bo_vector, ma_hoa_luong

GOC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "vectors")


def main():
    p = argparse.ArgumentParser(description="Tạo vector v1b và v1 đối chiếu")
    p.add_argument("--K", type=int, default=128)
    p.add_argument("--so-hang", type=int, default=20)
    p.add_argument("--S", type=int, default=6)
    p.add_argument("--seed", type=int, default=3)
    a = p.parse_args()

    rng = random.Random(a.seed)
    X = [rng.randint(-127, 127) for _ in range(a.K)]
    W = [[rng.choice([-1, 0, 1]) for _ in range(a.K)] for _ in range(a.so_hang)]

    tm_v1b = os.path.join(GOC, "v1b_mac_dinh")
    tm_v1 = os.path.join(GOC, "v1b_doi_chieu_v1")
    ghi_bo_vector(tm_v1b, X, W, a.S, "v1b", f"seed={a.seed}")
    ghi_bo_vector(tm_v1, X, W, a.S, "v1", f"doi chieu cua v1b, seed={a.seed}")
    cung_y = filecmp.cmp(os.path.join(tm_v1b, "y_expected.hex"),
                         os.path.join(tm_v1, "y_expected.hex"), shallow=False)
    n_v1b = len(ma_hoa_luong(X, W, "v1b")[1])
    n_v1 = len(ma_hoa_luong(X, W, "v1")[1])
    print(f"v1b: {n_v1b} beat W (so với v1: {n_v1} beat, gọn hơn {n_v1 / n_v1b:.2f} lần) | Y giống v1: {cung_y}")
    assert cung_y


if __name__ == "__main__":
    main()
