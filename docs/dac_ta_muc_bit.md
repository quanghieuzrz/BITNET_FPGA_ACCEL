# Đặc tả mức bit — IP core BitLinear 1.58-bit

Tài liệu này là **nguồn quy ước duy nhất** cho cả golden model (Python) và RTL (Verilog).
Thay đổi bất kỳ quy ước nào phải sửa ở đây trước, rồi mới sửa code hai bên.

Trạng thái: v1, v1b, v2a, v2b đã chốt định dạng và có golden model (`golden/bitnet_golden/`).
Bản cập nhật này bổ sung: đệm hàng (mục 4.2), beat Y (mục 6), khung vào và quy tắc gián đoạn (mục 7),
thanh ghi điều khiển (mục 8), mô hình hiệu năng (mục 10), dùng chung W cho nhiều token (mục 11).

## 0. Phạm vi và cách ghi số liệu

### 0.1. Chip làm gì, không làm gì

| Trong phạm vi (chạy trên IP) | Ngoài phạm vi (CPU / phần mềm) |
|---|---|
| 7 phép chiếu BitLinear mỗi khối: Q, K, V, O, Gate, Up, Down (nhân ma trận ternary × INT8, trọng số chảy qua) | Attention: QKᵀ, softmax, nhân với V |
| Chuẩn hoá Acc → INT8 (requant) | KV cache (lưu và đọc K, V của các token trước) |
| | RMSNorm, lượng tử hoá X (absmax), nhân scale FP, RoPE, hàm kích hoạt |
| | Lớp embedding và lm_head (128 256 hàng, BF16) |

Hệ quả: chi phí attention tăng theo O(L²) với độ dài ngữ cảnh L và **không** do IP gánh. Mọi kết quả tốc độ của dự án là
tốc độ **các lớp BitLinear**; khi ước tính token/giây cả mô hình phải ghi rõ phần ngoài IP được giả định thế nào.
(Cùng phạm vi với TernaryCore và PENSA.)

### 0.2. Quy tắc ghi số liệu

Mọi con số hiệu năng trong báo cáo, README, issue đều phải ghi: **đơn vị**, **đo cái gì**, **đo hay ước tính**, **lấy từ
script/bảng nào**. Ví dụ đúng: "2318 nhịp xung 100 MHz cho một lượt lớp 768 × 768 v1, T = 1, W từ BRAM, ước tính bằng
`mo_hinh_hieu_nang.py`". Tránh viết tắt dễ nhầm:

| Thuật ngữ | Nghĩa trong dự án |
|---|---|
| nhịp | một chu kỳ xung nhịp của IP (10 ns ở 100 MHz) |
| beat | một lần chuyển 512 bit trên AXI4-Stream |
| lượt | một lần START: T token × một lớp |
| token | một vị trí trong chuỗi (KHÔNG phải trang/khối trọng số) |
| tok/s | token mỗi giây; ghi rõ là **độ trễ một chuỗi** (T = 1) hay **thông lượng** (T > 1) |
| hiệu suất bus | byte thực nhận mỗi nhịp ÷ byte tối đa cổng cho phép mỗi nhịp |

## 1. Tham số chung

| Tham số | Giá trị | Ghi chú |
|---|---|---|
| Độ rộng beat | 512 bit | AXI4-Stream TDATA |
| Tần số mục tiêu | 100 MHz | Chu kỳ 10 ns |
| Kiểu X, Y | INT8 có dấu, bù hai, **đối xứng** | **−127 … 127**; mẫu `0x80` (−128) bị cấm |
| Kiểu W | Ternary | −1, 0, +1 |
| Khúc | 64 phần tử | = số X trong một beat |
| Bộ tích luỹ | 24 bit có dấu | Hàng dài nhất 6912 → \|Acc\| ≤ 6912 × 127 = 877 824 < 2²⁰, cần ≥ 21 bit |
| K (độ dài X) | Bội số của 64, **64 … 6912** | 6912 = dung lượng BRAM chứa X (6912 byte) |
| N (số hàng W thật) | **1 … 65 535** | Không cần chia hết cho R (xem mục 4.2) |
| S | **1 … 23** | S = 0 bị cấm (2^(S−1) vô nghĩa) |

