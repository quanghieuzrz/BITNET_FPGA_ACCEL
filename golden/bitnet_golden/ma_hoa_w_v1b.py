"""Mã hoá / giải mã W v1b: kiểu TQ1_0, gói hệ 3, 5 trọng số / byte, 5 hàng / beat.

Quy ước (docs/dac_ta_muc_bit.md, mục 3.4):
  - Chữ số hệ 3 của trọng số: -1 -> 0, 0 -> 1, +1 -> 2.
  - 5 trọng số [w0, w1, w2, w3, w4] -> byte = d0*81 + d1*27 + d2*9 + d3*3 + d4   (w0 là chữ số cao nhất)
    vd [+1, 0, -1, -1, +1] -> 2*81 + 1*27 + 0 + 0 + 2 = 191.  Byte 243..255 bị cấm.
  - Beat: nối 5 khúc hàng (mỗi khúc so_cot trọng số) thành một dãy 5*so_cot trọng số,
    byte j chứa phần tử 5j .. 5j+4 của dãy, đặt ở bit [8j+7 : 8j].
    Với so_cot = 64: 64 byte = 512 bit, vừa khít một beat. Một byte có thể chứa trọng số của hai hàng.

Lưu ý: chỉ "kiểu TQ1_0" (cùng ý tưởng 5 trọng số / byte). Thứ tự chữ số và bố cục beat là quy ước
của dự án, không trùng bố cục khối trong file GGUF của bitnet.cpp.
"""
from .hang_so import KHUC, LAN_V1B, TQ_MOI_BYTE, TQ_SO_MA

_CHU_SO = {-1: 0, 0: 1, +1: 2}
_TRONG_SO = {0: -1, 1: 0, 2: +1}


def ma_hoa_byte_tq(nam_trong_so):
    """5 trọng số -> 1 byte (0..242)."""
    if len(nam_trong_so) != TQ_MOI_BYTE:
        raise ValueError(f"Cần đúng {TQ_MOI_BYTE} trọng số")
    gia_tri = 0
    for w in nam_trong_so:
        if w not in _CHU_SO:
            raise ValueError(f"Trọng số {w} không phải -1/0/+1")
        gia_tri = gia_tri * 3 + _CHU_SO[w]            # như đọc số: nhân 3 rồi cộng chữ số tiếp theo
    return gia_tri


def _tao_bang_tra():
    """Bảng tra 243 dòng: byte -> 5 trọng số (đúng thứ mạch ROM 256 dòng sẽ chứa)."""
    bang = []
    for b in range(TQ_SO_MA):
        chu_so, x = [], b
        for _ in range(TQ_MOI_BYTE):
            chu_so.append(x % 3)
            x //= 3
        bang.append([_TRONG_SO[d] for d in reversed(chu_so)])
    return bang


BANG_TRA_TQ = _tao_bang_tra()


def giai_ma_byte_tq(b):
    """1 byte -> 5 trọng số, bằng cách TRA BẢNG (không chia)."""
    if b >= TQ_SO_MA:
        raise ValueError(f"Byte {b} bị cấm (chỉ 0..{TQ_SO_MA - 1} hợp lệ)")
    return list(BANG_TRA_TQ[b])


def ma_hoa_w_v1b(cac_khuc_hang, so_cot=KHUC):
    """Ghép đúng LAN_V1B (5) khúc hàng thành một beat."""
    if len(cac_khuc_hang) != LAN_V1B:
        raise ValueError(f"Một beat v1b chứa đúng {LAN_V1B} khúc hàng")
    day = []
    for r, hang in enumerate(cac_khuc_hang):
        if len(hang) != so_cot:
            raise ValueError(f"Khúc hàng {r} phải có {so_cot} trọng số")
        day += hang                                    # nối các hàng thành một dãy dài
    beat = 0
    for j in range(len(day) // TQ_MOI_BYTE):           # so_cot byte (5 hàng x so_cot / 5)
        beat |= ma_hoa_byte_tq(day[TQ_MOI_BYTE * j:TQ_MOI_BYTE * j + TQ_MOI_BYTE]) << (8 * j)
    return beat


def giai_ma_w_v1b(beat, so_hang=LAN_V1B, so_cot=KHUC):
    """Mở hết các byte ra một dãy dài, rồi cắt lại thành từng khúc hàng."""
    so_byte = so_hang * so_cot // TQ_MOI_BYTE
    if beat >> (8 * so_byte):
        raise ValueError("Có bit ngoài vùng dữ liệu")
    day = []
    for j in range(so_byte):
        day += giai_ma_byte_tq((beat >> (8 * j)) & 0xFF)
    return [day[so_cot * r:so_cot * r + so_cot] for r in range(so_hang)]
