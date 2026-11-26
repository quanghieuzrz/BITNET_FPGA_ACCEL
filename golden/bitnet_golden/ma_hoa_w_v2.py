"""Mã hoá / giải mã W v2 (nén 2:4). Quy ước theo docs/dac_ta_muc_bit.md, mục 3.2 và 3.3.

v2a: 5 bit / nhóm 4, nhóm phải có ĐÚNG 2 phần tử khác 0, 6 hàng / beat
     bit [80r + 5g + 4 : 80r + 5g] = nhóm g của hàng r
     trong nhóm: [4:2] = mã vị trí, [1] = dấu phần tử vị trí nhỏ hơn, [0] = dấu phần tử còn lại

v2b: 6 bit / nhóm 4, nhóm có TỐI ĐA 2 phần tử khác 0, 5 hàng / beat
     bit [96r + 6g + 5 : 96r + 6g] = nhóm g của hàng r
     [5] = bit chế độ
       chế độ 0: [4:0] giống hệt v2a
       chế độ 1: [4] = Z, [3:2] = vị trí, [1] = dấu, [0] = 0
                 Z = 1: nhóm toàn 0 ;  Z = 0: đúng 1 phần tử khác 0

Dấu: 0 = +1, 1 = -1. Phần đệm phía trên (bit 511..480) = 0.
"""
from .hang_so import (KHUC, NHOM, CAP_VI_TRI, BEAT_BIT,
                      W_V2A_BIT_NHOM, W_V2B_BIT_NHOM, LAN_V2A, LAN_V2B)


def _dau(w):
    return 1 if w == -1 else 0


def _tu_dau(bit):
    return -1 if bit else +1


def _vi_tri_khac_0(nhom):
    for i, w in enumerate(nhom):
        if w not in (-1, 0, 1):
            raise ValueError(f"Trọng số {w} không phải -1/0/+1")
    return [i for i, w in enumerate(nhom) if w != 0]


# ---------------- Một nhóm 4 trọng số ----------------
def ma_hoa_nhom_v2a(nhom):
    """[0, +1, 0, -1] -> 0b10001 (vị trí 100, dấu 0, dấu 1)."""
    vt = _vi_tri_khac_0(nhom)
    if len(vt) != 2:
        raise ValueError(f"v2a cần đúng 2 phần tử khác 0, nhóm {nhom} có {len(vt)}")
    ma_vt = CAP_VI_TRI.index((vt[0], vt[1]))
    return (ma_vt << 2) | (_dau(nhom[vt[0]]) << 1) | _dau(nhom[vt[1]])


def giai_ma_nhom_v2a(ma):
    ma_vt = (ma >> 2) & 0b111
    if ma_vt >= len(CAP_VI_TRI):
        raise ValueError(f"Mã vị trí {ma_vt:03b} bị cấm")
    a, b = CAP_VI_TRI[ma_vt]
    nhom = [0] * NHOM
    nhom[a] = _tu_dau((ma >> 1) & 1)
    nhom[b] = _tu_dau(ma & 1)
    return nhom


def ma_hoa_nhom_v2b(nhom):
    """[0,0,0,0] -> 1 1 00 0 0 ;  [0,0,+1,0] -> 1 0 10 0 0 ;  2 phần tử -> 0 + mã v2a."""
    vt = _vi_tri_khac_0(nhom)
    if len(vt) == 2:
        return ma_hoa_nhom_v2a(nhom)                      # bit chế độ = 0
    if len(vt) == 0:
        return (1 << 5) | (1 << 4)                        # chế độ 1, Z = 1
    if len(vt) == 1:
        p = vt[0]
        return (1 << 5) | (p << 2) | (_dau(nhom[p]) << 1) # chế độ 1, Z = 0
    raise ValueError(f"v2b cho phép tối đa 2 phần tử khác 0, nhóm {nhom} có {len(vt)}")


def giai_ma_nhom_v2b(ma):
    if ((ma >> 5) & 1) == 0:
        return giai_ma_nhom_v2a(ma & 0b11111)
    if (ma >> 4) & 1:                                     # Z = 1
        if ma & 0b1111:
            raise ValueError(f"Nhóm toàn 0 nhưng bit [3:0] khác 0: {ma:06b}")
        return [0] * NHOM
    if ma & 1:
        raise ValueError(f"Bit [0] phải bằng 0 ở chế độ 1: {ma:06b}")
    nhom = [0] * NHOM
    nhom[(ma >> 2) & 0b11] = _tu_dau((ma >> 1) & 1)
    return nhom


# ---------------- Một beat ----------------
def _ma_hoa_beat(cac_khuc_hang, so_lan, bit_nhom, ham_nhom, so_cot):
    if len(cac_khuc_hang) > so_lan:
        raise ValueError(f"Một beat chứa tối đa {so_lan} khúc hàng")
    if so_cot % NHOM:
        raise ValueError(f"Số cột {so_cot} phải chia hết cho {NHOM}")
    bit_moi_hang = (so_cot // NHOM) * bit_nhom
    beat = 0
    for r, hang in enumerate(cac_khuc_hang):
        if len(hang) != so_cot:
            raise ValueError(f"Khúc hàng {r} phải có {so_cot} trọng số")
        for g in range(so_cot // NHOM):
            ma = ham_nhom(hang[NHOM * g:NHOM * g + NHOM])
            beat |= ma << (bit_moi_hang * r + bit_nhom * g)
    return beat


def _giai_ma_beat(beat, so_hang, bit_nhom, ham_nhom, so_cot):
    bit_moi_hang = (so_cot // NHOM) * bit_nhom
    if beat >> (so_hang * bit_moi_hang):
        raise ValueError("Phần đệm phía trên phải bằng 0")
    mat_na = (1 << bit_nhom) - 1
    cac_hang = []
    for r in range(so_hang):
        hang = []
        for g in range(so_cot // NHOM):
            hang += ham_nhom((beat >> (bit_moi_hang * r + bit_nhom * g)) & mat_na)
        cac_hang.append(hang)
    return cac_hang


def ma_hoa_w_v2a(cac_khuc_hang, so_cot=KHUC):
    return _ma_hoa_beat(cac_khuc_hang, LAN_V2A, W_V2A_BIT_NHOM, ma_hoa_nhom_v2a, so_cot)


def giai_ma_w_v2a(beat, so_hang=LAN_V2A, so_cot=KHUC):
    return _giai_ma_beat(beat, so_hang, W_V2A_BIT_NHOM, giai_ma_nhom_v2a, so_cot)


def ma_hoa_w_v2b(cac_khuc_hang, so_cot=KHUC):
    return _ma_hoa_beat(cac_khuc_hang, LAN_V2B, W_V2B_BIT_NHOM, ma_hoa_nhom_v2b, so_cot)


def giai_ma_w_v2b(beat, so_hang=LAN_V2B, so_cot=KHUC):
    return _giai_ma_beat(beat, so_hang, W_V2B_BIT_NHOM, giai_ma_nhom_v2b, so_cot)