Quy ước chung: **chỉ số thấp nằm ở bit thấp**. Phần tử số 0 luôn ở bit thấp nhất của vùng chứa nó.

Vì sao cấm −128: khi W = −1 làn phải tính −X; −(−128) = +128 không vừa INT8 và sẽ quay vòng thành −128.
Kẹp đối xứng ±127 giống cách BitNet b1.58 lượng tử hoá kích hoạt (và giống PENSA), nên không cần mở rộng X lên 9 bit
trong làn. Y cũng kẹp ±127 vì Y là X của lớp kế tiếp.

## 2. Beat X

```
bit [8c+7 : 8c] = X[c]          c = 0 … 63
```

X[0] ở bit 7..0, X[63] ở bit 511..504. Beat X thứ b chứa X[64b … 64b+63].

## 3. Beat W

### 3.1. v1 — 2 bit / trọng số, 4 hàng / beat

```
bit [128r + 2c + 1 : 128r + 2c] = W[hàng r][cột c]     r = 0 … 3, c = 0 … 63
```

| Mã | Giá trị |
|---|---|
| `00` | 0 |
| `01` | +1 |
| `10` | −1 |
| `11` | Cấm (báo lỗi) |

### 3.2. v2a — 5 bit / nhóm 4, đúng 2 phần tử khác 0, 6 hàng / beat

```
bit [80r + 5g + 4 : 80r + 5g] = nhóm g của hàng r      r = 0 … 5, g = 0 … 15
bit [511 : 480] = 0 (đệm)
```

Trong 5 bit của nhóm: `[4:2]` = mã vị trí, `[1]` = dấu phần tử có vị trí nhỏ hơn, `[0]` = dấu phần tử còn lại.
Dấu: `0` = +1, `1` = −1. Nhóm g gồm các cột 4g … 4g+3.

| Mã vị trí | Cặp vị trí | Mặt nạ (vị trí 0→3) |
|---|---|---|
| `000` | (0, 1) | 1100 |
| `001` | (0, 2) | 1010 |
| `010` | (0, 3) | 1001 |
| `011` | (1, 2) | 0110 |
| `100` | (1, 3) | 0101 |
| `101` | (2, 3) | 0011 |
| `110`, `111` | Cấm | |

Yêu cầu: mọi nhóm có **đúng 2** phần tử khác 0 (mô hình phải train với ràng buộc này).

### 3.3. v2b — 6 bit / nhóm 4, tối đa 2 phần tử khác 0, 5 hàng / beat

```
bit [96r + 6g + 5 : 96r + 6g] = nhóm g của hàng r      r = 0 … 4, g = 0 … 15
bit [511 : 480] = 0 (đệm)
```

Bit `[5]` = bit chế độ.

- **Chế độ 0** (đúng 2 phần tử khác 0): `[4:0]` giống hệt 5 bit của v2a.
- **Chế độ 1** (ít hơn 2 phần tử khác 0): `[4]` = Z, `[3:2]` = vị trí, `[1]` = dấu, `[0]` = 0.
  - Z = 1: nhóm toàn 0 (các bit còn lại = 0).
  - Z = 0: đúng 1 phần tử khác 0 tại vị trí `[3:2]` (0 … 3), dấu `[1]`.

### 3.4. v1b — kiểu TQ1_0, 5 trọng số / byte, 5 hàng / beat

Gói hệ 3: 3⁵ = 243 ≤ 256 nên 5 trọng số vừa 1 byte (1.6 bit/trọng số). Dùng được mọi mô hình BitNet, không cần 2:4.

