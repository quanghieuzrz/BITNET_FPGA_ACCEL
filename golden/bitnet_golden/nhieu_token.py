"""Mở rộng: DÙNG CHUNG MỘT BEAT W CHO T TOKEN (tái sử dụng trọng số).

Vì sao: trên Arty A7, DDR3L chỉ cấp ~13 byte/nhịp trong khi một beat W là 64 byte, nên các làn ngồi chờ
~79 % thời gian. Nếu trong BRAM có sẵn X của T token, mỗi beat W vừa đến được GIỮ LẠI T nhịp và dùng cho
lần lượt từng token -> cùng lượng trọng số kéo từ RAM, làm được T lần việc. Trọng số là thứ đắt (băng thông),
X là thứ rẻ (nằm sẵn trên chip).

Dùng được khi có nhiều token cùng chờ một lớp: pha prefill (đọc câu hỏi), mô hình encoder / không tự hồi quy
(một lượt suy luận cho cả chuỗi), hoặc gộp nhiều yêu cầu (batch). KHÔNG giúp pha decode của MỘT người dùng
(mỗi lúc chỉ có 1 token mới).

Quy ước (đặc tả mục 11):
  Khung vào : X token 0 (K/64 beat), X token 1, ..., X token T-1, rồi các beat W như khi T = 1.
  Tính     : mỗi beat W (nhóm g, khúc k) được dùng T nhịp: nhịp t cộng vào Acc[t][làn] với khúc X thứ k của token t.
  Ra       : với mỗi khối 64 hàng b = 0, 1, ...: beat Y khối b của token 0, của token 1, ..., của token T-1.
"""
from .hang_so import KHUC, SO_LAN
from .chuan_hoa import chuan_hoa, kiem_tra_acc
from .dem_hang import dem_hang, so_nhom_hang
from .ma_hoa_x import ma_hoa_x
from .ma_hoa_y import dong_goi_y
from .tham_chieu import tinh_y_thang


def khung_x(cac_X):
    """Các beat X của T token, token-trước (token 0 hết rồi mới tới token 1)."""
    return [ma_hoa_x(X[k:k + KHUC]) for X in cac_X for k in range(0, len(X), KHUC)]


def thu_tu_beat_y(cac_Y):
    """Sắp các beat Y theo quy ước: khối 64 hàng trước, trong khối thì token 0 -> T-1."""
    theo_token = [dong_goi_y(Y) for Y in cac_Y]
    return [theo_token[t][b] for b in range(len(theo_token[0])) for t in range(len(cac_Y))]


def tach_beat_y(cac_beat, T):
    """Ngược lại: beat thứ i thuộc token i % T."""
    return [cac_beat[t::T] for t in range(T)]


def tinh_theo_chip(cac_X, W, S, phien_ban):
    """Mô phỏng thứ tự tính khi T > 1 và đếm nhịp tính (băng thông lý tưởng).
    Trả về (danh sách Y theo token, số nhịp dùng làn)."""
    T, K, N = len(cac_X), len(cac_X[0]), len(W)
    R = SO_LAN[phien_ban]
    Wd = dem_hang(W, phien_ban)
    cac_Y = [[] for _ in range(T)]
    nhip = 0
    for g in range(so_nhom_hang(N, R)):
        acc = [[0] * R for _ in range(T)]
        for k in range(K // KHUC):
            beat_w = [Wd[g * R + lan][k * KHUC:(k + 1) * KHUC] for lan in range(R)]   # nhận 1 beat W
            for t in range(T):                                                        # giữ beat T nhịp
                nhip += 1
                x = cac_X[t][k * KHUC:(k + 1) * KHUC]
                for lan in range(R):
                    acc[t][lan] += sum(xi if w == 1 else (-xi if w == -1 else 0) for w, xi in zip(beat_w[lan], x))
                    kiem_tra_acc(acc[t][lan])
        for t in range(T):
            for lan in range(R):
                if g * R + lan < N:
                    cac_Y[t].append(chuan_hoa(acc[t][lan], S))
    for t in range(T):
        assert cac_Y[t] == tinh_y_thang(W, cac_X[t], S)
    return cac_Y, nhip
