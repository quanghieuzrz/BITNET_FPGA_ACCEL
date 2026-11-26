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