- Chữ số: −1 → 0, 0 → 1, +1 → 2. Năm trọng số [w0 … w4] → byte = d0·81 + d1·27 + d2·9 + d3·3 + d4 (w0 là chữ số cao nhất).
  Ví dụ [+1, 0, −1, −1, +1] → 191. Byte 243 … 255 bị cấm.
- Beat: nối 5 khúc hàng thành dãy s[0 … 319] với s[64r + c] = W[hàng r][cột c]; byte j chứa s[5j … 5j+4], nằm ở
  `bit [8j+7 : 8j]`, j = 0 … 63. Không có bit đệm. Một byte có thể chứa trọng số của hai hàng
  (vd byte 12 = cột 60…63 của hàng 0 và cột 0 của hàng 1).
- Giải mã: 64 bảng tra (ROM 256 dòng × 10 bit), mỗi bảng ra 5 trọng số; 320 trọng số chia cho 5 làn bằng nối dây.
- Chỉ là *kiểu* TQ1_0: thứ tự chữ số và bố cục beat là quy ước của dự án, không trùng bố cục khối trong file GGUF.

### 3.5. So sánh các phiên bản

| Phiên bản | Bit/trọng số | Hàng/beat (R) | Phép/nhịp | So với v1 | Cộng-trừ mỗi 4 trọng số | Yêu cầu mô hình |
|---|---|---|---|---|---|---|
| v1 | 2.0 | 4 | 256 | 1.00× | 4 | BitNet bất kỳ |
| v1b | 1.6 | 5 | 320 | 1.25× | 4 | BitNet bất kỳ |
| v2b | 1.5 | 5 | 320 | 1.25× | 2 | Tối đa 2 phần tử khác 0 / nhóm |
| v2a | 1.25 | 6 | 384 | 1.50× | 2 | Đúng 2 phần tử khác 0 / nhóm |

v1b và v2b có cùng băng thông; lợi thế của v2b chỉ còn ở làn nhỏ hơn (2 phép cộng-trừ mỗi nhóm) và bộ giải mã nhỏ hơn.
Kiểm chứng: `golden/so_sanh_phien_ban.py`.

## 4. Thứ tự dữ liệu (luồng tính)

### 4.1. Thứ tự

1. Nạp toàn bộ X của token vào BRAM: K/64 beat X.
2. Với mỗi nhóm R hàng (R = 4 ở v1, 5 ở v1b và v2b, 6 ở v2a), nhóm g = 0 … ⌈N/R⌉ − 1:
   - Xoá R bộ tích luỹ.
   - Với mỗi khúc k = 0 … K/64 − 1: đọc khúc X thứ k từ BRAM, nhận 1 beat W (khúc k của R hàng), cộng dồn.
   - Chuẩn hoá R bộ tích luỹ, đưa các số Y của **hàng thật** vào hàng đợi Y (mục 6).

Số beat W = ⌈N/R⌉ × K/64.

### 4.2. Đệm hàng khi N không chia hết cho R

Kích thước thật của BitNet 2B không phải lúc nào cũng chia hết cho R:

| N | v1 (R = 4) | v1b, v2b (R = 5) | v2a (R = 6) |
|---|---|---|---|
| 2560 | 640 nhóm | 512 nhóm | 426,67 → **427 nhóm, đệm 2 hàng** |
| 6912 | 1728 nhóm | 1382,4 → **1383 nhóm, đệm 3 hàng** | 1152 nhóm |
| 640 | 160 nhóm | 128 nhóm | 106,67 → **107 nhóm, đệm 2 hàng** |

Quy tắc:
- Phía gửi (CPU/golden model) thêm ⌈N/R⌉·R − N **hàng giả** vào **cuối** W rồi mới đóng gói.
- Nội dung hàng giả: **toàn 0** ở v1, v1b, v2b. Ở **v2a** hàng toàn 0 không mã hoá được (mỗi nhóm phải có đúng 2 phần tử
  khác 0), nên dùng mẫu cố định **[+1, +1, 0, 0]** lặp lại (mã vị trí `000`, hai dấu `0`, mỗi nhóm = `00000`).
