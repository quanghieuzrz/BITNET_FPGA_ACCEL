"""Tạo bộ vector kiểm thử v1 NGẪU NHIÊN cho RTL.

Cách chạy (đứng ở thư mục golden/):
    python3 tao_vector_v1.py                              # mặc định
    python3 tao_vector_v1.py --K 2560 --so-hang 64 --S 8 --seed 7

Kết quả nằm trong ../vectors/<ten>/:
    x_in.hex, w_in.hex, y_expected.hex, config.txt
"""
import argparse
import os
import random

from bitnet_golden.bo_vector import ghi_bo_vector_v1


def tao_du_lieu(K, so_hang, seed):
    rng = random.Random(seed)
    X = [rng.randint(-127, 127) for _ in range(K)]
    W = [[rng.choice([-1, 0, 1]) for _ in range(K)] for _ in range(so_hang)]
    return X, W


def main():
    p = argparse.ArgumentParser(description="Tạo vector kiểm thử v1 ngẫu nhiên")
    p.add_argument("--K", type=int, default=128, help="độ dài X (chia hết cho 64)")
    p.add_argument("--so-hang", type=int, default=8, help="số hàng W (chia hết cho 4)")
    p.add_argument("--S", type=int, default=6, help="số bit dịch khi chuẩn hoá")
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--ten", default="v1_mac_dinh", help="tên thư mục con trong vectors/")
    a = p.parse_args()

    X, W = tao_du_lieu(a.K, a.so_hang, a.seed)
    thu_muc = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "vectors", a.ten)
    Y = ghi_bo_vector_v1(thu_muc, X, W, a.S, ghi_chu=f"ngau nhien, seed={a.seed}")
    print(f"Đã ghi vectors/{a.ten}/: K={a.K}, {a.so_hang} hàng, {len(Y)} số Y")


if __name__ == "__main__":
    main()
