# Quy tắc viết RTL

Mục đích: tránh lỗi kiểu **"mô phỏng đúng, chip thật sai"**. Ví dụ có thật từ dự án TernaryCore (cùng bo Arty A7):
một thanh ghi được gán ở **hai khối `always`**; trình mô phỏng vẫn chạy, nhưng Vivado nối cứng đầu ra về 0 nên chip trả
toàn số 0. Lỗi kiểu này testbench không bắt được, chỉ lộ ra khi tổng hợp.

Mọi file trong `rtl/` phải tuân theo các quy tắc dưới đây. Trước khi gộp code, đi hết danh sách kiểm tra ở cuối.

## 1. Thanh ghi và khối `always`

| # | Quy tắc | Lý do |
|---|---|---|
| R1 | Mỗi thanh ghi **chỉ được gán trong một khối `always`** | Gán ở hai nơi = hai mạch cùng lái một dây; tổng hợp ra kết quả khó đoán |
| R2 | Khối tuần tự dùng `always @(posedge clk)` và **chỉ dùng `<=`** | Mọi thanh ghi cập nhật cùng lúc, đúng như phần cứng |
| R3 | Khối tổ hợp dùng `always @(*)` và **chỉ dùng `=`**, hoặc dùng `assign` | Không lẫn hai kiểu gán |
| R4 | Khối tổ hợp phải **gán đủ mọi nhánh** (gán giá trị mặc định ở đầu khối, `case` có `default`) | Thiếu nhánh → công cụ tạo latch, lệch thời gian |
| R5 | Không dùng `initial` trong RTL tổng hợp, trừ nạp ROM bằng `$readmemh` | `initial` không thành phần cứng (trừ ROM/BRAM) |

## 2. Reset và xung nhịp

| # | Quy tắc |
|---|---|
| R6 | **Một miền xung nhịp** (`clk`, 100 MHz) cho toàn IP. Nếu sau này có miền khác (vd MIG 83 MHz) thì qua FIFO bất đồng bộ của Xilinx, không tự viết |
| R7 | **Reset đồng bộ, mức cao, tên `rst`**: `if (rst) ... else ...` bên trong `always @(posedge clk)` |
| R8 | Chỉ reset các thanh ghi **điều khiển** (valid, bộ đếm, trạng thái FSM). Thanh ghi **dữ liệu** lớn (khúc X, beat W) không cần reset — giảm fanout của `rst` |
| R9 | RESET mềm (bit CTRL[1]) được OR với `rst` thành một tín hiệu reset nội bộ duy nhất |

## 3. Số có dấu

| # | Quy tắc | Ví dụ lỗi |
|---|---|---|
| R10 | Mọi tín hiệu chứa X, Y, Acc khai báo **`signed`** | |
| R11 | Dịch phải số có dấu dùng **`>>>`**, không dùng `>>` | `>>` lấp bit 0 bên trái → Acc âm thành số dương lớn (đã thử với `requant.v`, testbench bắt được) |
| R12 | **Không trộn có dấu và không dấu trong một biểu thức**: chỉ cần một toán hạng không dấu là cả biểu thức thành không dấu | Hằng `1'b1` hay phép ghép `{...}` là không dấu → bọc `$signed(...)` |
| R13 | Mở rộng dấu tường minh khi tăng độ rộng: `{{n{a[MSB]}}, a}` | |
| R14 | Ghi rõ độ rộng mọi hằng số (`8'sd127`, `5'd1`) | Hằng không độ rộng mặc định 32 bit |

## 4. Cấu trúc và đặt tên

| # | Quy tắc |
|---|---|
| R15 | Một module một file, tên file = tên module |
| R16 | Kích thước dùng `parameter` / `localparam` (ACC_W, R, KHUC…), giá trị khớp `golden/bitnet_golden/hang_so.py` |
| R17 | Tín hiệu AXI giữ tên chuẩn: `s_axis_tdata`, `s_axis_tvalid`, `s_axis_tready`, `s_axis_tlast`, `m_axis_*`, `s_axil_*` |
| R18 | FSM: mã trạng thái là `localparam`; một khối `always` cho thanh ghi trạng thái, khối tổ hợp tính trạng thái kế có `default` |
| R19 | Bản sao X gắn `(* dont_touch = "true" *)` ngay tại khai báo, kèm chú thích lý do |
| R20 | Bộ giải mã W (ROM v1b, LUT vị trí v2) viết như hàm tra bảng thuần tổ hợp, tách module riêng để test riêng |

