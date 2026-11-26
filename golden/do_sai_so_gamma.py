"""Đo sai số khi làm tròn hệ số chuẩn hoá gamma về lũy thừa của 2 (gamma = 2^-S).

Ý tưởng
-------
Trong BitNet, đầu ra của lớp được lượng tử hoá về INT8 theo từng token (absmax):
    Y_q = round(Acc * gamma),   gamma = 127 / max|Acc|      (gamma khác nhau cho mỗi token)

Chip của mình muốn bỏ phép nhân, nên thay gamma bằng 2^-S (chỉ dịch bit).
Thí nghiệm so 4 cách chuẩn hoá (2 x 2):

                         gamma chính xác (cần nhân)     gamma = 2^-S (chỉ dịch)
    tính theo token      A. BitNet gốc (chuẩn)          B. S tính lúc chạy
    cố định theo lớp     C. gamma tĩnh                  D. S tĩnh (thiết kế hiện tại)

Thước đo (trên các token kiểm tra, không dùng để hiệu chỉnh):
    SNR (dB)   : Acc được biểu diễn lại chính xác tới đâu. Cao hơn = tốt hơn; mỗi 6 dB ~ 1 bit.
    % bị kẹp   : tỉ lệ giá trị Y bị kẹp ở 127 / -127.
    Mức dùng   : |Y| lớn nhất trung bình mỗi token (127 = dùng hết khoảng INT8).

Dữ liệu: MÔ PHỎNG (Hugging Face không truy cập được lúc viết). Phân bố gần mô hình thật:
    W ~ chuẩn, lượng tử absmean ra ternary;  X ~ đuôi dày (Student-t) + vài kênh ngoại lai.

Cách chạy (đứng ở thư mục golden/, cần numpy):
    python3 do_sai_so_gamma.py
    python3 do_sai_so_gamma.py --K 6912 --N 2560 --token 64
"""
import argparse

import numpy as np


def luong_tu_w(W):
    beta = np.mean(np.abs(W))
    return np.clip(np.round(W / beta), -1, 1).astype(np.int64)


def luong_tu_x(X):
    """Lượng tử INT8 theo từng token (cột), absmax."""
    s = 127.0 / np.max(np.abs(X), axis=0, keepdims=True)
    return np.clip(np.round(X * s), -127, 127).astype(np.int64)


def chuan_hoa_nhan(acc, gamma):
    """Cách có phép nhân: round(Acc * gamma) rồi kẹp."""
    return np.clip(np.floor(acc * gamma + 0.5), -127, 127)


def chuan_hoa_dich(acc, S):
    """Cách của chip: (Acc + 2^(S-1)) >> S rồi kẹp. S có thể là mảng (mỗi token một S)."""
    S = np.asarray(S, dtype=np.int64)
    return np.clip((acc + (np.int64(1) << (S - 1))) >> S, -127, 127)


def danh_gia(acc, Y, gamma):
    """So Acc gốc với Acc dựng lại từ Y (= Y / gamma)."""
    acc_lai = Y / gamma
    snr = 10 * np.log10(np.sum(acc.astype(float) ** 2) / np.sum((acc - acc_lai) ** 2))
    bi_kep = np.mean((Y == 127) | (Y == -127)) * 100
    muc_dung = np.mean(np.max(np.abs(Y), axis=0))
    return snr, bi_kep, muc_dung


CAC_CACH = ["A. gamma chính xác, theo token (gốc)",
            "B. 2^-S, tính S lúc chạy",
            "C. gamma chính xác, tĩnh",
            "D. 2^-S tĩnh, làm tròn gần nhất",
            "E. 2^-S tĩnh, chọn an toàn"]


