# Giai đoạn 1: Đặc tả thuật toán và Golden Model

**Mục tiêu:** chốt cứng toàn bộ giao thức dữ liệu, kiến trúc chống nghẽn dây nối (routing) và toán học **trước khi viết RTL**,
để không bị lệch bit hay phải sửa lại giao tiếp. Mọi quy ước chi tiết nằm ở `docs/dac_ta_muc_bit.md`, là nguồn quy ước duy nhất
cho cả Python và RTL.

## 1.0. Phạm vi

IP chỉ tăng tốc **7 phép chiếu BitLinear** mỗi khối (Q, K, V, O, Gate, Up, Down) và chuẩn hoá đầu ra. Attention (QKᵀ, softmax,
PV), KV cache, RMSNorm, embedding, lm_head chạy ngoài IP. Mọi số liệu ghi rõ đơn vị, đo gì, đo hay ước tính, nguồn
(đặc tả mục 0).

## 1.1. Giao thức luồng 512-bit (Input-Stationary X Reuse)

**Tham số chung:** bus AXI4-Stream 512 bit (TDATA, TVALID, TREADY, TLAST; một beat được chuyển khi TVALID = TREADY = 1),
100 MHz (10 ns/nhịp), khúc = 64 phần tử. Quy ước bit: chỉ số thấp nằm ở bit thấp.

**Khoảng giá trị X và Y:** INT8 có dấu, kẹp **đối xứng [−127, 127]** (giống BitNet b1.58 và PENSA). Mẫu −128 bị cấm, vì khi W = −1
làn phải tính −X và −(−128) = +128 không vừa INT8.

**Pha nạp X (Load Activation):** toàn bộ vector X của một token (K ≤ 6912 phần tử, ≤ 6.75 KB) được nạp một lần vào BRAM trên chip,
K/64 beat; mỗi beat chở 64 phần tử, `bit [8c+7 : 8c] = X[c]`. Khi tính, từng khúc 64 phần tử được đọc từ BRAM và nhân bản thành
6 bản sao thanh ghi độc lập, đặt sát cây cộng của từng làn, gắn `(* dont_touch = "true" *)` để công cụ tổng hợp không gộp lại,
nhằm giảm fanout và đường dây dài để đóng timing 100 MHz trên Artix-7.

**Pha bắn W (Stream Weights):** mỗi beat W chứa khúc 64 cột của R hàng, đi kèm khúc X cùng vị trí.

**Thứ tự tính:** với mỗi nhóm R hàng: xoá R bộ tích luỹ → lần lượt qua K/64 khúc (mỗi khúc = 1 nhịp: đọc khúc X từ BRAM, nhận
1 beat W, R làn cộng dồn) → chuẩn hoá R kết quả → sang nhóm R hàng tiếp theo. X chỉ đọc từ bộ nhớ ngoài một lần, W đọc đúng một
lần, mỗi làn chỉ cần một thanh ghi Acc.

**Đệm hàng:** số hàng N không cần chia hết cho R (vd 2560/6 hay 6912/5 của BitNet 2B). Phía gửi thêm tối đa R − 1 hàng giả
vào cuối (toàn 0; riêng v2a dùng mẫu [+1, +1, 0, 0] vì nhóm toàn 0 không mã hoá được), chip tính nhưng không xuất Y của hàng
giả, dựa vào thanh ghi N. Chi phí ≤ 0,05 % số beat W trên toàn BitNet 2B.

**Bộ tích luỹ:** 24 bit có dấu. Trường hợp xấu nhất (hàng 6912, |X| = 127): |Acc| ≤ 877 824 < 2²⁰, cần tối thiểu 21 bit.

## 1.2. Định dạng trọng số và chiến lược sparsity

| Phiên bản | Mã hoá W | Bit/trọng số | Hàng/beat | Phép/nhịp | Yêu cầu mô hình |
|---|---|---|---|---|---|
| v1 | 2 bit/trọng số | 2.0 | 4 | 256 | BitNet bất kỳ |
| v1b (kiểu TQ1_0) | 5 trọng số/byte, giải mã bảng tra 256 dòng | 1.6 | 5 | 320 | BitNet bất kỳ |
| v2b | 6 bit/nhóm 4 | 1.5 | 5 | 320 | Tối đa 2 phần tử khác 0 / nhóm |
| v2a | 5 bit/nhóm 4 | 1.25 | 6 | 384 | Đúng 2 phần tử khác 0 / nhóm |

**Nấc 1 (v1, dày đặc + zero-gating):** mã `00` = 0, `01` = +1, `10` = −1, `11` cấm. Khi W = 0, đầu vào vị trí đó trong cây cộng
được ép cố định về 0 và mạch đổi dấu không chuyển trạng thái, giảm công suất động mà không đổi thông lượng.

