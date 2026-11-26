# bitnet-fpga-accel

IP core trên FPGA tăng tốc lớp **BitLinear** của BitNet b1.58 (trọng số ternary −1/0/+1, kích hoạt INT8)
chỉ bằng cộng, trừ và dịch bit (0 DSP), với hai phiên bản để so sánh:

- **v1**: dày đặc, 2 bit/trọng số, zero-gating
- **v1b**: kiểu TQ1_0, 5 trọng số/byte (1.6 bit/trọng số), phiên bản đối chứng
- **v2a / v2b**: nén 2:4 structured sparsity (5 bit hoặc 6 bit mỗi nhóm 4 trọng số)

## Cấu trúc thư mục

```
bitnet-fpga-accel/
├── README.md
├── .gitignore
├── docs/
│   ├── dac_ta_muc_bit.md        # Đặc tả mức bit: nguồn quy ước duy nhất
│   ├── giai_doan_1.md           # Tổng kết giai đoạn 1
│   ├── quy_tac_rtl.md           # Quy tắc viết RTL + danh sách kiểm tra
│   └── ke_hoach_danh_gia.md     # Đo gì, so với ai, bằng dữ liệu nào
├── golden/                      # Golden model Python (bit-accurate)
│   ├── bitnet_golden/
│   │   ├── hang_so.py           # Tham số chung
│   │   ├── chuan_hoa.py         # Re-quantization
│   │   ├── ma_hoa_x.py          # Mã hoá / giải mã beat X
│   │   ├── ma_hoa_w_v1.py       # Mã hoá / giải mã beat W v1
│   │   ├── ma_hoa_w_v1b.py      # Mã hoá / giải mã beat W v1b (kiểu TQ1_0)
│   │   ├── ma_hoa_w_v2.py       # Mã hoá / giải mã beat W v2a, v2b (nén 2:4)
│   │   ├── tham_chieu.py        # Tính đáp án Y
│   │   ├── xuat_hex.py          # Ghi file .hex
│   │   ├── dem_hang.py          # Đệm hàng khi N không chia hết cho R
│   │   ├── ma_hoa_y.py          # Đóng gói beat Y (giống beat X)
│   │   ├── thanh_ghi.py         # Bảng thanh ghi AXI4-Lite, mã lỗi, đếm beat
│   │   ├── tre.py               # Tạo file trễ (gián đoạn) cho testbench
│   │   ├── mo_hinh_giao_dich.py # Mô hình theo nhịp: bắt tay, hàng đợi Y, chặn ngược
│   │   ├── nhieu_token.py       # Dùng chung một beat W cho T token
│   │   └── bo_vector.py         # Ghi một bộ vector (v1 / v1b / v2a / v2b) từ X, W, S
│   ├── tao_vector_v1.py         # Tạo bộ vector v1 ngẫu nhiên
│   ├── tao_vector_bien.py       # Tạo các bộ vector biên (bước 7)
│   ├── tao_vector_v1b.py        # Tạo vector v1b + v1 đối chiếu
│   ├── tao_vector_v2.py         # Tạo vector v2a, v2b + v1 đối chiếu (bước 8)
│   ├── so_sanh_phien_ban.py     # So sánh 4 cách đóng gói W trên cùng dữ liệu
│   ├── tao_vector_768.py        # Bộ 768 x 768 (mốc so sánh TernaryCore)
│   ├── tao_vector_requant.py    # Vector cho requant.v
│   ├── tao_vector_w_decode.py   # Vector cho w_decode_v1.v
│   ├── mo_hinh_hieu_nang.py     # Dự đoán số nhịp, token/giây theo băng thông
│   ├── do_sai_so_gamma.py       # Đo sai số khi thay gamma bằng 2^-S (cần numpy)
│   └── tests/
│       └── test_golden.py       # Kiểm thử tự động
├── learning/                    # Script học từng bước (bước 1–5)
├── rtl/
│   ├── requant.v                # Khối chuẩn hoá (giai đoạn 2, bước 1)
│   └── w_decode_v1.v            # Giải mã beat W v1 (giai đoạn 2, bước 2)
├── tb/
│   ├── tb_requant.v             # Testbench khối chuẩn hoá
│   └── tb_w_decode_v1.v         # Testbench khối giải mã W v1
├── scripts/
│   ├── chay_tb_requant.sh       # Một lệnh: tạo vector -> mô phỏng -> so kết quả
│   ├── chay_tb_w_decode_v1.sh   # Như trên cho khối giải mã W v1 (kèm lint)
│   └── uoc_luong_tai_nguyen.sh  # Ước lượng LUT/FF/DSP sơ bộ bằng Yosys
└── vectors/                     # Vector sinh tự động (không đưa lên GitHub)
```

