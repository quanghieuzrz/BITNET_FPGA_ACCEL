# Kế hoạch đánh giá

Chốt ngay ở Giai đoạn 1 để biết từ đầu cần đo gì, so với ai và bằng dữ liệu nào.

## 1. Bốn câu hỏi cần trả lời

| # | Câu hỏi | Đo bằng |
|---|---|---|
| Q1 | Chip có tính **đúng từng bit** không? | Testbench RTL so với golden model (mọi bộ vector, có và không gián đoạn); sau đó chạy trên bo, so Y đọc về |
| Q2 | Chip **tốn bao nhiêu tài nguyên** và chạy **nhanh tới đâu**? | Báo cáo Vivado: LUT, FF, BRAM, **DSP = 0**, WNS / Fmax, công suất ước tính |
| Q3 | Chip **xử lý nhanh bao nhiêu** và bị nghẽn ở đâu? | Thanh ghi CYCLES trên bo, so với `mo_hinh_hieu_nang.py` |
| Q4 | Cách tính trên chip **giữ được độ chính xác** của mô hình không? | Mô phỏng phần mềm pipeline số nguyên chèn vào BitNet b1.58 2B4T, đo perplexity |

## 2. Hiệu năng và tài nguyên (Q2, Q3)

### 2.1. Các chỉ số

- Tài nguyên: LUT, FF, BRAM, DSP (phải = 0); tỉ lệ % trên XC7A100T.
- Fmax (WNS ở 100 MHz), công suất động (Vivado Power Report, ước tính).
- Số nhịp mỗi lớp (CYCLES), ở hai chế độ: nguồn W từ BRAM trên chip (giới hạn tính toán) và từ DDR3L qua DMA
  (giới hạn băng thông).
- Chỉ số dẫn xuất: **phép/nhịp**, **phép/nhịp/1000 LUT** (hiệu quả trên diện tích), tỉ lệ đo thật / dự đoán.
- **Năng lượng mỗi token** (J/token) = công suất × thời gian. Trên Arty A7, tốc độ bị DDR3L 16 bit chặn ở mức ngang
  một CPU nhỏ, nên lợi thế cần chứng minh là **hiệu quả** (J/token, phép/nhịp/LUT, 0 DSP), không phải tok/s tuyệt đối.
  Đo: Vivado Power Report (ước tính) và đo dòng nguồn của bo (thực tế), so với Pi 4B đo cùng cách.
- **Hiệu suất bus** của luồng W (byte nhận mỗi nhịp ÷ byte tối đa mỗi nhịp). TernaryCore báo ~1,01 nhịp mỗi từ 32 bit,
  tức ~99 % mức sàn của cổng; đây là cách tốt để chứng minh phía nạp dữ liệu đã tối ưu.
- Ghi số liệu theo quy tắc ở đặc tả mục 0.2 (đơn vị, đo gì, đo hay ước tính, nguồn).

### 2.2. Mốc so sánh

| Mốc | Vì sao | Cách làm |
|---|---|---|
| **TernaryCore** (Arty A7-100T, cùng mã 2 bit, kiến trúc output-stationary) | Cùng bo, cùng định dạng → so sánh **công bằng nhất** | Tổng hợp **nguyên bản** repo của họ trong một thư mục riêng (không chép RTL vào repo này vì giấy phép CERN-OHL-S); chạy cùng bài toán 768 × 768 (`golden/tao_vector_768.py`) |
| CPU mềm MicroBlaze trên cùng bo | Cho thấy lợi ích của IP so với phần mềm | Viết vòng lặp C cộng/trừ ternary, đo nhịp bằng timer |
| v1 ↔ v1b ↔ v2b ↔ v2a (ablation nội bộ) | Tách đóng góp của từng ý tưởng | Cùng X, W (đối chiếu), cùng bo |
| **bitnet.cpp trên CPU nhỏ** (Raspberry Pi 4B 2 GB, laptop của bạn) | Mốc phần mềm thật, rẻ, ai cũng kiểm lại được | Chạy `llama-bench`/`run_inference.py` của bitnet.cpp, ghi riêng tốc độ prefill và decode, số luồng, công suất (đồng hồ đo USB). Số tham khảo từ một video thử nghiệm: Pi 4B decode ~2,1–2,8 tok/s, prefill ~1,4 tok/s (cả mô hình, 4 luồng) — chỉ để định hướng, phải tự đo lại |
| PENSA (Alveo U50, HBM) | Chỉ để **tham khảo bối cảnh**, không so trực tiếp vì khác hẳn cấp phần cứng | Trích số liệu công bố |

So với TernaryCore cần tách hai mức:
- **Mức lõi tính toán:** số nhịp khi dữ liệu đã sẵn (công thức của dự án: 768 × 768 v1 ≈ 12 + 2304 + 2 nhịp).
- **Mức hệ thống:** gồm cả cách nạp dữ liệu (họ nạp bằng CPU qua AXI; dự án này dùng DMA). Số công bố của họ
  (5,32 triệu nhịp) là mức hệ thống, nên phải đo mình ở cùng mức trước khi so.

Câu hỏi khoa học của phần so sánh: **khi bị giới hạn bởi băng thông RAM, cách sắp xếp nào hiệu quả hơn trên mỗi LUT** —
1 X/nhịp phát cho nhiều hàng (TernaryCore) hay 64 X/nhịp qua cây cộng (dự án này)?