## 5. Bắt tay AXI (theo đặc tả mục 7)

| # | Quy tắc |
|---|---|
| R21 | Một beat chỉ được dùng khi `tvalid && tready` cùng = 1 ở sườn lên. Định nghĩa một dây `wire nhan = s_axis_tvalid && s_axis_tready;` và chỉ dùng dây này |
| R22 | Mọi bộ đếm và Acc chỉ đổi khi `nhan = 1` (gián đoạn → giữ nguyên) |
| R23 | `m_axis_tvalid` khi đã lên 1 thì giữ tới khi `m_axis_tready = 1`; `m_axis_tdata` không đổi trong lúc chờ |
| R24 | `tready` không được phụ thuộc tổ hợp vào `tvalid` của chính cổng đó (luật AXI, tránh vòng tổ hợp) |

## 6. Ràng buộc tài nguyên

| # | Quy tắc |
|---|---|
| R25 | **DSP48 = 0** là yêu cầu của đề tài. Không dùng `*` trên tín hiệu; nếu báo cáo tổng hợp có DSP thì tìm và sửa |
| R26 | Bộ nhớ X dùng BRAM (khai báo mảng + đọc đồng bộ); kiểm tra báo cáo tổng hợp thấy RAMB36/RAMB18, không phải LUTRAM rải rác |

## 7. Không phụ thuộc bo

Bo chạy thật chưa chốt (Arty A7, Zybo Z7-20 hoặc KV260). Lõi phải chạy được trên cả ba mà không sửa.

| # | Quy tắc |
|---|---|
| R27 | Chỉ dùng AMD/Xilinx (Vivado). Không gọi trực tiếp primitive riêng của một dòng chip (`RAMB36E1`, `DSP48E1`…); khai báo mảng để Vivado tự suy ra BRAM |
| R28 | Đóng timing ở **100 MHz trên Artix-7 (-1)**, dòng chậm nhất; dòng nhanh hơn tự khắc qua |
| R29 | Ngân sách: IP ≤ ~50 % LUT của chip nhỏ nhất (XC7Z020, ~53 nghìn LUT), tức ≤ ~26 nghìn LUT, để còn chỗ cho DMA và vỏ |
| R30 | Lõi chỉ biết cổng AXI4-Stream 512 bit và AXI4-Lite. Mọi thứ về RAM, DMA, CPU, chân (XDC) nằm trong vỏ riêng của từng bo |
| R31 | Mỗi khối xong: tổng hợp out-of-context cho cả `xc7a100t`, `xc7z020`, `xck26`; cả ba phải qua timing và ngân sách |

## 8. Kiểm tra trước khi gộp code

Với **mỗi** module mới hoặc vừa sửa:

1. **Lint:** `verilator --lint-only -Wall rtl/<file>.v` (hoặc `iverilog -g2012 -Wall`). Không còn cảnh báo về độ rộng,
   latch, tín hiệu nhiều nguồn.
2. **Mô phỏng tự kiểm tra:** testbench đọc vector golden và tự báo `ĐẠT` / `LỖI`, không so bằng mắt.
   Chạy cả chế độ có gián đoạn (`tre_vao.hex`, `tre_ra.hex`) khi module có cổng AXI.
3. **Thử phá:** cố ý sửa sai một chỗ (vd `>>>` thành `>>`) và xác nhận testbench báo lỗi, rồi trả lại.
4. **Tổng hợp thử** trong Vivado (out-of-context), đọc báo cáo:
   - Không có cảnh báo "multi-driven net", "latch inferred", "signal is tied to constant" bất ngờ.
   - Số DSP = 0. Số LUT, FF, BRAM ghi vào bảng tiến độ.
   - WNS ≥ 0 ở 100 MHz (sau khi ghép vào top), cho cả ba chip ở quy tắc R31.
5. Cập nhật bảng tiến độ trong `README.md`.

Quy tắc kiểm tra số 4 là bài học chính từ TernaryCore: **tổng hợp sớm và thường xuyên**, không đợi tới lúc ghép cả hệ thống.
