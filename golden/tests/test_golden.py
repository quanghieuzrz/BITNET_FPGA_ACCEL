"""Kiểm thử tự động cho golden model.

Chạy (đứng ở thư mục golden/):
    python3 -m pytest tests            # nếu đã cài pytest
    python3 tests/test_golden.py       # không cần pytest
"""
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from bitnet_golden.chuan_hoa import chuan_hoa
from bitnet_golden.ma_hoa_x import ma_hoa_x, giai_ma_x
from bitnet_golden.ma_hoa_w_v1 import ma_hoa_w_v1, giai_ma_w_v1
from bitnet_golden.tham_chieu import tinh_y_thang, tinh_y_theo_chip
from bitnet_golden.xuat_hex import beat_sang_hex


def test_chuan_hoa_cac_truong_hop():
    # (Acc, S, Y mong đợi) — lấy từ bước 2
    for acc, S, y in [(1000, 4, 63), (-1000, 4, -62), (5000, 4, 127),
                      (-5000, 4, -127), (8, 4, 1), (-233, 6, -4), (0, 4, 0)]:
        assert chuan_hoa(acc, S) == y, (acc, S)


def test_requant_E_va_B():
    from bitnet_golden.chuan_hoa import chon_S_an_toan, chuan_hoa_theo_token, s_nho_nhat_vua
    # ví dụ đã học: token 1 lớn nhất 222 -> S = 1 ; token 2 lớn nhất 900 -> S = 3
    assert s_nho_nhat_vua(222) == 1 and s_nho_nhat_vua(900) == 3
    assert s_nho_nhat_vua(254) == 1          # (254 + 1) >> 1 = 127, vừa khít
    assert s_nho_nhat_vua(255) == 2          # (255 + 1) >> 1 = 128 sẽ bị kẹp -> phải S = 2
    t1, t2 = [-88, 78, 222, -115], [400, -900, 150, -320]
    assert chuan_hoa_theo_token(t1) == ([-44, 39, 111, -57], 1)      # cách B
    assert chuan_hoa_theo_token(t2) == ([50, -112, 19, -40], 3)
    S = chon_S_an_toan(t1 + t2)                                       # cách E
    assert S == 3
    assert [chuan_hoa(a, S) for a in t1] == [-11, 10, 28, -14]
    for a in t1 + t2:                                                 # E không bao giờ kẹp trên dữ liệu hiệu chỉnh
        assert -127 <= (a + (1 << (S - 1))) >> S <= 127                # giá trị TRƯỚC khi kẹp đã nằm trong INT8


def test_x_ma_hoa_giai_ma():
    x = [10, -1, 127, -127]
    assert f"{ma_hoa_x(x):08X}" == "817FFF0A"
    for sai in ([-128], [128]):                       # -128 và ngoài khoảng đều bị từ chối
        try:
            ma_hoa_x(sai)
            assert False, sai
        except ValueError:
            pass
    rng = random.Random(0)
    x64 = [rng.randint(-127, 127) for _ in range(64)]
    assert giai_ma_x(ma_hoa_x(x64)) == x64


def test_w_v1_ma_hoa_giai_ma():
    assert f"{ma_hoa_w_v1([[+1, 0, -1, -1], [0, +1, +1, -1]], so_cot=4):016b}" == "1001010010100001"
    rng = random.Random(0)
    bon_hang = [[rng.choice([-1, 0, 1]) for _ in range(64)] for _ in range(4)]
    assert giai_ma_w_v1(ma_hoa_w_v1(bon_hang)) == bon_hang


def test_hai_cach_tinh_y_khop():
    rng = random.Random(1)
    K, so_hang = 256, 12
    X = [rng.randint(-127, 127) for _ in range(K)]
    W = [[rng.choice([-1, 0, 1]) for _ in range(K)] for _ in range(so_hang)]
    assert tinh_y_thang(W, X, 7) == tinh_y_theo_chip(W, X, 7, so_lan=4)


def test_beat_du_128_ky_tu():
    assert len(beat_sang_hex(0)) == 128


def _moi_nhom_ternary():
    """Liệt kê đủ 81 nhóm 4 trọng số (3^4)."""
    import itertools
    return [list(t) for t in itertools.product([-1, 0, 1], repeat=4)]


def test_v2_vi_du_tinh_tay():
    from bitnet_golden.ma_hoa_w_v2 import ma_hoa_nhom_v2a, ma_hoa_nhom_v2b
    assert f"{ma_hoa_nhom_v2a([0, +1, 0, -1]):05b}" == "10001"     # vị trí 100, dấu 0, 1
    assert f"{ma_hoa_nhom_v2b([0, +1, 0, -1]):06b}" == "010001"    # chế độ 0 + mã v2a
    assert f"{ma_hoa_nhom_v2b([0, 0, +1, 0]):06b}" == "101000"     # 1 0 10 0 0
    assert f"{ma_hoa_nhom_v2b([0, 0, 0, -1]):06b}" == "101110"     # 1 0 11 1 0
    assert f"{ma_hoa_nhom_v2b([0, 0, 0, 0]):06b}" == "110000"      # 1 1 00 0 0


