# Bước 5: mã hoá W v1 (2 bit / trọng số) thành beat 512 bit
# Quy ước (đặc tả mức bit):
#   Mã: 0 -> 00, +1 -> 01, -1 -> 10   (11 không dùng)
#   bit [128*r + 2*c + 1 : 128*r + 2*c] = W[hàng r][cột c]   (r = 0..3, c = 0..63)
#   -> hàng 0 ở 128 bit thấp nhất, cột 0 ở 2 bit thấp nhất của hàng
import random

MA = {0: 0b00, +1: 0b01, -1: 0b10}        # trọng số -> mã 2 bit
GIAI = {0b00: 0, 0b01: +1, 0b10: -1}      # mã 2 bit -> trọng số


def ma_hoa_w(cac_hang, so_cot):
    # cac_hang: danh sách các khúc hàng (mỗi khúc so_cot trọng số)
    beat = 0
    for r in range(len(cac_hang)):
        for c in range(so_cot):
            vi_tri = (so_cot * 2) * r + 2 * c          # bit bắt đầu của W[r][c]
            beat = beat | (MA[cac_hang[r][c]] << vi_tri)
    return beat


def giai_ma_w(beat, so_hang, so_cot):
    cac_hang = []
    for r in range(so_hang):
        hang = []
        for c in range(so_cot):
            vi_tri = (so_cot * 2) * r + 2 * c
            ma = (beat >> vi_tri) & 0b11                 # lấy 2 bit
            if ma == 0b11:
                raise ValueError(f"Mã 11 không hợp lệ ở hàng {r}, cột {c}")
            hang.append(GIAI[ma])
        cac_hang.append(hang)
    return cac_hang


# ---- Phần A: 1 hàng, 4 trọng số (8 bit) ----
print("=== Phần A: 1 hàng 4 trọng số -> 8 bit ===")
hang_a = [+1, 0, -1, -1]
for c, w in enumerate(hang_a):
    print(f"  W[{c}] = {w:+d}  ->  mã {MA[w]:02b}")
beat_a = ma_hoa_w([hang_a], 4)
print(f"  Beat (nhị phân): {beat_a:08b}")
print("                   W3W2W1W0")
print("  Giải mã lại    :", giai_ma_w(beat_a, 1, 4))

# ---- Phần B: 2 hàng, mỗi hàng 4 trọng số (16 bit) ----
print()
print("=== Phần B: 2 hàng x 4 trọng số -> 16 bit ===")
hai_hang = [[+1, 0, -1, -1],      # hàng 0
            [0, +1, +1, -1]]      # hàng 1
beat_b = ma_hoa_w(hai_hang, 4)
print(f"  Beat (nhị phân): {beat_b:016b}")
print("                   |-hàng 1-||-hàng 0-|")
print("  Giải mã lại    :", giai_ma_w(beat_b, 2, 4))

# ---- Phần C: beat thật, 4 hàng x 64 trọng số = 512 bit ----
print()
print("=== Phần C: 4 hàng x 64 trọng số -> beat 512 bit ===")
random.seed(1)
bon_hang = [[random.choice([-1, 0, 1]) for _ in range(64)] for _ in range(4)]
beat_c = ma_hoa_w(bon_hang, 64)
hex_c = f"{beat_c:0128X}"
print("  4 trọng số đầu của hàng 0:", bon_hang[0][:4])
print("  Beat hex (128 ký tự):")
print("  " + hex_c)
print("  Ký tự hex CUỐI cùng (= W[0][1], W[0][0]):", hex_c[-1])
print("  Giải mã lại có khớp không?", giai_ma_w(beat_c, 4, 64) == bon_hang)