**v1b (kiểu TQ1_0, phiên bản đối chứng):** định dạng 5 trọng số/byte của bitnet.cpp và PENSA. Một beat = 64 byte = 320 trọng số =
5 khúc hàng × 64 (nối 5 khúc thành một dãy, một byte có thể chứa trọng số của hai hàng). Đạt 5 hàng/beat mà không cần mô hình
train lại, dùng để kiểm chứng nén 2:4 có thật sự đáng giá hay không.

**Nấc 2 (v2, 2:4 structured sparsity):** nhóm 4 trọng số liên tiếp có tối đa 2 phần tử khác 0.
- **v2a (5 bit/nhóm):** `[4:2]` = mã vị trí (6 cặp C(4,2), `000` … `101`, giải mã bằng LUT 3→4), `[1]`, `[0]` = dấu hai phần tử
  khác 0. Mỗi khúc hàng 80 bit, 6 hàng/beat (480 bit + 32 bit đệm), 384 phép/nhịp, tăng tốc 1.5×. Giới hạn: nhóm 2:4 ternary có
  33 cấu hình hợp lệ, vượt 32 mã của 5 bit; v2a chỉ mã hoá 24 cấu hình có **đúng 2** phần tử khác 0.
- **v2b (6 bit/nhóm):** thêm bit chế độ `[5]`; chế độ 1 dùng bit Z cho nhóm toàn 0 hoặc mã hoá nhóm có 1 phần tử khác 0.
  Mã hoá đủ 33 cấu hình. 5 hàng/beat, 1.25×.
- Ở v2, mỗi nhóm chỉ cần 2 phép cộng/trừ thay vì 4: làn nhỏ hơn và ít tiêu thụ hơn v1/v1b. Đây là lợi thế còn lại của v2b so với
  v1b (cùng băng thông).

## 1.3. Chuẩn hoá đầu ra (Re-quantization, 0 DSP)

> Y = Clamp( (Acc + 2^(S−1)) >>> S, −127, 127 )

Quy ước làm tròn `.5` lên; S ≥ 1 nạp qua thanh ghi `Shift_Amt`.

Kết quả đo (`golden/do_sai_so_gamma.py`, lớp 2560 × 2560 và 2560 × 6912, dữ liệu mô phỏng):

| Cách | SNR | % bị kẹp | Kết luận |
|---|---|---|---|
| Gamma chính xác theo token (BitNet gốc, cần nhân) | ~41.6 dB | ~0 | Mốc so sánh |
| B: 2⁻ˢ, S theo token lúc chạy | ~38 dB | 0 | Kém gốc ~0.6 bit |
| D: 2⁻ˢ, S tĩnh làm tròn gần nhất | 19–39 dB, dao động | tới 1.2 | Loại bỏ |
| E: 2⁻ˢ, S tĩnh chọn an toàn | ~33–34 dB | ~0 | Ổn định |

Sai số chủ yếu đến từ việc dùng **S cố định** cho mọi token, không phải từ việc làm tròn gamma về 2⁻ˢ. Lộ trình:
1. **Requant E (bản đầu):** S tĩnh theo lớp, chọn an toàn trên tập hiệu chỉnh. Mạch chỉ cần thanh ghi `Shift_Amt`.
2. **Requant B (nâng cấp):** S tính theo từng token; thêm bộ nhớ tạm Acc (≈ 7.5 KB BRAM với 2560 hàng), bộ tìm max|Acc|,
   bộ dò bit 1 cao nhất, lượt chuẩn hoá thứ hai (~2.5% thời gian). Vẫn 0 DSP.

## 1.4. Giao tiếp và điều khiển

- **Khung vào (một cổng AXI4-Stream):** K/64 beat X rồi ⌈N/R⌉ × K/64 beat W; `TLAST` ở beat cuối.
- **Đầu ra Y:** đóng gói **giống hệt beat X** (64 số INT8/beat, Y[0] ở bit thấp), ⌈N/64⌉ beat: một định dạng chung cho X
  và Y. CPU đổi Y về số thực bằng Y · 2^S · β · γ / 127 (β: scale của W, γ: scale của X) rồi chạy tiếp các bước ngoài IP.
  Chip có hàng đợi Y để gom R số mỗi nhóm thành beat 64 số.
- **Gián đoạn và chặn ngược:** chỉ beat có `TVALID = TREADY = 1` mới được tính; không có beat thì Acc và bộ đếm giữ nguyên;
  phía nhận Y chưa sẵn sàng thì chip hạ `TREADY` vào. Kết quả không phụ thuộc thời gian, gián đoạn chỉ làm chậm.
- **Thanh ghi AXI4-Lite:** CTRL (START, RESET mềm), STATUS (BUSY, DONE, ERROR), K, N, SHIFT_AMT, CYCLES (đếm nhịp để đo hiệu
  năng), MODE (v1/v1b/v2a/v2b), ERR_CODE, ID. Lỗi dữ liệu (mã W cấm, X = −128, TLAST sai) không làm treo bus.
- Chi tiết: `docs/dac_ta_muc_bit.md` mục 6–8.

## 1.5. Mô hình hiệu năng

