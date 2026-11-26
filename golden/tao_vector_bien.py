"""Bước 7: tạo các bộ vector BIÊN cho v1 — những trường hợp dữ liệu ngẫu nhiên hiếm khi gặp.

Cách chạy (đứng ở thư mục golden/):
    python3 tao_vector_bien.py

Mỗi trường hợp ghi vào ../vectors/bien_<ten>/ (x_in.hex, w_in.hex, y_expected.hex, config.txt).
Mỗi bộ có đúng 4 hàng W (= 1 nhóm v1), nên cho ra 4 số Y.
"""
import os

from bitnet_golden.bo_vector import ghi_bo_vector_v1

GOC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "vectors")


# ---------- Hàm phụ tạo hàng W ----------
def lap_mau(K, mau):
    """Lặp mẫu cho đủ K trọng số: lap_mau(6, [+1, -1]) = [+1, -1, +1, -1, +1, -1]."""
    return [mau[j % len(mau)] for j in range(K)]


def dat_vi_tri(K, cac_vi_tri):
    """Hàng toàn 0, chỉ đặt giá trị ở vài vị trí: dat_vi_tri(4, {1: -1}) = [0, -1, 0, 0]."""
    w = [0] * K
    for vi_tri, gia_tri in cac_vi_tri.items():
        w[vi_tri] = gia_tri
    return w


# ---------- Các trường hợp: mỗi hàm trả về (tên, X, W, S, ghi chú) ----------
def th_acc_cuc_dai():
    # Hàng dài nhất 6912, X toàn -127: Acc lớn nhất có thể. Kiểm tra Acc 24 bit không tràn.
    K = 6912
    X = [-127] * K
    W = [lap_mau(K, [-1]),        # (-1)(-127) x 6912 = +877824 -> kẹp 127
         lap_mau(K, [+1]),        # (+1)(-127) x 6912 = -877824 -> kẹp -127
         lap_mau(K, [0]),         # toàn 0 -> 0
         lap_mau(K, [+1, -1])]    # xen kẽ, triệt tiêu -> 0
    return "acc_cuc_dai", X, W, 6, "Acc = +877824, -877824, 0, 0 -> Y = 127, -127, 0, 0"


def th_x_toan_127():
    # X toàn số dương lớn nhất.
    K = 128
    X = [127] * K
    W = [lap_mau(K, [+1]),        # +16256
         lap_mau(K, [-1]),        # -16256
         lap_mau(K, [+1, 0]),     # +8128
         lap_mau(K, [0, -1])]     # -8128
    return "x_toan_127", X, W, 4, "Acc = +/-16256, +/-8128, deu bi kep"


def th_moc_nua():
    # Acc nằm đúng mốc .5 sau khi chia (S = 2, chia 4). Quy ước: .5 làm tròn LÊN.
    K = 64
    X = [2, 6] + [0] * (K - 2)
    W = [dat_vi_tri(K, {0: +1}),  # Acc =  2 ->  0.5 ->  1
         dat_vi_tri(K, {0: -1}),  # Acc = -2 -> -0.5 ->  0
         dat_vi_tri(K, {1: +1}),  # Acc =  6 ->  1.5 ->  2
         dat_vi_tri(K, {1: -1})]  # Acc = -6 -> -1.5 -> -1
    return "moc_nua", X, W, 2, "Acc = 2, -2, 6, -6 -> Y = 1, 0, 2, -1"


def th_moc_kep():
    # Y vừa chạm biên (không kẹp) và vừa vượt biên (bị kẹp). S = 1 (chia 2). Biên là +/-127.
    K = 64
    X = [127, 127, 1, 1, -127, -127, -1, -1] + [0] * (K - 8)
    W = [dat_vi_tri(K, {0: +1, 1: +1}),                  # Acc =  254 -> (254+1)>>1 =  127 (chạm, không kẹp)
         dat_vi_tri(K, {0: +1, 1: +1, 2: +1, 3: +1}),    # Acc =  256 ->  128 -> kẹp  127
         dat_vi_tri(K, {4: +1, 5: +1}),                  # Acc = -254 -> (-253)>>1 = -127 (chạm, không kẹp)
         dat_vi_tri(K, {4: +1, 5: +1, 6: +1, 7: +1})]    # Acc = -256 -> (-255)>>1 = -128 -> kẹp -127
    return "moc_kep", X, W, 1, "Acc = 254, 256, -254, -256 -> Y = 127, 127, -127, -127"


def th_tru_so_am():
    # Trừ số âm, cộng số âm: chỗ dễ sai dấu trong RTL.
    K = 64
    X = [-100, -50, 30, -1] + [0] * (K - 4)
    W = [dat_vi_tri(K, {0: -1}),                         # -(-100) = +100
         dat_vi_tri(K, {0: +1}),                         # +(-100) = -100
         dat_vi_tri(K, {0: -1, 1: -1, 2: -1, 3: -1}),    # 100 + 50 - 30 + 1 = 121
         dat_vi_tri(K, {3: -1})]                         # -(-1) = +1
    return "tru_so_am", X, W, 1, "Acc = 100, -100, 121, 1 -> Y = 50, -50, 61, 1"


def th_vi_tri_bit():
    # Mỗi hàng chỉ có một trọng số ở cột biên: đầu khúc 1, cuối khúc 1, đầu khúc 2, cuối khúc 2.
    # X[c] = c - 64 để mỗi cột cho một giá trị khác nhau -> lệch vị trí là lộ ngay.
    K = 128
    X = [c - 64 for c in range(K)]          # X[0] = -64, X[63] = -1, X[64] = 0, X[127] = 63
    W = [dat_vi_tri(K, {0: +1}),            # X[0]    = -64
         dat_vi_tri(K, {63: -1}),           # -X[63]  =   1
         dat_vi_tri(K, {64: +1, 65: +1}),   # X[64] + X[65] = 0 + 1 = 1
         dat_vi_tri(K, {127: -1})]          # -X[127] = -63
    return "vi_tri_bit", X, W, 1, "Kiem tra cot 0, 63, 64, 65, 127 nam dung cho trong beat"


CAC_TRUONG_HOP = [th_acc_cuc_dai, th_x_toan_127, th_moc_nua, th_moc_kep, th_tru_so_am, th_vi_tri_bit]


def main():
    print(f"{'Bộ vector':<20} {'K':>5} {'S':>2}  Y")
    print("-" * 64)
    for ham in CAC_TRUONG_HOP:
        ten, X, W, S, ghi_chu = ham()
        Y = ghi_bo_vector_v1(os.path.join(GOC, f"bien_{ten}"), X, W, S, ghi_chu)
        print(f"bien_{ten:<15} {len(X):>5} {S:>2}  {Y}")
        print(f"{'':<29}({ghi_chu})")


if __name__ == "__main__":
    main()
