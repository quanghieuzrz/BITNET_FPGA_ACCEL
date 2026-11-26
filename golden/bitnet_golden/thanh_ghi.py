"""A3. Bảng thanh ghi điều khiển (AXI4-Lite, 32 bit, địa chỉ byte).

| Địa chỉ | Tên       | Quyền | Nghĩa |
|---------|-----------|-------|-------|
| 0x00    | CTRL      | W     | bit 0 START (tự xoá), bit 1 RESET mềm (tự xoá) |
| 0x04    | STATUS    | R     | bit 0 BUSY, bit 1 DONE (giữ tới lần START sau), bit 2 ERROR |
| 0x08    | K         | R/W   | độ dài X, bội số của 64, 64 ... 6912 |
| 0x0C    | N         | R/W   | số hàng W THẬT (chưa đệm), 1 ... 65535 |
| 0x10    | SHIFT_AMT | R/W   | S, 1 ... 23 |
| 0x14    | CYCLES    | R     | số nhịp từ START tới DONE (đo hiệu năng) |
| 0x18    | MODE      | R/W   | 0 = v1, 1 = v1b, 2 = v2a, 3 = v2b |
| 0x1C    | ERR_CODE  | R     | mã lỗi (bảng LOI_* bên dưới), 0 = không lỗi |
| 0x20    | ID        | R     | hằng số nhận dạng IP: 0x424E0100 ("BN", phiên bản 1.0) |
| 0x24    | SO_TOKEN  | R/W   | T = số token dùng chung mỗi beat W, 1 ... 8 (giai đoạn 2 chỉ hỗ trợ T = 1) |

Quy tắc: chỉ ghi K, N, SHIFT_AMT, MODE khi BUSY = 0 (ghi lúc BUSY bị bỏ qua).
START khi cấu hình sai -> không chạy, ERROR = 1, ERR_CODE = LOI_CAU_HINH.
"""
from .hang_so import KHUC, K_TOI_DA, N_TOI_DA, S_MIN, S_MAX, SO_LAN, MA_CHE_DO, T_TOI_DA
from .dem_hang import so_nhom_hang

DIA_CHI = {"CTRL": 0x00, "STATUS": 0x04, "K": 0x08, "N": 0x0C, "SHIFT_AMT": 0x10,
           "CYCLES": 0x14, "MODE": 0x18, "ERR_CODE": 0x1C, "ID": 0x20, "SO_TOKEN": 0x24}

CTRL_START, CTRL_RESET = 1 << 0, 1 << 1
STATUS_BUSY, STATUS_DONE, STATUS_ERROR = 1 << 0, 1 << 1, 1 << 2
ID_IP = 0x424E0100

# Mã lỗi (ERR_CODE)
LOI_KHONG = 0
LOI_CAU_HINH = 1     # K, N, S hoặc MODE sai / chưa hỗ trợ
LOI_MA_W = 2         # gặp mã W cấm (v1: 11; v1b: byte >= 243; v2a: vị trí 110/111; v2b: mẫu sai)
LOI_MA_X = 3         # gặp X = 0x80 (-128)
LOI_TLAST = 4        # TLAST đến sớm, hoặc không có ở beat cuối

CHE_DO_THEO_MA = {v: k for k, v in MA_CHE_DO.items()}


def kiem_tra_cau_hinh(K, N, S, mode, mode_ho_tro=(0, 1, 2, 3), T=1, t_toi_da=T_TOI_DA):
    """Trả về LOI_KHONG nếu cấu hình hợp lệ, ngược lại LOI_CAU_HINH.
    mode_ho_tro: các chế độ bản RTL hiện tại hỗ trợ (giai đoạn 2 chỉ có v1 -> (0,)).
    t_toi_da: T lớn nhất bản RTL hiện tại hỗ trợ (giai đoạn 2: 1)."""
    if not (1 <= T <= t_toi_da):
        return LOI_CAU_HINH
    if not (KHUC <= K <= K_TOI_DA and K % KHUC == 0):
        return LOI_CAU_HINH
    if not (1 <= N <= N_TOI_DA):
        return LOI_CAU_HINH
    if not (S_MIN <= S <= S_MAX):      # S = 0 làm 2^(S-1) vô nghĩa -> cấm
        return LOI_CAU_HINH
    if mode not in mode_ho_tro:
        return LOI_CAU_HINH
    return LOI_KHONG


def so_beat_x(K, T=1):
    return T * (K // KHUC)


def so_beat_w(K, N, phien_ban):
    return so_nhom_hang(N, SO_LAN[phien_ban]) * (K // KHUC)


def so_beat_y(N, T=1):
    return T * -(-N // KHUC)


def so_beat_vao(K, N, phien_ban, T=1):
    """Một khung vào = X (của T token) rồi W liền nhau trên cùng cổng; TLAST ở beat cuối cùng."""
    return so_beat_x(K, T) + so_beat_w(K, N, phien_ban)
