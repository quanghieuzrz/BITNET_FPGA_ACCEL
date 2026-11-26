"""Beat X: bit [8c+7 : 8c] = X[c] (bù hai 8 bit), c = 0..63. X[0] ở bit thấp nhất.

X nằm trong [-127, 127]; mẫu bit 0x80 (-128) bị cấm.
"""
from .hang_so import KHUC, X_BIT, INT8_MIN, INT8_MAX


def ma_hoa_x(x_khuc):
    """Ghép tối đa 64 số INT8 thành một beat (số nguyên 512 bit)."""
    if len(x_khuc) > KHUC:
        raise ValueError(f"Một beat X chứa tối đa {KHUC} số")
    beat = 0
    for c, x in enumerate(x_khuc):
        if not (INT8_MIN <= x <= INT8_MAX):
            raise ValueError(f"X[{c}] = {x} nằm ngoài INT8")
        beat |= (x & 0xFF) << (X_BIT * c)
    return beat


def giai_ma_x(beat, so_luong=KHUC):
    """Tách beat ra danh sách số INT8 (bản mẫu cho phần giải mã trong RTL)."""
    x_khuc = []
    for c in range(so_luong):
        b = (beat >> (X_BIT * c)) & 0xFF
        if b == 0x80:
            raise ValueError(f"X[{c}] = -128 (0x80) bị cấm")
        x_khuc.append(b - 256 if b >= 128 else b)
    return x_khuc
