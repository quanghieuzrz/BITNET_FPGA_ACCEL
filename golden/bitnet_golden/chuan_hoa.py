"""Re-quantization: Y = Kẹp( (Acc + 2^(S-1)) >>> S, -127, 127 ).

Quy ước làm tròn: ".5 làm tròn LÊN" (vd 62.5 -> 63, -62.5 -> -62).
RTL phải dùng dịch phải SỐ HỌC (>>>) trên số có dấu để khớp.
"""
from .hang_so import ACC_BIT, INT8_MIN, INT8_MAX


def kiem_tra_acc(acc):
    """Báo lỗi nếu Acc vượt độ rộng ACC_BIT bit có dấu (RTL sẽ bị tràn)."""
    gioi_han = 1 << (ACC_BIT - 1)
    if not (-gioi_han <= acc < gioi_han):
        raise OverflowError(f"Acc = {acc} vượt {ACC_BIT} bit có dấu")


def chuan_hoa(acc, S):
    """Đổi Acc (số nguyên) về INT8 chỉ bằng cộng, dịch bit và kẹp."""
    if S < 1:
        raise ValueError("S phải >= 1")
    kiem_tra_acc(acc)
    y = (acc + (1 << (S - 1))) >> S      # >> của Python với số âm = dịch số học
    return max(INT8_MIN, min(INT8_MAX, y))


def s_nho_nhat_vua(max_abs):
    """S >= 1 nhỏ nhất sao cho max_abs / 2^S <= 127 (chỉ dùng so sánh và dịch, như mạch dò bit)."""
    S = 1
    while (max_abs >> S) > INT8_MAX or ((max_abs + (1 << (S - 1))) >> S) > INT8_MAX:
        S += 1
    return S


def chon_S_an_toan(cac_acc_hieu_chinh):
    """Requant E: một S cho cả lớp, đủ lớn để token hiệu chỉnh lớn nhất cũng không bị kẹp.

    cac_acc_hieu_chinh: danh sách Acc (của mọi token chạy thử, gộp chung).
    """
    return s_nho_nhat_vua(max(abs(a) for a in cac_acc_hieu_chinh))


def chuan_hoa_theo_token(cac_acc_cua_token):
    """Requant B: S riêng cho token này, tính từ max|Acc| của chính nó. Trả về (danh sách Y, S)."""
    S = s_nho_nhat_vua(max(abs(a) for a in cac_acc_cua_token))
    return [chuan_hoa(a, S) for a in cac_acc_cua_token], S
