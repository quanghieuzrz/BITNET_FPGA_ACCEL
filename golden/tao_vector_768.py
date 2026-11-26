"""B2. Bộ vector 768 x 768: CÙNG kích thước bài toán TernaryCore công bố (Tier 1, phép chiếu 768 -> 768),
để so sánh công bằng trên cùng bo Arty A7-100T.

768 / 4 = 192 (v1 vừa khít), 768 / 6 = 128 (v2a vừa khít), 768 / 5 = 153,6 -> v1b, v2b phải đệm 2 hàng (kiểm tra A1).

Cách chạy (đứng ở thư mục golden/):
    python3 tao_vector_768.py
Tạo ra trong ../vectors/:
    t768_v1/, t768_v1b/      W dày đặc (khoảng 1/3 mỗi giá trị, giống phân bố BitNet)
    t768_v2a/, t768_v2a_v1/  W đúng 2:4, đóng gói v2a và v1 (Y phải giống hệt)
    t768_v2b/                W tối đa 2:4
S chọn theo cách E (an toàn) từ chính Acc của bộ dữ liệu.
"""
import argparse
import filecmp
import os
import random

from bitnet_golden.bo_vector import ghi_bo_vector
from bitnet_golden.chuan_hoa import chon_S_an_toan
from bitnet_golden.tham_chieu import tinh_acc_thang
from bitnet_golden.thanh_ghi import so_beat_vao
from tao_vector_v2 import nhom_dung_2, nhom_toi_da_2, tao_W

GOC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "vectors")


def main():
    p = argparse.ArgumentParser(description="Bộ vector 768 x 768 (mốc so sánh TernaryCore)")
    p.add_argument("--seed", type=int, default=768)
    a = p.parse_args()
    rng = random.Random(a.seed)
    K = N = 768
    X = [rng.randint(-127, 127) for _ in range(K)]
    W_day = [[rng.choice([-1, 0, 1]) for _ in range(K)] for _ in range(N)]
    W_2a = tao_W(K, N, rng, nhom_dung_2)
    W_2b = tao_W(K, N, rng, nhom_toi_da_2)

    cac_bo = [("t768_v1", W_day, "v1"), ("t768_v1b", W_day, "v1b"),
              ("t768_v2a", W_2a, "v2a"), ("t768_v2a_v1", W_2a, "v1"), ("t768_v2b", W_2b, "v2b")]
    for ten, W, pb in cac_bo:
        S = chon_S_an_toan(tinh_acc_thang(W, X))
        ghi_bo_vector(os.path.join(GOC, ten), X, W, S, pb, f"768x768 mốc TernaryCore, {pb}")
        print(f"{ten:<12} {pb:<4} S = {S:>2}  beat vào = {so_beat_vao(K, N, pb):>5}")
    giong = filecmp.cmp(os.path.join(GOC, "t768_v2a", "y_out.hex"),
                        os.path.join(GOC, "t768_v2a_v1", "y_out.hex"), shallow=False)
    print("Y của v2a và v1 (cùng W) giống hệt:", giong)
    assert giong


if __name__ == "__main__":
    main()
