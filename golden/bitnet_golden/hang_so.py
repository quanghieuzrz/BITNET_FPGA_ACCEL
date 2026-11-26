"""Tham số dùng chung. Mọi quy ước ở đây phải khớp docs/dac_ta_muc_bit.md."""

BEAT_BIT = 512            # độ rộng bus AXI4-Stream
X_BIT = 8                 # mỗi số X là INT8
KHUC = BEAT_BIT // X_BIT  # 64 số X / beat = độ dài một khúc hàng W

ACC_BIT = 24              # độ rộng bộ tích luỹ (có dấu)

# X và Y dùng khoảng ĐỐI XỨNG [-127, 127] (như BitNet b1.58 và PENSA):
# -128 bị cấm, vì đổi dấu -(-128) = +128 không vừa INT8.
INT8_MIN = -127
INT8_MAX = 127

# W v1: 2 bit / trọng số
W_V1_BIT = 2
LAN_V1 = BEAT_BIT // (KHUC * W_V1_BIT)   # 4 hàng / beat
MA_W_V1 = {0: 0b00, +1: 0b01, -1: 0b10}  # 0b11 bị cấm
GIAI_W_V1 = {0b00: 0, 0b01: +1, 0b10: -1}

# W v1b (kiểu TQ1_0): gói hệ 3, 5 trọng số / byte
TQ_MOI_BYTE = 5                           # 3^5 = 243 <= 256
TQ_SO_MA = 3 ** TQ_MOI_BYTE               # 243 mã hợp lệ (0..242); 243..255 bị cấm
LAN_V1B = (BEAT_BIT // 8) * TQ_MOI_BYTE // KHUC   # 64 byte x 5 / 64 = 5 hàng / beat

# W v2: nén 2:4, mỗi nhóm 4 trọng số liên tiếp
NHOM = 4
SO_NHOM = KHUC // NHOM                    # 16 nhóm / khúc hàng
W_V2A_BIT_NHOM = 5                        # 3 bit vị trí + 2 bit dấu
W_V2B_BIT_NHOM = 6                        # thêm 1 bit chế độ
LAN_V2A = BEAT_BIT // (SO_NHOM * W_V2A_BIT_NHOM)   # 512 // 80 = 6 hàng / beat
LAN_V2B = BEAT_BIT // (SO_NHOM * W_V2B_BIT_NHOM)   # 512 // 96 = 5 hàng / beat

# Mã vị trí 3 bit -> cặp vị trí khác 0 trong nhóm (chỉ số trong danh sách = mã)
CAP_VI_TRI = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]   # 110, 111 bị cấm

# ---- Phiên bản đóng gói W (dùng chung cho đệm hàng, thanh ghi MODE, mô hình hiệu năng) ----
SO_LAN = {"v1": LAN_V1, "v1b": LAN_V1B, "v2a": LAN_V2A, "v2b": LAN_V2B}   # R = số hàng / beat W
MA_CHE_DO = {"v1": 0, "v1b": 1, "v2a": 2, "v2b": 3}                       # giá trị thanh ghi MODE

# ---- Giới hạn phần cứng ----
K_TOI_DA = 6912          # BRAM chứa X: 6912 byte (hàng dài nhất của BitNet 2B, lớp Down)
N_TOI_DA = 65535         # thanh ghi N 16 bit (lm_head 128256 hàng không chạy trên chip)
S_MIN, S_MAX = 1, ACC_BIT - 1
T_TOI_DA = 8             # số token tối đa mỗi lượt (dùng chung 1 beat W): BRAM X = T x 6912 byte = 54 KB