def test_v2a_du_24_kieu():
    from bitnet_golden.ma_hoa_w_v2 import ma_hoa_nhom_v2a, giai_ma_nhom_v2a
    hop_le = [n for n in _moi_nhom_ternary() if sum(w != 0 for w in n) == 2]
    assert len(hop_le) == 24
    cac_ma = set()
    for n in hop_le:
        ma = ma_hoa_nhom_v2a(n)
        assert ma < 32 and giai_ma_nhom_v2a(ma) == n
        cac_ma.add(ma)
    assert len(cac_ma) == 24                        # không hai nhóm nào trùng mã
    for n in _moi_nhom_ternary():                   # nhóm 0, 1, 3, 4 phần tử khác 0 phải bị từ chối
        if sum(w != 0 for w in n) != 2:
            try:
                ma_hoa_nhom_v2a(n)
                assert False, n
            except ValueError:
                pass


def test_v2b_du_33_kieu():
    from bitnet_golden.ma_hoa_w_v2 import ma_hoa_nhom_v2b, giai_ma_nhom_v2b
    hop_le = [n for n in _moi_nhom_ternary() if sum(w != 0 for w in n) <= 2]
    assert len(hop_le) == 33                        # 1 + 8 + 24
    cac_ma = set()
    for n in hop_le:
        ma = ma_hoa_nhom_v2b(n)
        assert ma < 64 and giai_ma_nhom_v2b(ma) == n
        cac_ma.add(ma)
    assert len(cac_ma) == 33


def test_v2_beat_va_y_giong_v1():
    import tao_vector_v2 as tv2
    from bitnet_golden.ma_hoa_w_v2 import (ma_hoa_w_v2a, giai_ma_w_v2a,
                                           ma_hoa_w_v2b, giai_ma_w_v2b)
    rng = random.Random(5)
    sau_hang = tv2.tao_W(64, 6, rng, tv2.nhom_dung_2)
    nam_hang = tv2.tao_W(64, 5, rng, tv2.nhom_toi_da_2)
    beat_a, beat_b = ma_hoa_w_v2a(sau_hang), ma_hoa_w_v2b(nam_hang)
    assert beat_a >> 480 == 0 and beat_b >> 480 == 0           # phần đệm = 0
    assert giai_ma_w_v2a(beat_a) == sau_hang
    assert giai_ma_w_v2b(beat_b) == nam_hang
    X = [rng.randint(-127, 127) for _ in range(128)]
    W = tv2.tao_W(128, 60, rng, tv2.nhom_toi_da_2)
    y = tinh_y_thang(W, X, 6)
    for so_lan in (4, 5, 6):                                    # v1, v2b, v2a
        assert tinh_y_theo_chip(W, X, 6, so_lan) == y


def test_v1b_tq_byte():
    from bitnet_golden.ma_hoa_w_v1b import ma_hoa_byte_tq, giai_ma_byte_tq
    assert ma_hoa_byte_tq([+1, 0, -1, -1, +1]) == 191          # ví dụ đã học
    assert ma_hoa_byte_tq([-1] * 5) == 0 and ma_hoa_byte_tq([+1] * 5) == 242
    import itertools
    tat_ca = [list(t) for t in itertools.product([-1, 0, 1], repeat=5)]
    assert len(tat_ca) == 243
    cac_byte = {ma_hoa_byte_tq(t) for t in tat_ca}
    assert cac_byte == set(range(243))                            # đủ 243 mã, không trùng
    for t in tat_ca:
        assert giai_ma_byte_tq(ma_hoa_byte_tq(t)) == t
    for b in range(243, 256):                                     # byte 243..255 bị cấm
        try:
            giai_ma_byte_tq(b)
            assert False, b
        except ValueError:
            pass


def test_v1b_beat_vat_qua_hai_hang():
    from bitnet_golden.ma_hoa_w_v1b import ma_hoa_w_v1b, giai_ma_w_v1b, giai_ma_byte_tq
    rng = random.Random(8)
    nam_hang = [[rng.choice([-1, 0, 1]) for _ in range(64)] for _ in range(5)]
    beat = ma_hoa_w_v1b(nam_hang)
    assert beat >> 512 == 0                                       # vừa khít 512 bit
    assert giai_ma_w_v1b(beat) == nam_hang
    # byte 12 chứa trọng số 60..63 của hàng 0 và trọng số 0 của hàng 1
    assert giai_ma_byte_tq((beat >> 96) & 0xFF) == nam_hang[0][60:64] + nam_hang[1][0:1]
    X = [rng.randint(-127, 127) for _ in range(128)]
    W = [[rng.choice([-1, 0, 1]) for _ in range(128)] for _ in range(20)]
    assert tinh_y_theo_chip(W, X, 6, so_lan=5) == tinh_y_thang(W, X, 6)


