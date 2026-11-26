# Bước 2: chuẩn hoá Acc về INT8 đối xứng (từ -127 đến 127), không dùng phép nhân
# Công thức: Y = Kẹp( (Acc + 2^(S-1)) >> S , -127, 127 )

def chuan_hoa(acc, S):
    lam_tron = 1 << (S - 1)          # 2^(S-1): một nửa của 2^S (S=4 -> 8)
    y = (acc + lam_tron) >> S        # dịch phải S bit = chia cho 2^S, giữ dấu âm
    if y > 127:                      # kẹp: quá lớn thì giữ 127
        y = 127
    if y < -127:                     # kẹp: quá nhỏ thì giữ -127 (không dùng -128)
        y = -127
    return y

S = 4   # chia cho 2^4 = 16

cac_acc = [-128, 1000, -1000, 5000, -5000, 24, 40, 8]

print(f"S = {S}, tức chia cho {1 << S}")
print()
print(f"{'Acc':>7} | {'chia thật':>9} | {'chỉ dịch (cắt)':>14} | {'Y (làm tròn + kẹp)':>18}")
print("-" * 60)
for acc in cac_acc:
    chia_that = acc / (1 << S)       # phép chia số thực, chỉ để so sánh
    chi_dich = acc >> S              # dịch bit nhưng không cộng làm tròn
    y = chuan_hoa(acc, S)
    print(f"{acc:>7} | {chia_that:>9.2f} | {chi_dich:>14} | {y:>18}")
