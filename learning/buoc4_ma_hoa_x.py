# Bước 4: mã hoá X thành beat 512 bit
# Quy ước (đặc tả mức bit): bit [8c+7 : 8c] = X[c]
#   -> X[0] nằm ở 8 bit THẤP NHẤT (bên phải), X[63] ở 8 bit CAO NHẤT (bên trái)
# X là INT8 ĐỐI XỨNG: chỉ dùng -127..127. Mẫu 0x80 (-128) bị cấm,
#   vì làn phải tính -X mà -(-128) = +128 không vừa 8 bit.
import random

X_MIN, X_MAX = -127, 127


def so_sang_byte(x):
    # Đổi số có dấu (-127..127) sang 8 bit theo kiểu bù hai (0..255)
    if not (X_MIN <= x <= X_MAX):
        raise ValueError(f"X = {x} nằm ngoài -127..127 (cấm -128)")
    return x & 0xFF


def byte_sang_so(b):
    # Đổi ngược 8 bit (0..255) về số có dấu
    if b == 0x80:
        raise ValueError("Gặp byte 0x80 (-128): mẫu bị cấm")
    if b >= 128:            # bit trái nhất = 1 -> số âm
        return b - 256
    return b


def ma_hoa_x(x_khuc):
    # Ghép các số X thành MỘT số nguyên lớn (beat)
    beat = 0
    for c in range(len(x_khuc)):
        beat = beat | (so_sang_byte(x_khuc[c]) << (8 * c))   # đặt X[c] vào bit 8c..8c+7
    return beat


def giai_ma_x(beat, so_luong):
    # Tách beat ngược lại thành các số X
    x_khuc = []
    for c in range(so_luong):
        b = (beat >> (8 * c)) & 0xFF                           # lấy 8 bit ở vị trí 8c
        x_khuc.append(byte_sang_so(b))
    return x_khuc


# ---- Phần A: ví dụ nhỏ, 4 số (beat 32 bit) để dễ nhìn ----
print("=== Phần A: 4 số X -> beat 32 bit ===")
x_nho = [10, -1, 127, -127]
for x in x_nho:
    print(f"  X = {x:5d}  ->  8 bit: {so_sang_byte(x):08b}  (hex {so_sang_byte(x):02X})")

beat_nho = ma_hoa_x(x_nho)
hex_nho = f"{beat_nho:08X}"
print()
print("  X =", x_nho)
print(f"  Beat (nhị phân): {beat_nho:032b}")
print("  Beat (hex)     :", " ".join(hex_nho[i:i + 2] for i in range(0, 8, 2)))
print("                   X3 X2 X1 X0      <- đọc từ PHẢI sang TRÁI")
print("  Giải mã lại    :", giai_ma_x(beat_nho, 4))

# ---- Phần B: beat thật, 64 số = 512 bit ----
print()
print("=== Phần B: 64 số X -> beat 512 bit ===")
random.seed(1)
x_khuc = [random.randint(X_MIN, X_MAX) for _ in range(64)]
beat = ma_hoa_x(x_khuc)
hex_str = f"{beat:0128X}"                     # 512 bit = 128 ký tự hex
print("  8 số X đầu:", x_khuc[:8])
print("  Beat hex (128 ký tự):")
print("  " + hex_str)
print("  Số ký tự hex:", len(hex_str))
cuoi = hex_str[-16:]
print("  16 ký tự CUỐI = X[7]..X[0]:", " ".join(cuoi[i:i + 2] for i in range(0, 16, 2)))
print("  Giải mã lại có khớp không?", giai_ma_x(beat, 64) == x_khuc)

# ---- Phần C: thử đưa -128 vào -> phải bị từ chối ----
print()
print("=== Phần C: thử X = -128 ===")
try:
    ma_hoa_x([5, -128])
except ValueError as loi:
    print("  Bị từ chối đúng như đặc tả:", loi)
