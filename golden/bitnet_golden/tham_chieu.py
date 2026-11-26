"""Tính đáp án Y theo hai cách:

- tinh_y_thang : nhân thẳng cả hàng (đơn giản nhất, dùng làm đáp án)
- tinh_y_theo_chip : chia khúc 64, chia nhóm làn, cộng dồn (mô phỏng thứ tự của chip)

Hai cách phải ra cùng kết quả.
"""
from .hang_so import KHUC
from .chuan_hoa import chuan_hoa, kiem_tra_acc


def tinh_acc_thang(W, X):
    return [sum(w * x for w, x in zip(hang, X)) for hang in W]


def tinh_y_thang(W, X, S):
    return [chuan_hoa(acc, S) for acc in tinh_acc_thang(W, X)]


def tinh_y_theo_chip(W, X, S, so_lan, hang_gia=None):
    """Mô phỏng thứ tự tính của chip. Nếu số hàng không chia hết cho so_lan thì đệm hàng giả
    (mặc định toàn 0; truyền hang_gia để dùng mẫu khác, vd mẫu v2a) rồi BỎ Y của hàng giả."""
    N, K = len(W), len(X)
    if K % KHUC != 0:
        raise ValueError(f"K = {K} phải chia hết cho {KHUC}")
    thieu = (-N) % so_lan
    W = W + [hang_gia if hang_gia is not None else [0] * K] * thieu
    so_hang = len(W)
    Y = [0] * so_hang
    for nhom in range(0, so_hang, so_lan):
        acc = [0] * so_lan
        for k in range(0, K, KHUC):
            x_khuc = X[k:k + KHUC]
            for lan in range(so_lan):
                w_khuc = W[nhom + lan][k:k + KHUC]
                for w, x in zip(w_khuc, x_khuc):
                    if w == 1:
                        acc[lan] += x
                    elif w == -1:
                        acc[lan] -= x
                kiem_tra_acc(acc[lan])
        for lan in range(so_lan):
            Y[nhom + lan] = chuan_hoa(acc[lan], S)
    return Y[:N]                                   # bỏ đầu ra của hàng giả