def chay_mot_lan(K, N, so_token, seed):
    """Trả về {tên cách: (SNR, % bị kẹp, mức dùng)} và vài thông tin phụ."""
    rng = np.random.default_rng(seed)

    # ---- Dữ liệu mô phỏng ----
    W = luong_tu_w(rng.normal(0, 0.02, size=(N, K)))
    X = rng.standard_t(df=4, size=(K, so_token))
    kenh_ngoai_lai = rng.choice(K, size=K // 200, replace=False)
    X[kenh_ngoai_lai] *= 8.0                                   # vài kênh rất lớn, như LLM thật
    X = X * rng.uniform(0.5, 2.0, size=(1, so_token))          # mỗi token một độ lớn khác nhau
    Xq = luong_tu_x(X)

    ACC = W @ Xq                                               # Acc nguyên, mỗi cột một token
    so_hc = so_token // 2
    acc_hc, acc_kt = ACC[:, :so_hc], ACC[:, so_hc:]            # hiệu chỉnh / kiểm tra

    max_kt = np.max(np.abs(acc_kt), axis=0)
    max_hc = np.max(np.abs(acc_hc), axis=0)

    # A. BitNet gốc: gamma chính xác, theo từng token
    gA = 127.0 / max_kt
    YA = chuan_hoa_nhan(acc_kt, gA)

    # B. S tính lúc chạy: nhỏ nhất sao cho max|Acc| / 2^S <= 127 (không bao giờ kẹp)
    SB = np.maximum(1, np.ceil(np.log2(max_kt / 127.0))).astype(np.int64)
    YB = chuan_hoa_dich(acc_kt, SB)
    gB = 2.0 ** -SB

    # C. gamma tĩnh: lấy trung vị trên token hiệu chỉnh, dùng cho mọi token
    gC = np.median(127.0 / max_hc)
    YC = chuan_hoa_nhan(acc_kt, gC)

    # D. S tĩnh: làm tròn gamma tĩnh về lũy thừa 2 GẦN NHẤT (có thể lên hoặc xuống)
    SD = int(np.round(-np.log2(gC)))
    YD = chuan_hoa_dich(acc_kt, SD)
    gD = 2.0 ** -SD

    # E. S tĩnh chọn AN TOÀN: đủ lớn để token có max|Acc| lớn nhất lúc hiệu chỉnh vẫn không bị kẹp
    SE = int(max(1, np.ceil(np.log2(max_hc.max() / 127.0))))
    YE = chuan_hoa_dich(acc_kt, SE)
    gE = 2.0 ** -SE

    ket_qua = {}
    for ten, Y, g in zip(CAC_CACH, [YA, YB, YC, YD, YE], [gA, gB, gC, gD, gE]):
        ket_qua[ten] = danh_gia(acc_kt, Y, g)
    phu = dict(max_min=max_kt.min(), max_max=max_kt.max(), gC=gC, SD=SD, SE=SE,
               SB_min=SB.min(), SB_max=SB.max())
    return ket_qua, phu


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--K", type=int, default=2560, help="độ dài X (cột của W)")
    p.add_argument("--N", type=int, default=2560, help="số hàng W (số Y)")
    p.add_argument("--token", type=int, default=64, help="số token (nửa hiệu chỉnh, nửa kiểm tra)")
    p.add_argument("--lap", type=int, default=10, help="số lần chạy với seed khác nhau")
    a = p.parse_args()

    tat_ca = {ten: [] for ten in CAC_CACH}
    for seed in range(a.lap):
        ket_qua, phu = chay_mot_lan(a.K, a.N, a.token, seed)
        for ten in CAC_CACH:
            tat_ca[ten].append(ket_qua[ten])
        if seed == 0:
            print(f"Lớp BitLinear mô phỏng: {a.N} hàng x K = {a.K}, {a.token} token mỗi lần, {a.lap} lần")
            print(f"Ví dụ lần 1: max|Acc| theo token từ {phu['max_min']:.0f} đến {phu['max_max']:.0f}; "
                  f"gamma tĩnh = {phu['gC']:.4f} -> S gần nhất = {phu['SD']}, S an toàn = {phu['SE']}; "
                  f"S lúc chạy từ {phu['SB_min']} đến {phu['SB_max']}")
    print()
    print(f"{'Cách':<38} {'SNR trung bình (thấp-cao) dB':>30} {'% bị kẹp TB':>12}")
    print("-" * 82)
    for ten in CAC_CACH:
        mang = np.array(tat_ca[ten])
        snr = mang[:, 0]
        print(f"{ten:<38} {snr.mean():12.1f} ({snr.min():5.1f} - {snr.max():5.1f})"
              f" {mang[:, 1].mean():12.2f}")


if __name__ == "__main__":
    main()
