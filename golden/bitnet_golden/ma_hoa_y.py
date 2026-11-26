"""A2. Beat Y (đầu ra của chip): ĐÓNG GÓI GIỐNG HỆT BEAT X.

    beat thứ b chứa Y[64b] ... Y[64b + 63];   bit [8c+7 : 8c] = Y[64b + c]

Số beat Y = làm tròn lên N / 64. Beat cuối nếu thiếu thì các byte còn lại = 0x00.
Lợi ích: một định dạng chung cho X và Y. (Trong BitNet thật Y không đi thẳng làm X lớp sau: CPU còn
đổi Y về số thực, norm, lượng tử lại — xem đặc tả mục 5.1.)
(Các kích thước thật của BitNet 2B: 2560, 6912, 640 đều là bội số của 64 nên không có byte thừa.)
"""
from .hang_so import KHUC
from .ma_hoa_x import ma_hoa_x, giai_ma_x


def dong_goi_y(Y):
    return [ma_hoa_x(Y[i:i + KHUC]) for i in range(0, len(Y), KHUC)]


def giai_ma_y(cac_beat, N):
    """Tách các beat Y ra N số; kiểm tra byte thừa ở beat cuối phải bằng 0."""
    Y = []
    for beat in cac_beat:
        Y += giai_ma_x(beat)
    for c, y in enumerate(Y[N:]):
        if y != 0:
            raise ValueError(f"Byte thừa thứ {c} ở beat Y cuối khác 0")
    return Y[:N]
