# Bước 1: tính 1 hàng W × X bằng cộng/trừ (không dùng phép nhân)
# Dữ liệu nhỏ: X có 8 số, W có 1 hàng 8 trọng số

X = [10, 20, 5, 7, -3, 100, -127, 0]   # mỗi số là INT8, nhưng chỉ dùng -127..127 (không dùng -128)
W = [+1, -1, 0, +1, -1, 0, +1, 0]      # mỗi trọng số là -1, 0 hoặc +1

acc = 0
for j in range(len(X)):
    if W[j] == +1:
        acc = acc + X[j]
        viec = f"cộng {X[j]}"
    elif W[j] == -1:
        acc = acc - X[j]
        viec = f"trừ  {X[j]}"
    else:
        viec = "bỏ qua"
    print(f"vị trí {j}: W={W[j]:+d}, X={X[j]:5d} -> {viec:12s} | Acc = {acc}")

print()
print("Kết quả cộng/trừ   :", acc)

# Kiểm tra lại bằng phép nhân thông thường: phải ra giống hệt
acc_nhan = sum(W[j] * X[j] for j in range(len(X)))
print("Kiểm tra bằng nhân :", acc_nhan)
print("Khớp?              :", acc == acc_nhan)
