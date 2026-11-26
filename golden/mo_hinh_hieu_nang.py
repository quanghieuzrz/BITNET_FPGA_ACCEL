"""B1. Mô hình hiệu năng: dự đoán số nhịp mỗi lớp BitLinear và số token/giây, cho cả 4 phiên bản.

Công thức (một token, một lớp K -> N):
    beat_X  = K / 64
    beat_W  = ceil(N / R) * K / 64                       (R = số hàng / beat, đã tính hàng đệm)
    nhịp_W  = max( beat_W ,  beat_W * 64 byte / (băng thông / tần số) )
    nhịp    = beat_X + nhịp_W + TRE_DUOI                 (TRE_DUOI: vài nhịp xả pipeline + chuẩn hoá)

Tức là: nếu RAM cấp đủ 64 byte/nhịp thì chip bị giới hạn bởi TÍNH TOÁN (1 beat W / nhịp);
nếu không, chip bị giới hạn bởi BĂNG THÔNG (chờ trọng số) — đây là kết luận chung của PENSA và TernaryCore.
Giả định X nạp từ BRAM/bộ nhớ trên chip nên không tốn băng thông DDR đáng kể (K byte so với hàng MB W).

Cách chạy (đứng ở thư mục golden/):
    python3 mo_hinh_hieu_nang.py
    python3 mo_hinh_hieu_nang.py --tan-so 100 --kiem-tra       # đối chiếu với mô hình giao dịch
"""
import argparse
import math
import random

from bitnet_golden.hang_so import SO_LAN, KHUC
from bitnet_golden.dem_hang import so_nhom_hang, so_hang_dem

TRE_DUOI = 1          # nhịp xả cuối lớp (ngoài T nhịp của beat W cuối); cập nhật lại sau khi đo trên RTL

# Bảy phép chiếu BitLinear trong 1 khối của BitNet b1.58 2B4T (K -> N), 30 khối
LOP_2B4T = [("Q", 2560, 2560), ("K", 2560, 640), ("V", 2560, 640), ("O", 2560, 2560),
            ("Gate", 2560, 6912), ("Up", 2560, 6912), ("Down", 6912, 2560)]
SO_KHOI = 30

# Băng thông bộ nhớ ngoài (GB/s)
KICH_BAN_BW = [
    ("Lý tưởng: bus 512 bit đầy", 6.4),
    ("DDR3L Arty A7, đỉnh (16 bit x 667 Mb/s)", 1.333),
    ("DDR3L Arty A7, thực tế ~75%", 1.0),
]
BIT_MOI_TRONG_SO = {"v1": 2.0, "v1b": 1.6, "v2b": 1.5, "v2a": 1.25}
CAC_PB = ["v1", "v1b", "v2b", "v2a"]


