"""Ghi một bộ vector từ X, W, S cho trước.

Hỗ trợ bốn phiên bản đóng gói W: v1, v1b (kiểu TQ1_0), v2a, v2b. Đáp án Y KHÔNG phụ thuộc phiên bản
(cùng X, W, S thì cùng Y), chỉ cách đóng gói W và số hàng mỗi beat là khác.

Số hàng N KHÔNG cần chia hết cho R: hàng giả được đệm tự động (xem dem_hang.py), chip bỏ Y của hàng giả.

Các file ghi ra:
    x_in.hex        K/64 beat X
    w_in.hex        các beat W (đã đệm hàng)
    y_expected.hex  N số Y, mỗi dòng 1 số (để đọc bằng mắt)
    y_out.hex       các beat Y đúng như chip xuất ra bus (A2)
    tre_vao.hex     số nhịp trễ trước mỗi beat vào (A4)
    tre_ra.hex      số nhịp phía nhận chặn mỗi beat Y (A4)
    config.txt      tham số, gồm giá trị các thanh ghi điều khiển (A3)
"""
import os

from .hang_so import KHUC, SO_LAN, MA_CHE_DO
from .ma_hoa_x import ma_hoa_x
from .ma_hoa_y import dong_goi_y
from .ma_hoa_w_v1 import ma_hoa_w_v1
from .ma_hoa_w_v1b import ma_hoa_w_v1b
from .ma_hoa_w_v2 import ma_hoa_w_v2a, ma_hoa_w_v2b
from .dem_hang import dem_hang, hang_dem, so_hang_dem
from .tham_chieu import tinh_y_thang, tinh_y_theo_chip
from .thanh_ghi import so_beat_x, so_beat_w, so_beat_y, kiem_tra_cau_hinh, LOI_KHONG
from .tre import tao_tre, ghi_tre, rng_mac_dinh
from .xuat_hex import ghi_cac_beat, ghi_int8

# phiên bản -> (số làn = số hàng / beat, hàm đóng gói một beat W)
PHIEN_BAN = {pb: (SO_LAN[pb], ham) for pb, ham in
             [("v1", ma_hoa_w_v1), ("v1b", ma_hoa_w_v1b), ("v2a", ma_hoa_w_v2a), ("v2b", ma_hoa_w_v2b)]}


def ma_hoa_luong(X, W, phien_ban="v1"):
    """Trả về (các beat X, các beat W) theo đúng thứ tự chip nhận. W được đệm hàng nếu cần."""
    so_lan, ma_hoa_w = PHIEN_BAN[phien_ban]
    K = len(X)
    W = dem_hang(W, phien_ban)
    beat_x = [ma_hoa_x(X[k:k + KHUC]) for k in range(0, K, KHUC)]
    beat_w = []
    for nhom in range(0, len(W), so_lan):
        for k in range(0, K, KHUC):
            beat_w.append(ma_hoa_w([W[nhom + lan][k:k + KHUC] for lan in range(so_lan)]))
    return beat_x, beat_w


def ghi_bo_vector(thu_muc, X, W, S, phien_ban="v1", ghi_chu="", rng_tre=None):
    """Tính đáp án, tự kiểm tra hai cách tính, đóng gói và ghi các file. Trả về Y."""
    so_lan, _ = PHIEN_BAN[phien_ban]
    K, N = len(X), len(W)
    if kiem_tra_cau_hinh(K, N, S, MA_CHE_DO[phien_ban]) != LOI_KHONG:
        raise ValueError(f"Cấu hình không hợp lệ: K={K}, N={N}, S={S}")
    Y = tinh_y_thang(W, X, S)
    assert Y == tinh_y_theo_chip(W, X, S, so_lan, hang_dem(K, phien_ban)), "Hai cách tính Y không khớp!"
    beat_x, beat_w = ma_hoa_luong(X, W, phien_ban)
    beat_y = dong_goi_y(Y)
    assert len(beat_x) == so_beat_x(K) and len(beat_w) == so_beat_w(K, N, phien_ban)
    assert len(beat_y) == so_beat_y(N)

    rng_tre = rng_tre or rng_mac_dinh()
    os.makedirs(thu_muc, exist_ok=True)
    p = lambda ten: os.path.join(thu_muc, ten)
    ghi_cac_beat(p("x_in.hex"), beat_x)
    ghi_cac_beat(p("w_in.hex"), beat_w)
    ghi_int8(p("y_expected.hex"), Y)
    ghi_cac_beat(p("y_out.hex"), beat_y)
    ghi_tre(p("tre_vao.hex"), tao_tre(len(beat_x) + len(beat_w), rng_tre))
    ghi_tre(p("tre_ra.hex"), tao_tre(len(beat_y), rng_tre))
    with open(p("config.txt"), "w", encoding="utf-8") as f:
        f.write(f"PHIEN_BAN={phien_ban}\nMODE={MA_CHE_DO[phien_ban]}\nK={K}\nN={N}\n"
                f"N_DEM={N + so_hang_dem(N, so_lan)}\nKHUC={KHUC}\nLAN={so_lan}\nS={S}\n"
                f"SO_BEAT_X={len(beat_x)}\nSO_BEAT_W={len(beat_w)}\nSO_BEAT_Y={len(beat_y)}\n"
                f"GHI_CHU={ghi_chu}\n")
    return Y


def ghi_bo_vector_v1(thu_muc, X, W, S, ghi_chu=""):
    return ghi_bo_vector(thu_muc, X, W, S, "v1", ghi_chu)
