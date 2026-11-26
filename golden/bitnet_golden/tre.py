"""A4. Dữ liệu đến cách quãng (gián đoạn) và đầu ra bị chặn (backpressure).

Thực tế DDR3 không cấp đủ 512 bit mỗi nhịp, nên TVALID có lúc = 0 giữa các beat vào; phía nhận Y
(DMA ghi) có lúc chưa sẵn sàng nên TREADY đầu ra có lúc = 0. Chip phải cho ra Y GIỐNG HỆT trường hợp
không gián đoạn: không mất beat, không đếm trùng beat, Acc giữ nguyên khi không có beat.

File trễ (đọc bằng $readmemh, mỗi dòng 2 ký tự hex):
    tre_vao.hex : dòng i = số nhịp TVALID = 0 TRƯỚC khi nguồn đưa beat vào thứ i (X rồi W)
    tre_ra.hex  : dòng j = số nhịp phía nhận giữ TREADY = 0 sau khi beat Y thứ j xuất hiện
"""
import random

TRE_TOI_DA = 15


def tao_tre(so_beat, rng, xac_suat=0.3, tre_toi_da=TRE_TOI_DA):
    """Mỗi beat có xác suất `xac_suat` bị trễ 1..tre_toi_da nhịp, còn lại trễ 0."""
    return [rng.randint(1, tre_toi_da) if rng.random() < xac_suat else 0 for _ in range(so_beat)]


def ghi_tre(duong_dan, cac_tre):
    with open(duong_dan, "w", encoding="utf-8") as f:
        for t in cac_tre:
            f.write(f"{t:02X}\n")


def khong_tre(so_beat):
    return [0] * so_beat


def rng_mac_dinh(seed=12345):
    return random.Random(seed)