- Chip tính hàng giả như hàng thật (làn không cần biết), nhưng **không xuất Y của hàng giả**: chip dùng thanh ghi N
  (số hàng thật) để biết dừng ở đâu.
- Requant B (S theo token, mục 5): bộ tìm max|Acc| **phải bỏ qua hàng giả**, nếu không S sẽ sai.
- Chi phí: tối đa R − 1 hàng mỗi lớp, trên toàn BitNet 2B chỉ tốn 0,02 % (v1b, v2b) đến 0,05 % (v2a) số beat W.

Golden model: `dem_hang.py`; `tinh_y_theo_chip` tự đệm và bỏ hàng giả.

## 5. Chuẩn hoá đầu ra

```
Y = Kẹp( (Acc + 2^(S−1)) >>> S, −127, 127 )
```

- `>>>` là dịch phải **số học** trên số có dấu.
- Quy ước làm tròn: `.5` làm tròn lên (62.5 → 63, −62.5 → −62).
- S ∈ [1, 23], nạp qua thanh ghi `SHIFT_AMT` (mục 8).

### 5.1. Đổi kết quả về số thực (phần mềm, ngoài IP)

BitNet b1.58 lượng tử như sau (γ = max|x| của token, β = trung bình |W| của cả ma trận, cả hai là số thực):

```
X_q = Kẹp( round(x · 127 / γ), −127, 127 )         W_q = Kẹp( round(W / β), −1, 1 )
W·x ≈ β · (γ / 127) · Acc
```

Chip xuất Y ≈ Acc / 2^S, nên CPU khôi phục kết quả thật bằng:

```
W·x ≈ Y · 2^S · β · γ / 127
```

- β có sẵn trong checkpoint (tensor scale đi kèm mỗi ma trận trọng số); γ do CPU tính khi lượng tử X; S là SHIFT_AMT.
- Phép nhân này chạy trên CPU bằng số thực, một lần cho mỗi số Y, nên không ảnh hưởng mục tiêu 0 DSP của IP.
- Sai số so với BitNet gốc chỉ đến từ bước Y = Kẹp(round(Acc / 2^S)) — đúng thứ đo bằng `do_sai_so_gamma.py`.

### 5.2. Cách chọn S (theo kết quả `golden/do_sai_so_gamma.py`, dữ liệu mô phỏng)

| Cách | SNR (dB) | % bị kẹp | Ghi chú |
|---|---|---|---|
| Gamma chính xác theo token (BitNet gốc, cần nhân) | ~41.5 | 0.02 | Mốc so sánh |
| **2⁻ˢ, S tính lúc chạy theo token** | **~38** | **0** | Chỉ kém ~3.5 dB (~0.6 bit) |
| 2⁻ˢ, S tĩnh, làm tròn gần nhất | 25–35, dao động mạnh | tới 1.5 | Không nên dùng |
| 2⁻ˢ, S tĩnh, chọn an toàn | ~33–34 | 0 | Phương án dự phòng |

Kết luận: sai số chủ yếu đến từ **S cố định** (độ lớn các token khác nhau 3–4 lần), không phải từ việc
làm tròn gamma về 2⁻ˢ.

**Quyết định (lộ trình hai bước):**

1. **Bước 1 — Requant E (làm trước, cho mọi phiên bản W):** S tĩnh theo lớp, chọn **an toàn** lúc hiệu chỉnh:
   S = max(1, ⌈log₂(max|Acc| lớn nhất trên các token hiệu chỉnh / 127)⌉). Mạch: một thanh ghi `SHIFT_AMT`.
   Golden model: `chon_S_an_toan` trong `chuan_hoa.py`.