def nhip_mot_lop(K, N, pb, bw_gbs=None, f_mhz=100, T=1):
    """Số nhịp cho MỘT lượt: T token cùng dùng chung luồng W (T = 1: bình thường)."""
    R = SO_LAN[pb]
    beat_x = T * (K // KHUC)
    beat_w = so_nhom_hang(N, R) * (K // KHUC)
    nhip_tinh = T * beat_w                      # mỗi beat W dùng T nhịp
    if bw_gbs is None:
        nhip_w = nhip_tinh
    else:
        byte_moi_nhip = bw_gbs * 1e9 / (f_mhz * 1e6)
        nhip_w = max(nhip_tinh, math.ceil(beat_w * 64 / byte_moi_nhip))
    return beat_x + nhip_w + T + TRE_DUOI


def nhip_mot_token(pb, bw_gbs=None, f_mhz=100, T=1):
    """Số nhịp TRUNG BÌNH cho một token (cả mô hình)."""
    return SO_KHOI * sum(nhip_mot_lop(K, N, pb, bw_gbs, f_mhz, T) for _, K, N in LOP_2B4T) / T


def T_vua_du(bw_gbs, f_mhz=100):
    """T nhỏ nhất để làn không còn ngồi chờ RAM = làm tròn lên (64 byte / byte mỗi nhịp)."""
    return math.ceil(64 / (bw_gbs * 1e9 / (f_mhz * 1e6)))


def lang_phi_dem(pb):
    """% beat W tốn cho hàng đệm trên toàn mô hình."""
    R = SO_LAN[pb]
    that = sum(N * K for _, K, N in LOP_2B4T)
    dem = sum(so_hang_dem(N, R) * K for _, K, N in LOP_2B4T)
    return 100 * dem / (that + dem)


def kiem_tra_voi_mo_hinh_giao_dich():
    """Đối chiếu công thức (băng thông lý tưởng) với mô hình theo nhịp trên lớp nhỏ."""
    from bitnet_golden.mo_hinh_giao_dich import chay
    from bitnet_golden.dem_hang import dem_hang
    rng = random.Random(3)
    K, N = 256, 50
    X = [rng.randint(-127, 127) for _ in range(K)]
    for pb in CAC_PB:
        W = [[rng.choice([-1, 1, 0, 0]) if pb in ("v1", "v1b") else 0 for _ in range(K)] for _ in range(N)]
        if pb.startswith("v2"):
            W = [[+1, -1, 0, 0] * (K // 4) for _ in range(N)]
        _, nhip_gd, _ = chay(X, dem_hang(W, pb), N, 6, pb)
        nhip_ct = nhip_mot_lop(K, N, pb)
        print(f"  {pb:<4} công thức {nhip_ct:>5} nhịp | mô hình giao dịch {nhip_gd:>5} nhịp")


def main():
    p = argparse.ArgumentParser(description="Mô hình hiệu năng BitLinear trên FPGA")
    p.add_argument("--tan-so", type=float, default=100, help="MHz")
    p.add_argument("--kiem-tra", action="store_true")
    a = p.parse_args()
    f = a.tan_so

    print(f"Tần số {f:g} MHz, BitNet b1.58 2B4T ({SO_KHOI} khối x 7 lớp BitLinear), 1 token\n")
    print("1) Số nhịp từng lớp khi băng thông lý tưởng (giới hạn bởi tính toán)")
    print(f"{'Lớp':<6}{'K':>6}{'N':>6} | " + " | ".join(f"{pb:>8}" for pb in CAC_PB))
    for ten, K, N in LOP_2B4T:
        print(f"{ten:<6}{K:>6}{N:>6} | " + " | ".join(f"{nhip_mot_lop(K, N, pb, None, f):>8}" for pb in CAC_PB))

    print("\n2) Hàng đệm (A1) tốn bao nhiêu beat W")
    for pb in CAC_PB:
        print(f"  {pb:<4} R = {SO_LAN[pb]}: lãng phí {lang_phi_dem(pb):.3f}%")

    print("\n3) Token/giây theo băng thông bộ nhớ ngoài")
    print(f"{"Kịch bản":<52}" + "".join(f"{pb:>8}" for pb in CAC_PB))
    print(f"{'Giới hạn tính toán (không chờ RAM)':<52}" +
          "".join(f"{f * 1e6 / nhip_mot_token(pb, None, f):>8.2f}" for pb in CAC_PB))
    for ten, bw in KICH_BAN_BW:
        print(f"{ten + f' ({bw} GB/s)':<52}" +
              "".join(f"{f * 1e6 / nhip_mot_token(pb, bw, f):>8.2f}" for pb in CAC_PB))

    can = 64 * f * 1e6 / 1e9
    print(f"\n4) Băng thông cần để KHÔNG bị chờ RAM: 64 byte/nhịp x {f:g} MHz = {can:.1f} GB/s")
    tong_w = sum(K * N for _, K, N in LOP_2B4T) * SO_KHOI
    for pb in CAC_PB:
        mb = tong_w * BIT_MOI_TRONG_SO[pb] / 8 / 2**20
        print(f"  {pb:<4} trọng số mỗi token: {mb:7.0f} MB  (Arty A7 chỉ có 256 MB DDR3L)")

    print("\n5) Dùng chung beat W cho T token (prefill / encoder / batch) - THÔNG LƯỢNG tok/s, DDR3L đỉnh 1.333 GB/s")
    bw = 1.333
    print(f"   T vừa đủ để hết chờ RAM: {T_vua_du(bw, f)}  (với 1.0 GB/s: {T_vua_du(1.0, f)})")
    print(f"{'T':<6}" + "".join(f"{pb:>8}" for pb in CAC_PB) + "   BRAM cho X (lớp Down, K = 6912)")
    for T in (1, 2, 4, 5, 8):
        print(f"{T:<6}" + "".join(f"{f * 1e6 / nhip_mot_token(pb, bw, f, T):>8.2f}" for pb in CAC_PB)
              + f"   {T * 6912 / 1024:6.1f} KB")
    print("   Lưu ý: decode của MỘT người dùng vẫn là T = 1 (mỗi lúc chỉ có 1 token mới).")

    if a.kiem_tra:
        print("\n6) Đối chiếu công thức với mô hình giao dịch (K = 256, N = 50)")
        kiem_tra_voi_mo_hinh_giao_dich()


if __name__ == "__main__":
    main()