def test_cac_truong_hop_bien():
    # Đáp án tính tay cho từng bộ vector biên (xem tao_vector_bien.py)
    import tao_vector_bien as tvb
    mong_doi = {
        "acc_cuc_dai": [127, -127, 0, 0],
        "x_toan_127": [127, -127, 127, -127],
        "moc_nua": [1, 0, 2, -1],
        "moc_kep": [127, 127, -127, -127],
        "tru_so_am": [50, -50, 61, 1],
        "vi_tri_bit": [-32, 1, 1, -31],
    }
    for ham in tvb.CAC_TRUONG_HOP:
        ten, X, W, S, _ = ham()
        assert tinh_y_thang(W, X, S) == mong_doi[ten], ten
        assert tinh_y_theo_chip(W, X, S, so_lan=4) == mong_doi[ten], ten


# ---------------- Bổ sung giai đoạn 1: A1 – A4 ----------------
def _W_hop_le(phien_ban, K, N, rng):
    """W ngẫu nhiên hợp lệ với phiên bản (v2a: đúng 2 khác 0 / nhóm; v2b: tối đa 2)."""
    def nhom():
        if phien_ban in ("v1", "v1b"):
            return [rng.choice([-1, 0, 1]) for _ in range(4)]
        so = 2 if phien_ban == "v2a" else rng.choice([0, 1, 2])
        g = [0] * 4
        for p in rng.sample(range(4), so):
            g[p] = rng.choice([-1, 1])
        return g
    return [sum((nhom() for _ in range(K // 4)), []) for _ in range(N)]


def test_A1_dem_hang():
    from bitnet_golden.dem_hang import dem_hang, so_nhom_hang, so_hang_dem
    from bitnet_golden.bo_vector import ma_hoa_luong, PHIEN_BAN
    from bitnet_golden.hang_so import SO_LAN
    # kích thước thật của BitNet 2B
    assert so_nhom_hang(2560, 6) == 427 and so_hang_dem(2560, 6) == 2
    assert so_nhom_hang(6912, 5) == 1383 and so_hang_dem(6912, 5) == 3
    assert so_hang_dem(640, 6) == 2 and so_hang_dem(2560, 4) == 0
    rng = random.Random(7)
    K = 128
    X = [rng.randint(-127, 127) for _ in range(K)]
    for pb in ("v1", "v1b", "v2a", "v2b"):
        for N in (1, 7, 11, 13):                       # không chia hết cho 4, 5, 6
            W = _W_hop_le(pb, K, N, rng)
            Wd = dem_hang(W, pb)
            assert len(Wd) % SO_LAN[pb] == 0 and Wd[:N] == W
            beat_x, beat_w = ma_hoa_luong(X, W, pb)   # v2a: hàng giả phải mã hoá được
            assert len(beat_w) == so_nhom_hang(N, SO_LAN[pb]) * (K // 64)
            assert tinh_y_theo_chip(W, X, 6, SO_LAN[pb]) == tinh_y_thang(W, X, 6)


def test_A1_hang_dem_v2a_khong_duoc_toan_0():
    from bitnet_golden.ma_hoa_w_v2 import ma_hoa_w_v2a
    try:
        ma_hoa_w_v2a([[0] * 64])
        assert False, "v2a phải từ chối hàng toàn 0"
    except ValueError:
        pass


def test_A2_dong_goi_y():
    from bitnet_golden.ma_hoa_y import dong_goi_y, giai_ma_y
    Y = list(range(-60, 70))                           # 130 số -> 3 beat, beat cuối 2 số
    beats = dong_goi_y(Y)
    assert len(beats) == 3 and beats[2] >> 16 == 0     # byte thừa = 0
    assert giai_ma_y(beats, 130) == Y
    assert beats[0] == ma_hoa_x(Y[:64])                # giống hệt beat X


def test_A3_thanh_ghi():
    from bitnet_golden.thanh_ghi import (kiem_tra_cau_hinh, LOI_KHONG, LOI_CAU_HINH,
                                         so_beat_w, so_beat_vao, DIA_CHI)
    assert kiem_tra_cau_hinh(2560, 2560, 8, 0) == LOI_KHONG
    assert kiem_tra_cau_hinh(2560, 2560, 0, 0) == LOI_CAU_HINH     # S = 0 cấm
    assert kiem_tra_cau_hinh(100, 10, 4, 0) == LOI_CAU_HINH        # K không chia hết 64
    assert kiem_tra_cau_hinh(7168, 10, 4, 0) == LOI_CAU_HINH       # K > 6912
    assert kiem_tra_cau_hinh(2560, 0, 4, 0) == LOI_CAU_HINH        # N = 0
    assert kiem_tra_cau_hinh(2560, 64, 4, 2, mode_ho_tro=(0,)) == LOI_CAU_HINH   # v2a chưa có RTL
    assert so_beat_w(2560, 2560, "v1") == 640 * 40
    assert so_beat_w(2560, 2560, "v2a") == 427 * 40
    assert so_beat_vao(128, 7, "v1") == 2 + 2 * 2
    assert len(set(DIA_CHI.values())) == len(DIA_CHI)             # không trùng địa chỉ


def test_A4_gian_doan_khong_doi_Y():
    from bitnet_golden.mo_hinh_giao_dich import chay
    from bitnet_golden.dem_hang import dem_hang
    from bitnet_golden.thanh_ghi import so_beat_vao, so_beat_y
    from bitnet_golden.tre import tao_tre
    rng = random.Random(11)
    K = 192
    X = [rng.randint(-127, 127) for _ in range(K)]
    for pb in ("v1", "v1b", "v2a", "v2b"):
        N = 137                                         # 3 beat Y, beat cuối 9 số; cần đệm hàng
        W = _W_hop_le(pb, K, N, rng)
        y_dung = tinh_y_thang(W, X, 7)
        Wd = dem_hang(W, pb)
        y0, nhip0, _ = chay(X, Wd, N, 7, pb)
        assert y0 == y_dung, pb
        assert nhip0 <= so_beat_vao(K, N, pb) + 3      # không gián đoạn: ~1 beat / nhịp
        for lan in range(5):                            # 5 kiểu gián đoạn ngẫu nhiên
            tv = tao_tre(so_beat_vao(K, N, pb), rng, xac_suat=0.5)
            tr = tao_tre(so_beat_y(N), rng, xac_suat=0.8, tre_toi_da=200)   # đầu ra bị chặn lâu
            y1, nhip1, _ = chay(X, Wd, N, 7, pb, tv, tr)
            assert y1 == y_dung, (pb, lan)
            assert nhip1 >= nhip0 + sum(tv)            # gián đoạn chỉ làm chậm, không làm sai


def test_nhieu_token_dung_chung_W():
    from bitnet_golden.nhieu_token import tinh_theo_chip, thu_tu_beat_y, tach_beat_y, khung_x
    from bitnet_golden.ma_hoa_y import dong_goi_y
    from bitnet_golden.thanh_ghi import kiem_tra_cau_hinh, LOI_KHONG, LOI_CAU_HINH, so_beat_x, so_beat_y
    rng = random.Random(21)
    K, N = 128, 70
    for pb in ("v1", "v1b", "v2a", "v2b"):
        W = _W_hop_le(pb, K, N, rng)
        for T in (1, 3, 5):
            cac_X = [[rng.randint(-127, 127) for _ in range(K)] for _ in range(T)]
            cac_Y, nhip = tinh_theo_chip(cac_X, W, 6, pb)          # tự so với tinh_y_thang từng token
            so_beat_w = -(-N // {"v1": 4, "v1b": 5, "v2a": 6, "v2b": 5}[pb]) * (K // 64)
            assert nhip == T * so_beat_w                            # mỗi beat W dùng T nhịp
            beats = thu_tu_beat_y(cac_Y)
            assert len(beats) == so_beat_y(N, T) and len(khung_x(cac_X)) == so_beat_x(K, T)
            assert beats[1 % T] == dong_goi_y(cac_Y[1 % T])[0]      # khối 0 của token 1 đứng thứ 2
            assert [b for b in tach_beat_y(beats, T)] == [dong_goi_y(Y) for Y in cac_Y]
    assert kiem_tra_cau_hinh(2560, 2560, 8, 0, T=4) == LOI_KHONG
    assert kiem_tra_cau_hinh(2560, 2560, 8, 0, T=4, t_toi_da=1) == LOI_CAU_HINH   # giai đoạn 2: chỉ T = 1
    assert kiem_tra_cau_hinh(2560, 2560, 8, 0, T=9) == LOI_CAU_HINH


if __name__ == "__main__":
    so_test = 0
    for ten, ham in list(globals().items()):
        if ten.startswith("test_"):
            ham()
            print(f"OK  {ten}")
            so_test += 1
    print(f"Tất cả {so_test} test đều qua.")