2. **Bước 2 — Requant B (nâng cấp khi bước 1 đã ổn định):** S tính lúc chạy cho từng token:
   S = max(1, ⌈log₂(max|Acc| của token / 127)⌉), **chỉ xét hàng thật**. Mạch thêm: bộ nhớ tạm N giá trị Acc
   (2560 × 24 bit ≈ 7.5 KB BRAM; 6912 hàng ≈ 20 KB), bộ tìm max|Acc|, bộ dò bit 1 cao nhất, lượt chuẩn hoá thứ hai
   (thêm ~2.5% thời gian với lớp 2560 × 2560). Vẫn 0 DSP. Golden model: `chuan_hoa_theo_token` trong `chuan_hoa.py`.

Ablation có thêm so sánh E và B (độ chính xác và tài nguyên). Cần đo lại với trọng số và kích hoạt thật của BitNet b1.58 2B4T.

## 6. Beat Y (đầu ra)

Y được đóng gói **giống hệt beat X**:

```
beat Y thứ b:  bit [8c+7 : 8c] = Y[64b + c]          c = 0 … 63
```

- Số beat Y = ⌈N/64⌉. Nếu N không chia hết cho 64, các byte thừa ở beat cuối = `0x00`.
  (Kích thước thật của BitNet 2B: 2560, 6912, 640 đều chia hết cho 64.)
- Lợi ích: một định dạng chung cho X và Y, nên phần mềm và DMA dùng một cách đọc/ghi; testbench nối được nhiều lớp liên
  tiếp. Lưu ý: trong BitNet thật, giữa hai lớp BitLinear luôn có bước chạy ngoài IP (norm, lượng tử lại X, attention hoặc
  ReLU², hàm kích hoạt FFN của BitNet b1.58), nên Y **không** đi thẳng làm X của lớp sau; CPU đổi Y về số thực (mục 5.1) rồi xử lý tiếp.
- Vì R (4, 5, 6) không chia hết 64, R số Y của một nhóm có thể nằm ở hai beat Y liên tiếp. Chip cần một hàng đợi Y
  (golden model dùng 128 số = 2 beat) để gom đủ 64 số rồi mới xuất.

Golden model: `ma_hoa_y.py` (`dong_goi_y`, `giai_ma_y`).

## 7. Giao tiếp AXI4-Stream

### 7.1. Tín hiệu

Mỗi cổng gồm `TDATA[511:0]`, `TVALID`, `TREADY`, `TLAST`. Một beat được chuyển khi **`TVALID = TREADY = 1` tại sườn lên**
của xung nhịp. Chip có **một cổng vào** (`s_axis`) và **một cổng ra** (`m_axis`).

### 7.2. Khung vào (một lần chạy = một token × một lớp)

```
[ K/64 beat X ][ ⌈N/R⌉ × K/64 beat W ]      TLAST = 1 chỉ ở beat W cuối cùng
```

Chip biết ranh giới X/W nhờ thanh ghi K, nên X và W đi chung một cổng (một kênh DMA là đủ).
Cổng ra: ⌈N/64⌉ beat Y, `TLAST = 1` ở beat Y cuối.

### 7.3. Quy tắc gián đoạn và chặn (bắt buộc)

1. **Chỉ beat có bắt tay mới được tính.** Nhịp nào `TVALID = 0` hoặc `TREADY = 0` thì không có beat: bộ đếm khúc,
   bộ đếm nhóm và các Acc **giữ nguyên**.
2. **Không mất, không đếm trùng.** Mỗi beat vào được dùng đúng một lần, theo đúng thứ tự.
3. **Phía gửi giữ ổn định.** Khi `TVALID = 1` mà `TREADY = 0`, phía gửi phải giữ nguyên `TDATA` và `TLAST` (luật AXI).
4. **Chặn ngược (backpressure).** Nếu phía nhận Y chưa sẵn sàng (`m_axis_tready = 0`) và hàng đợi Y không còn chỗ cho
   R số của nhóm kế, chip hạ `s_axis_tready` về 0 cho tới khi có chỗ.