> nhịp ≈ K/64 + max(beat_W, beat_W × 64 / (băng thông / tần số)) + vài nhịp xả,  beat_W = ⌈N/R⌉ × K/64

| Kịch bản (100 MHz, BitNet 2B4T, 1 token) | v1 | v1b | v2b | v2a |
|---|---|---|---|---|
| Giới hạn tính toán (RAM cấp đủ 6,4 GB/s) | 12,3 tok/s | 15,3 | 15,3 | 18,4 |
| DDR3L Arty A7 đỉnh ~1,33 GB/s | 2,6 tok/s | 3,2 | 3,2 | 3,8 |

Trên Arty A7, chip bị **giới hạn bởi băng thông** (DDR3L chỉ cấp ~21 % nhu cầu của v1), nên giảm bit/trọng số (v1b, v2) tăng
tốc gần đúng tỉ lệ. Cả mô hình (311–497 MB trọng số) không vừa 256 MB DDR3L: trên bo chỉ đánh giá từng lớp. Công thức khớp mô hình
theo nhịp trong golden model. Script: `golden/mo_hinh_hieu_nang.py`.

**Mở rộng T token (đặc tả mục 11):** khi nhiều token cùng chờ một lớp (prefill, encoder, gộp yêu cầu), mỗi beat W được giữ
T nhịp và dùng cho T token. Trên Arty A7, T = 5 đưa thông lượng v1 từ 2,6 lên 12,3 tok/s (bằng giới hạn tính toán), chỉ tốn
thêm BRAM cho X và R × T thanh ghi Acc. Giai đoạn 2 làm T = 1, thanh ghi SO_TOKEN có sẵn.

## 1.6. Python Golden Model

- Hai cách tính Y đối chiếu nhau: nhân thẳng (định nghĩa) và cộng/trừ chia khúc theo đúng thứ tự của chip.
- Mã hoá/giải mã beat X, W v1, v1b, v2a, v2b; giải mã là bản mẫu cho bộ giải mã RTL.
- Đệm hàng (`dem_hang.py`), đóng gói Y (`ma_hoa_y.py`), bảng thanh ghi và kiểm tra cấu hình (`thanh_ghi.py`).
- **Mô hình theo nhịp** (`mo_hinh_giao_dich.py`): mô phỏng bắt tay TVALID/TREADY, hàng đợi Y, chặn ngược; dùng để kiểm tra
  quy tắc gián đoạn và đối chiếu số nhịp.
- Xuất vector .hex (mỗi dòng 1 beat = 128 ký tự hex, đọc bằng `$readmemh`): `x_in.hex`, `w_in.hex`, `y_out.hex`,
  `y_expected.hex`, `tre_vao.hex`, `tre_ra.hex`, `config.txt`.
- Bộ vector ngẫu nhiên (seed cố định), 6 bộ vector biên, vector v1b/v2a/v2b kèm bản v1 đối chiếu cùng W,
  bộ 768 × 768 cho cả 4 phiên bản (cùng bài toán TernaryCore công bố).
- Mô hình dùng chung W cho T token (`nhieu_token.py`).
- 19 test tự động, gồm kiểm tra đủ 243 mã v1b, 24 cấu hình v2a, 33 cấu hình v2b, đệm hàng, beat Y, thanh ghi,
  và 20 kịch bản gián đoạn ngẫu nhiên.

## 1.7. Quy tắc RTL và kế hoạch đánh giá

- `docs/quy_tac_rtl.md`: 26 quy tắc (một thanh ghi một khối `always`, reset đồng bộ, `signed` và `>>>`, không latch, bắt tay
  AXI, DSP = 0) và danh sách kiểm tra lint → mô phỏng → thử phá → tổng hợp thử cho mỗi module.
- `docs/ke_hoach_danh_gia.md`: 4 câu hỏi (đúng bit, tài nguyên, tốc độ, độ chính xác), mốc so sánh TernaryCore cùng bo và
  MicroBlaze, kế hoạch đo perplexity bằng mô phỏng pipeline số nguyên trên BitNet 2B4T.

## 1.8. Tiêu chí hoàn thành (Mốc 1)

- [x] Đặc tả mức bit cho X, W (v1, v1b, v2a, v2b), chuẩn hoá, file vector, giao tiếp.
- [x] Golden model và bộ vector cho cả 4 phiên bản, test tự động.
- [x] Đo sai số chuẩn hoá, chốt lộ trình requant E → B.
- [x] Kẹp đối xứng ±127 cho X và Y.
- [x] Đệm hàng, beat Y, khung vào, quy tắc gián đoạn, bảng thanh ghi, mã lỗi.
- [x] Mô hình hiệu năng, quy tắc RTL, kế hoạch đánh giá, bộ vector 768 × 768.
- [x] Phạm vi IP, quy tắc ghi số liệu, mở rộng T token, chỉ số hiệu suất bus.
- [ ] Đo lại sai số chuẩn hoá với trọng số và kích hoạt thật của BitNet b1.58 2B4T.
- [ ] Giảng viên duyệt đặc tả.
