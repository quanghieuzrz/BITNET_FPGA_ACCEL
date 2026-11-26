"""Mô hình MỨC GIAO DỊCH (theo nhịp) của chip: nhận khung vào qua bắt tay TVALID/TREADY, tính,
xuất beat Y. Dùng để:
  1. kiểm tra quy tắc A4: có gián đoạn hay không thì Y vẫn giống hệt;
  2. đếm số nhịp, đối chiếu với mô hình hiệu năng (B1) và sau này với RTL.

Giả định (bản mẫu cho RTL giai đoạn 2):
  - Một cổng vào: K/64 beat X, rồi các beat W; nhận tối đa 1 beat / nhịp.
  - Chuẩn hoá chạy song song (pipeline), không làm dừng luồng W.
  - Hàng đợi Y chứa tối đa HANG_DOI_Y số; khi không còn chỗ cho R số của nhóm kế, chip hạ TREADY vào.
  - Thanh ghi ra giữ một beat Y tới khi phía nhận chấp nhận.
"""
from .hang_so import KHUC, SO_LAN
from .chuan_hoa import chuan_hoa, kiem_tra_acc
from .dem_hang import so_nhom_hang
from .ma_hoa_y import giai_ma_y
from .ma_hoa_x import ma_hoa_x

HANG_DOI_Y = 2 * KHUC


def chay(X, W_dem, N, S, phien_ban, tre_vao=None, tre_ra=None):
    """X, W_dem: số nguyên (W đã đệm). Trả về (Y, so_nhip, cac_beat_y)."""
    R = SO_LAN[phien_ban]
    K = len(X)
    so_khuc = K // KHUC
    so_nhom = so_nhom_hang(N, R)
    tong_vao = so_khuc + so_nhom * so_khuc
    tre_vao = tre_vao or [0] * tong_vao
    tre_ra = tre_ra or [0] * (-(-N // KHUC))

    i_vao, cho_vao = 0, tre_vao[0]       # beat vào kế tiếp và số nhịp còn phải chờ TVALID
    bo_nho_x = []
    acc = [0] * R
    hang_doi, so_y_da_tinh = [], 0
    thanh_ghi_ra, cho_ra, j_ra = None, 0, 0
    cac_beat_y = []
    nhip = 0

    while len(cac_beat_y) < len(tre_ra):
        nhip += 1
        # ---- phía ra: bắt tay beat Y ----
        if thanh_ghi_ra is not None:
            if cho_ra == 0:
                cac_beat_y.append(thanh_ghi_ra)
                thanh_ghi_ra, j_ra = None, j_ra + 1
            else:
                cho_ra -= 1
        if thanh_ghi_ra is None:
            con_lai = N - (so_y_da_tinh - len(hang_doi))      # số Y chưa đưa vào thanh ghi ra
            if len(hang_doi) >= KHUC or (hang_doi and len(hang_doi) == con_lai):
                thanh_ghi_ra = ma_hoa_x(hang_doi[:KHUC])
                hang_doi = hang_doi[KHUC:]
                cho_ra = tre_ra[j_ra]
        # ---- phía vào: bắt tay beat X / W ----
        tready = len(hang_doi) + R <= HANG_DOI_Y
        if i_vao < tong_vao:
            if cho_vao > 0:
                cho_vao -= 1                                    # TVALID = 0
            elif tready:                                        # TVALID = TREADY = 1 -> nhận beat
                if i_vao < so_khuc:
                    bo_nho_x.append(X[i_vao * KHUC:(i_vao + 1) * KHUC])
                else:
                    t = i_vao - so_khuc
                    nhom, k = divmod(t, so_khuc)
                    if k == 0:
                        acc = [0] * R
                    for lan in range(R):
                        hang = nhom * R + lan
                        for w, x in zip(W_dem[hang][k * KHUC:(k + 1) * KHUC], bo_nho_x[k]):
                            acc[lan] += x if w == 1 else (-x if w == -1 else 0)
                        kiem_tra_acc(acc[lan])
                    if k == so_khuc - 1:                        # xong nhóm -> chuẩn hoá
                        for lan in range(R):
                            if nhom * R + lan < N:              # bỏ hàng giả
                                hang_doi.append(chuan_hoa(acc[lan], S))
                                so_y_da_tinh += 1
                i_vao += 1
                if i_vao < tong_vao:
                    cho_vao = tre_vao[i_vao]
    return giai_ma_y(cac_beat_y, N), nhip, cac_beat_y