5. **Kết quả không phụ thuộc thời gian.** Với cùng X, W, S, chuỗi beat Y phải **giống hệt** dù có gián đoạn hay không;
   gián đoạn chỉ làm tăng số nhịp.
6. Chip **không bao giờ** hạ `TVALID` của cổng ra khi beat Y chưa được nhận (luật AXI), và không đổi `TDATA` khi đang chờ.

Kiểm chứng: `mo_hinh_giao_dich.py` (mô hình theo nhịp) và test `test_A4_gian_doan_khong_doi_Y`; mỗi bộ vector có
`tre_vao.hex`, `tre_ra.hex` để testbench RTL tạo gián đoạn giống hệt.

## 8. Thanh ghi điều khiển (AXI4-Lite, 32 bit)

| Địa chỉ | Tên | Quyền | Nội dung |
|---|---|---|---|
| 0x00 | CTRL | W | bit 0 START (tự xoá), bit 1 RESET mềm (tự xoá) |
| 0x04 | STATUS | R | bit 0 BUSY, bit 1 DONE (giữ tới lần START sau), bit 2 ERROR |
| 0x08 | K | R/W | Độ dài X, bội số của 64, 64 … 6912 |
| 0x0C | N | R/W | Số hàng W **thật**, 1 … 65 535 |
| 0x10 | SHIFT_AMT | R/W | S, 1 … 23 |
| 0x14 | CYCLES | R | Số nhịp từ START tới DONE (đo hiệu năng) |
| 0x18 | MODE | R/W | 0 = v1, 1 = v1b, 2 = v2a, 3 = v2b |
| 0x1C | ERR_CODE | R | Mã lỗi đầu tiên gặp phải (bảng dưới), 0 = không lỗi |
| 0x20 | ID | R | Hằng số `0x424E0100` ("BN", phiên bản 1.0), để phần mềm nhận ra IP |
| 0x24 | SO_TOKEN | R/W | T = số token dùng chung mỗi beat W, 1 … 8 (mục 11). Giai đoạn 2 chỉ hỗ trợ T = 1 |

**Trình tự dùng (phần mềm):**

1. Đọc ID, kiểm tra đúng `0x424E0100`.
2. Ghi K, N, SHIFT_AMT, MODE (chỉ có tác dụng khi BUSY = 0).
3. Ghi CTRL = 1 (START). Chip kiểm tra cấu hình; nếu hợp lệ, BUSY = 1.
4. Khởi động DMA: gửi khung vào (mục 7.2), nhận ⌈N/64⌉ beat Y.
5. Chờ DONE = 1 (thăm dò STATUS). Đọc CYCLES, kiểm tra ERROR.

**Mã lỗi (ERR_CODE):**

| Mã | Tên | Khi nào | Chip làm gì |
|---|---|---|---|
| 1 | LOI_CAU_HINH | START khi K, N, S, MODE hoặc SO_TOKEN sai, hoặc chưa có trong bản RTL hiện tại | Không chạy; DONE = ERROR = 1 |
| 2 | LOI_MA_W | Gặp mã W cấm (v1 `11`; v1b byte ≥ 243; v2a vị trí `110`/`111`; v2b mẫu sai) | Coi trọng số đó = 0, chạy tiếp tới hết khung, ERROR = 1 |
| 3 | LOI_MA_X | Gặp X = `0x80` | Coi là −127, chạy tiếp, ERROR = 1 |
| 4 | LOI_TLAST | TLAST đến trước beat cuối, hoặc beat cuối không có TLAST | Kết thúc theo bộ đếm, ERROR = 1; phần mềm nên RESET mềm |

Nguyên tắc: **lỗi dữ liệu không làm treo bus** — chip vẫn nhận hết khung và vẫn xuất đủ ⌈N/64⌉ beat Y, để DMA không
bị kẹt; phần mềm đọc ERROR để biết kết quả không đáng tin. Giai đoạn 2 chỉ hỗ trợ MODE = 0 (v1).

