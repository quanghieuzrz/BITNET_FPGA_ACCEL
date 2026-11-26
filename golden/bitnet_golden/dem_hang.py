"""A1. Đệm hàng khi số hàng thật N không chia hết cho số làn R.

Ví dụ: lớp Q của BitNet 2B có N = 2560 hàng; v2a có R = 6 làn -> 2560 / 6 = 426,67 nhóm.
Cách làm: thêm hàng giả vào CUỐI cho đủ 427 nhóm (2562 hàng). Chip vẫn tính hàng giả như hàng thật
(vì làn không biết hàng nào là giả), nhưng BỎ đầu ra của chúng: chỉ xuất N số Y đầu tiên.

Nội dung hàng giả:
    v1, v1b, v2b : toàn 0 (mã hoá được bình thường).
    v2a          : KHÔNG được toàn 0, vì v2a bắt buộc mỗi nhóm 4 có ĐÚNG 2 phần tử khác 0.
                   Dùng mẫu cố định [+1, +1, 0, 0] lặp lại (mã vị trí 000, hai dấu +).
Hàng giả chỉ ảnh hưởng tới Acc của chính nó, Acc đó bị bỏ, nên Y của hàng thật không đổi.
Lưu ý cho requant B (S theo token): bộ tìm max|Acc| phải BỎ QUA hàng giả.
"""
from .hang_so import NHOM, SO_LAN

MAU_NHOM_DEM_V2A = [+1, +1, 0, 0]


def so_nhom_hang(N, R):
    """Số nhóm R hàng = làm tròn lên N / R."""
    return -(-N // R)


def so_hang_dem(N, R):
    """Số hàng giả cần thêm."""
    return so_nhom_hang(N, R) * R - N


def hang_dem(K, phien_ban):
    """Một hàng giả dài K, hợp lệ với phiên bản đóng gói."""
    if phien_ban == "v2a":
        return MAU_NHOM_DEM_V2A * (K // NHOM)
    return [0] * K


def dem_hang(W, phien_ban):
    """Trả về W đã đệm (độ dài là bội số của R). Không sửa W gốc."""
    R = SO_LAN[phien_ban]
    K = len(W[0])
    return W + [hang_dem(K, phien_ban) for _ in range(so_hang_dem(len(W), R))]