### 2.3. Kịch bản băng thông

Theo `mo_hinh_hieu_nang.py` (100 MHz): cần 6,4 GB/s để không chờ RAM, nhưng DDR3L của Arty A7 chỉ ~1,33 GB/s (đỉnh).
Vì vậy đo **cả hai** nguồn W: BRAM (cho thấy năng lực lõi) và DDR3L (cho thấy hệ thống thật), rồi đối chiếu với mô hình.
Toàn bộ BitNet 2B không vừa 256 MB DDR3L (cần 311–497 MB tuỳ phiên bản), nên trên bo chỉ đánh giá **từng lớp**;
số token/giây của cả mô hình là **ước tính** từ mô hình hiệu năng, ghi rõ trong báo cáo.

### 2.4. Hai kiểu tải

| Kiểu tải | T | Chỉ số báo cáo |
|---|---|---|
| Decode tự hồi quy (một người dùng) | 1 | độ trễ mỗi token |
| Prefill, encoder / mô hình không tự hồi quy, gộp yêu cầu | 2 … 8 | thông lượng token/giây |

Bài học từ trao đổi với nhóm TernaryCore: hệ thống bị giới hạn bởi băng thông thì decode trả chi phí chở trọng số **mỗi
token**, còn tải một lượt (encoder, phân loại, quyết định) trả **một lần cho cả chuỗi**. Thí nghiệm T > 1 cho thấy IP tận
dụng điều này tới đâu. Attention vẫn ngoài IP, chi phí O(L²) nên tải encoder chỉ hợp với ngữ cảnh ngắn.

### 2.5. Thông điệp trung thực về tốc độ

| | Decode (T = 1) | Prefill / encoder (T = 5) | Ghi chú |
|---|---|---|---|
| Chip, Arty A7, ước tính, chỉ lớp BitLinear | v1 2,6 / v2a 3,8 tok/s | v1 12,3 / v2a 18,4 tok/s | `mo_hinh_hieu_nang.py` |
| Pi 4B + bitnet.cpp, cả mô hình (video) | ~2,1–2,8 tok/s | ~1,4 tok/s | phải tự đo lại |

Kết luận cần viết rõ: ở decode, chip trên Arty A7 chỉ **ngang** một CPU nhỏ vì cả hai đều bị giới hạn bởi bộ nhớ;
lợi thế nằm ở **prefill/encoder (T > 1)**, ở **năng lượng**, và ở **khả năng mở rộng** khi có bộ nhớ nhanh hơn
(mô hình hiệu năng cho thấy tốc độ tăng tỉ lệ thuận với băng thông tới 6,4 GB/s).
Arty A7 (256 MB) không chứa nổi cả BitNet 2B (~400 MB); muốn chạy trọn mô hình trên bo phải dùng mô hình ternary nhỏ
hơn (vd mô hình student của TernaryCore) hoặc bo có ≥ 512 MB DDR.

## 3. Độ chính xác (Q4)

### 3.1. Mô phỏng phần mềm pipeline số nguyên

Thay mỗi lớp BitLinear của BitNet b1.58 2B4T bằng phép tính **giống hệt chip**:
lượng tử X về INT8 kẹp ±127 → cộng/trừ ternary thành Acc 24 bit → chuẩn hoá `(Acc + 2^(S−1)) >>> S`, kẹp ±127.
Phần ngoài chip (RMSNorm, attention, softmax, nhân scale FP) giữ nguyên.

### 3.2. Các cấu hình cần đo

| Cấu hình | Mục đích |
|---|---|
| BitNet gốc (BF16 scale, gamma chính xác) | Mốc |
| Requant E (S tĩnh, chọn an toàn) | Bản đầu của chip |
| Requant B (S theo token) | Bản nâng cấp |
| v2: W cắt thẳng về 2:4 (giữ 2 phần tử lớn nhất trong latent weight, không train lại) | Ước lượng cận dưới mất mát của 2:4 |
| v2: train lại 2:4 trên mô hình ternary nhỏ | Ước lượng mất mát thực tế khi có QAT |

### 3.3. Chỉ số và dữ liệu

- Perplexity trên WikiText-2 (giống cách PENSA báo cáo), có thể thêm vài benchmark ngắn (vd ARC-Easy, HellaSwag).
- Tập hiệu chỉnh S: vài trăm token lấy từ tập train, tách biệt tập đo.
- Đồng thời chạy lại `do_sai_so_gamma.py` với Acc thật thay cho dữ liệu mô phỏng.

Yêu cầu: máy có GPU hoặc CPU đủ RAM để chạy 2B tham số; tải trọng số từ Hugging Face (`microsoft/bitnet-b1.58-2B-4T`).

## 4. Kết quả cần có trong báo cáo

1. Bảng tài nguyên + Fmax cho v1, (v1b), v2a, v2b, và TernaryCore cùng bo.
2. Bảng số nhịp đo / dự đoán cho các lớp 768 × 768 và kích thước BitNet 2B (2560, 6912), nguồn BRAM và DDR3L.
3. Biểu đồ roofline: phép/nhịp theo băng thông, đánh dấu điểm đo thật.
4. Bảng perplexity cho các cấu hình ở mục 3.2.
5. Thảo luận: khi nào 2:4 đáng giá so với v1b (cùng băng thông, khác diện tích làn và độ chính xác).