Golden model: `thanh_ghi.py` (`DIA_CHI`, `kiem_tra_cau_hinh`, `so_beat_*`).

## 9. Định dạng file vector

| File | Định dạng |
|---|---|
| `x_in.hex`, `w_in.hex` | Mỗi dòng 1 beat = 128 ký tự hex; ký tự trái nhất là bit 511..508 (đọc bằng `$readmemh`). W đã đệm hàng |
| `y_out.hex` | Các beat Y đúng như chip xuất ra cổng `m_axis` (mục 6) |
| `y_expected.hex` | Mỗi dòng 1 số INT8 = 2 ký tự hex, bù hai (để đọc bằng mắt) |
| `tre_vao.hex` | Dòng i = số nhịp `TVALID = 0` trước beat vào thứ i (X rồi W), 2 ký tự hex |
| `tre_ra.hex` | Dòng j = số nhịp phía nhận giữ `TREADY = 0` khi beat Y thứ j đã sẵn sàng, 2 ký tự hex |
| `config.txt` | `KHOA=GIA_TRI`: PHIEN_BAN, MODE, K, N, N_DEM, KHUC, LAN, S, SO_BEAT_X, SO_BEAT_W, SO_BEAT_Y, GHI_CHU |

Testbench chạy mỗi bộ vector **hai lần**: không trễ (bỏ qua file trễ) và có trễ; cả hai lần `y_out.hex` phải khớp.

## 10. Mô hình hiệu năng

Một token, một lớp K → N:

```
nhịp ≈ K/64  +  max( beat_W ,  beat_W × 64 / (băng thông / tần số) )  +  vài nhịp xả
beat_W = ⌈N/R⌉ × K/64
```

Khi RAM cấp đủ 64 byte/nhịp (6,4 GB/s ở 100 MHz), chip bị giới hạn bởi tính toán; ngược lại bị giới hạn bởi băng thông.
DDR3L của Arty A7 (16 bit, 667 Mb/s) cho tối đa ~1,33 GB/s, tức chỉ ~21 % nhu cầu của v1.

Trên bo, đo thêm **hiệu suất bus** của luồng W = (số beat W × 64 byte ÷ số nhịp) ÷ byte/nhịp tối đa của đường nạp.
Khi đã bị giới hạn bởi băng thông, chỉ số này cho biết còn bao nhiêu để cải thiện phía nạp dữ liệu; nếu đã gần 100 % thì
muốn nhanh hơn chỉ còn cách **giảm số byte W phải chở** (v1b, v2) hoặc **dùng mỗi byte W cho nhiều việc hơn** (mục 11).
Kết quả ước tính và đối chiếu với mô hình theo nhịp: `golden/mo_hinh_hieu_nang.py`.
Quy tắc viết RTL: `docs/quy_tac_rtl.md`. Kế hoạch đánh giá: `docs/ke_hoach_danh_gia.md`.

## 11. Mở rộng: dùng chung một beat W cho T token

**Ý tưởng.** Khi bị giới hạn bởi băng thông, làn ngồi chờ phần lớn thời gian (trên Arty A7: ~79 %). Nếu BRAM có sẵn X của
T token, mỗi beat W vừa đến được giữ T nhịp và dùng cho lần lượt từng token. Cùng số byte W kéo từ RAM, làm được T lần việc.
Áp dụng khi nhiều token cùng chờ một lớp: **prefill**, **mô hình encoder / không tự hồi quy** (một lượt cho cả chuỗi),
**gộp nhiều yêu cầu**. Không giúp **decode của một người dùng** (mỗi lúc chỉ có 1 token mới, T = 1).

**Quy ước:**

- Khung vào: X token 0 (K/64 beat), X token 1, …, X token T−1, rồi các beat W **giống hệt** khi T = 1. Tổng T·K/64 + beat_W.
- Tính: beat W (nhóm g, khúc k) được giữ T nhịp; nhịp t cộng khúc X thứ k của token t vào Acc[t][làn].
  Đầu vào hạ `TREADY` trong T − 1 nhịp sau mỗi beat W.
