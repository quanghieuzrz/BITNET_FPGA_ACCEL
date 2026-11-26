# Bước 3: tính nhiều hàng W × X, chia X thành khúc 64 số, tính theo nhóm 4 hàng (giống v1)
import random

random.seed(1)          # cố định bộ sinh số ngẫu nhiên: chạy lần nào cũng ra cùng dữ liệu

K = 128                 # X dài 128 số  -> 128 / 64 = 2 khúc
SO_HANG = 8             # W có 8 hàng   -> 8 / 4 = 2 nhóm hàng
KHUC = 64               # mỗi khúc 64 số (= 1 beat X)
LAN = 4                 # v1: 4 làn, mỗi nhịp tính 4 hàng
S = 6                   # chuẩn hoá: chia cho 2^6 = 64


def chuan_hoa(acc, S):
    y = (acc + (1 << (S - 1))) >> S
    if y > 127:
        y = 127
    if y < -127:
        y = -127
    return y


def cong_tru(w_khuc, x_khuc):
    # Việc của MỘT làn trong một nhịp: cộng/trừ 64 cặp, không nhân
    tong = 0
    for j in range(len(x_khuc)):
        if w_khuc[j] == 1:
            tong += x_khuc[j]
        elif w_khuc[j] == -1:
            tong -= x_khuc[j]
    return tong


# ---- Tạo dữ liệu ngẫu nhiên ----
X = [random.randint(-127, 127) for _ in range(K)]
W = [[random.choice([-1, 0, 1]) for _ in range(K)] for _ in range(SO_HANG)]

# ---- Tính theo thứ tự của chip ----
Y = [0] * SO_HANG
nhip = 0
for nhom in range(0, SO_HANG, LAN):                 # nhóm hàng: 0-3, rồi 4-7
    acc = [0] * LAN                                 # mỗi làn 1 thanh ghi Acc, xoá về 0
    for k in range(0, K, KHUC):                     # khúc X: 0-63, rồi 64-127
        x_khuc = X[k:k + KHUC]                      # lấy khúc X (sẽ chép ra các làn)
        for lan in range(LAN):                      # 4 làn chạy song song (Python làm lần lượt)
            hang = nhom + lan
            w_khuc = W[hang][k:k + KHUC]            # khúc tương ứng của hàng đó
            acc[lan] += cong_tru(w_khuc, x_khuc)    # cộng dồn vào Acc của làn
        nhip += 1
        print(f"Nhịp {nhip}: hàng {nhom}-{nhom + LAN - 1}, khúc X {k}-{k + KHUC - 1} -> Acc = {acc}")
    for lan in range(LAN):                          # hết các khúc -> chuẩn hoá
        Y[nhom + lan] = chuan_hoa(acc[lan], S)
    print(f"   Xong nhóm hàng {nhom}-{nhom + LAN - 1}: Y = {Y[nhom:nhom + LAN]}")
    print()

# ---- Kiểm tra: tính thẳng cả hàng bằng phép nhân, không chia khúc ----
Y_kiem_tra = []
for hang in range(SO_HANG):
    acc_thang = sum(W[hang][j] * X[j] for j in range(K))
    Y_kiem_tra.append(chuan_hoa(acc_thang, S))

print("Y theo cách chip   :", Y)
print("Y tính thẳng (nhân):", Y_kiem_tra)
print("Khớp?              :", Y == Y_kiem_tra)
