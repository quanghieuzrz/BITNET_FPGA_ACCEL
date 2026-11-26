"""Beat W v1: bit [128r + 2c + 1 : 128r + 2c] = W[hàng r][cột c], r = 0..3, c = 0..63.

Mã: 00 = 0, 01 = +1, 10 = -1, 11 = cấm. Hàng 0 ở 128 bit thấp nhất.
"""
from .hang_so import KHUC, LAN_V1, W_V1_BIT, MA_W_V1, GIAI_W_V1


def ma_hoa_w_v1(cac_khuc_hang, so_cot=KHUC):
    """Ghép tối đa 4 khúc hàng (mỗi khúc so_cot trọng số) thành một beat."""
    if len(cac_khuc_hang) > LAN_V1:
        raise ValueError(f"Một beat W v1 chứa tối đa {LAN_V1} khúc hàng")
    bit_moi_hang = so_cot * W_V1_BIT
    beat = 0
    for r, hang in enumerate(cac_khuc_hang):
        if len(hang) != so_cot:
            raise ValueError(f"Khúc hàng {r} phải có {so_cot} trọng số")
        for c, w in enumerate(hang):
            if w not in MA_W_V1:
                raise ValueError(f"W[{r}][{c}] = {w} không phải -1/0/+1")
            beat |= MA_W_V1[w] << (bit_moi_hang * r + W_V1_BIT * c)
    return beat


def giai_ma_w_v1(beat, so_hang=LAN_V1, so_cot=KHUC):
    """Tách beat ra các khúc hàng; báo lỗi nếu gặp mã 11."""
    bit_moi_hang = so_cot * W_V1_BIT
    cac_hang = []
    for r in range(so_hang):
        hang = []
        for c in range(so_cot):
            ma = (beat >> (bit_moi_hang * r + W_V1_BIT * c)) & 0b11
            if ma == 0b11:
                raise ValueError(f"Mã 11 không hợp lệ ở hàng {r}, cột {c}")
            hang.append(GIAI_W_V1[ma])
        cac_hang.append(hang)
    return cac_hang