- Token t xong nhóm ở nhịp thứ t sau token 0, nên **R bộ chuẩn hoá vẫn đủ** (mỗi nhịp chuẩn hoá R số của một token).
- Ra: với mỗi khối 64 hàng b: beat Y khối b của token 0, của token 1, …, của token T−1. Beat Y thứ i thuộc token i mod T.

**Chi phí phần cứng:** BRAM X = T × K byte (T = 8, K = 6912: 54 KB, XC7A100T có ~600 KB BRAM); Acc tăng từ R lên R × T
thanh ghi 24 bit (v2a, T = 8: 48 thanh ghi); T hàng đợi Y; địa chỉ đọc X = t·K/64 + k. Làn và cây cộng **không đổi**.

**Hiệu quả ước tính** (`mo_hinh_hieu_nang.py`, BitNet 2B, DDR3L 1,33 GB/s, thông lượng):

| T | v1 | v1b | v2b | v2a |
|---|---|---|---|---|
| 1 | 2,6 tok/s | 3,2 | 3,2 | 3,8 |
| 4 | 10,2 | 12,8 | 12,8 | 15,3 |
| 5 (vừa đủ) | 12,3 | 15,3 | 15,3 | 18,4 |

T vừa đủ = ⌈64 byte ÷ byte/nhịp của RAM⌉ (1,33 GB/s → 5; 1,0 GB/s → 7). Lớn hơn nữa không nhanh thêm vì lúc đó bị giới hạn bởi
tính toán. Giai đoạn 2 làm T = 1; RTL thiết kế sẵn tham số T để mở rộng mà không đổi giao tiếp.
Golden model: `nhieu_token.py`.

## 12. Hướng phát triển (không thuộc bản đầu)

| Ý tưởng | Vì sao | Cách đánh giá |
|---|---|---|
| **Làn kiểu bảng tra** (như TL1/TL2 của bitnet.cpp): tính trước tổng các cặp X (x₁ ± x₂…) **một lần**, dùng chung cho cả R làn; mỗi làn chỉ chọn theo mã W | Cây cộng mỗi làn giảm từ 64 xuống 32 đầu vào. Nhưng trên FPGA, bộ chọn 9 đường (~2–3 LUT/bit) đắt hơn bộ cộng (~1 LUT/bit), nên chỉ có lời khi nhiều làn dùng chung (R lớn, nhiều lõi) | Ablation: tổng hợp hai kiểu làn, so LUT ở R = 4, 6, 12 |
| **X 4 bit** (các bản BitNet mới thử kích hoạt 4 bit) | Cây cộng hẹp hơn, BRAM X giảm một nửa. **Không** giảm băng thông vì W chiếm gần hết | Đổi tham số độ rộng X; cần mô hình train với X 4 bit |
| **Nhiều lõi song song** trên bo dư băng thông (vd KV260) | Khi RAM cấp > 64 byte/nhịp thì nghẽn ở tính toán; chia hàng cho 2–3 lõi, X phát cho tất cả (giống PENSA) | Mô hình hiệu năng + tổng hợp trên XCK26 |
| **Requant B** (S theo token) | Tăng ~5 dB SNR so với E | Đã có lộ trình ở mục 5.2 |
| Mô hình **MoE** ternary | Ít trọng số mỗi token hơn, nhưng các token đi vào chuyên gia khác nhau nên khó dùng chung beat W (mục 11) | Chỉ ghi nhận |

So sánh định dạng nén với bitnet.cpp: TL1 = 2 trọng số / 4 bit (2,0 bit), TL2 = 3 trọng số / 5 bit (1,67 bit),
v1b của dự án = 5 trọng số / 8 bit (1,6 bit), giới hạn lý thuyết log₂3 ≈ 1,585 bit.
