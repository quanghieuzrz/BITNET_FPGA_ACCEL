"""Golden model bit-accurate cho IP core BitLinear 1.58-bit.

Các module:
    hang_so      : tham số dùng chung (độ rộng beat, khúc, mã W)
    chuan_hoa    : re-quantization Acc -> INT8 (cộng làm tròn, dịch, kẹp)
    ma_hoa_x     : mã hoá / giải mã beat X
    ma_hoa_w_v1  : mã hoá / giải mã beat W v1 (2 bit / trọng số)
    ma_hoa_w_v1b : v1b kiểu TQ1_0 ; ma_hoa_w_v2 : v2a, v2b
    dem_hang     : đệm hàng ; ma_hoa_y : beat Y ; thanh_ghi : thanh ghi AXI4-Lite
    tre, mo_hinh_giao_dich : gián đoạn và mô hình theo nhịp
    tham_chieu   : tính đáp án Y (cách đơn giản, chắc chắn đúng)
    xuat_hex     : đổi beat sang chuỗi hex, ghi file .hex
"""
