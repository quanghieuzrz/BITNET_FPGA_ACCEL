# rtl/

Mã Verilog của IP core. Mọi file tuân theo `docs/quy_tac_rtl.md`.

| File | Khối | Trạng thái |
|---|---|---|
| `requant.v` | Chuẩn hoá: cộng làm tròn, dịch số học, kẹp ±127 | Xong, 3031/3031 vector |
| `w_decode_v1.v` | Giải mã beat W v1 → khac_0, am, loi_ma (thuần tổ hợp) | Xong, 2809/2809 vector |
| `lane.v` | Một làn: chọn ±X/0, cây cộng 64 đầu vào, Acc 24 bit | Tiếp theo |
| `x_buffer.v` | BRAM chứa X và 6 bản sao `dont_touch` | Chưa |
| `bitlinear_top.v` | Khối đỉnh: AXI4-Stream, AXI4-Lite, FSM, hàng đợi Y | Chưa |
