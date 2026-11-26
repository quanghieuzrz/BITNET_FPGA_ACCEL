"""So sánh 4 cách đóng gói W trên CÙNG một bộ X, W, S.

W được tạo theo luật "đúng 2 phần tử khác 0 mỗi nhóm 4" để cả 4 phiên bản đều đóng gói được.
Số hàng 60 = bội chung của 4 (v1), 5 (v1b, v2b), 6 (v2a).

Cách chạy (đứng ở thư mục golden/):
    python3 so_sanh_phien_ban.py
    python3 so_sanh_phien_ban.py --K 2560 --so-hang 120
"""
import argparse
import random

from bitnet_golden.bo_vector import PHIEN_BAN, ma_hoa_luong
from bitnet_golden.tham_chieu import tinh_y_thang, tinh_y_theo_chip
from tao_vector_v2 import tao_W, nhom_dung_2

BIT_MOI_TRONG_SO = {"v1": 2.0, "v1b": 1.6, "v2b": 1.5, "v2a": 1.25}
CAN_MO_HINH_24 = {"v1": "không", "v1b": "không", "v2b": "tối đa 2:4", "v2a": "đúng 2:4"}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--K", type=int, default=128)
    p.add_argument("--so-hang", type=int, default=60)
    p.add_argument("--S", type=int, default=6)
    p.add_argument("--seed", type=int, default=7)
    a = p.parse_args()

    rng = random.Random(a.seed)
    X = [rng.randint(-127, 127) for _ in range(a.K)]
    W = tao_W(a.K, a.so_hang, rng, nhom_dung_2)
    y = tinh_y_thang(W, X, a.S)

    print(f"K = {a.K}, {a.so_hang} hàng W")
    print(f"{'Phiên bản':<10} {'bit/TS':>7} {'hàng/beat':>10} {'beat W':>7} {'so v1':>6} {'Y giống':>8}  cần mô hình")
    print("-" * 72)
    so_beat_v1 = None
    for pb in ["v1", "v1b", "v2b", "v2a"]:
        so_lan, _ = PHIEN_BAN[pb]
        so_beat = len(ma_hoa_luong(X, W, pb)[1])
        so_beat_v1 = so_beat_v1 or so_beat
        giong = tinh_y_theo_chip(W, X, a.S, so_lan) == y
        print(f"{pb:<10} {BIT_MOI_TRONG_SO[pb]:>7} {so_lan:>10} {so_beat:>7} "
              f"{so_beat_v1 / so_beat:>5.2f}x {str(giong):>8}  {CAN_MO_HINH_24[pb]}")


if __name__ == "__main__":
    main()