## Bắt đầu

Công cụ RTL: Icarus Verilog (mô phỏng), Verilator (lint), Yosys (ước lượng tài nguyên), Vivado (tổng hợp chính thức).

Yêu cầu: Python 3.8 trở lên. Riêng `do_sai_so_gamma.py` cần thêm numpy (`pip install numpy`).

```bash
cd golden
python3 tests/test_golden.py        # chạy kiểm thử
python3 tao_vector_v1.py            # tạo vectors/v1_mac_dinh/
python3 tao_vector_v1.py --K 2560 --so-hang 64 --S 8 --ten v1_lon
python3 tao_vector_bien.py          # tạo 6 bộ vector biên vectors/bien_*/
python3 tao_vector_v2.py            # tạo vectors/v2a_*, v2b_* và bản v1 đối chiếu
python3 tao_vector_v1b.py           # tạo vectors/v1b_* và bản v1 đối chiếu
python3 so_sanh_phien_ban.py        # bảng so sánh v1, v1b, v2b, v2a
python3 tao_vector_768.py           # bộ 768 x 768 cho cả 4 phiên bản
python3 mo_hinh_hieu_nang.py --kiem-tra   # mô hình hiệu năng
```

## Tiến độ

| Giai đoạn | Nội dung | Trạng thái |
|---|---|---|
| 1 | Đặc tả mức bit, golden model v1 | Xong |
| 1 | Bộ test biên (v1) | Xong |
| 1 | Golden model v2a/v2b | Xong |
| 1 | Kẹp ±127, thêm v1b (kiểu TQ1_0) | Xong |
| 1 | Đo sai số khi làm tròn gamma về 2^-S (dữ liệu mô phỏng) | Xong, cần đo lại với dữ liệu thật |
| 1 | Đệm hàng, beat Y, khung vào, gián đoạn, thanh ghi, mã lỗi | Xong |
| 1 | Mô hình hiệu năng, quy tắc RTL, kế hoạch đánh giá, bộ 768 x 768 | Xong |
| 1 | Phạm vi IP, quy tắc ghi số liệu, mở rộng T token (đặc tả) | Xong; RTL T > 1 để sau |
| 2 | Khối chuẩn hoá requant.v + testbench (3031/3031 khớp) | Xong |
| 2 | Khối giải mã w_decode_v1.v + testbench (2809/2809 khớp, lint sạch, thử phá đạt) | Xong |
| 2 | Các khối còn lại của RTL v1 (lane, x_buffer, top), đóng timing 100 MHz | Đang làm |

### Tài nguyên từng khối (ước lượng sơ bộ bằng Yosys, Xilinx 7-series; số chính thức lấy từ Vivado)

| Khối | LUT | CARRY4 | FF | DSP |
|---|---|---|---|---|
| requant | 131 | 13 | 9 | 0 |
| w_decode_v1 | 713 | 0 | 0 | 0 |

`w_decode_v1` đứng riêng tốn 512 LUT cho khac_0/am; khi ghép với làn, Vivado thường gộp phần này vào mạch chọn ±X/0 của làn.
| 3 | RTL v2a, v2b | Chưa |
| 4 | Tích hợp trên board | Chưa |
| 5 | Ablation study, báo cáo | Chưa |
