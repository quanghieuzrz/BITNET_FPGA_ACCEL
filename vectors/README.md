# vectors/

Thư mục chứa bộ vector kiểm thử do golden model sinh ra. Các file ở đây **không đưa lên GitHub**
(xem `.gitignore`), vì luôn tạo lại được:

```bash
cd golden
python3 tao_vector_v1.py                 # tạo vectors/v1_mac_dinh/
```

Mỗi thư mục con gồm:

| File | Nội dung |
|---|---|
| `x_in.hex` | Các beat X, mỗi dòng 512 bit = 128 ký tự hex |
| `w_in.hex` | Các beat W, đúng thứ tự chip nhận (đã đệm hàng nếu cần) |
| `y_out.hex` | Các beat Y đúng như chip xuất ra bus (đóng gói giống X) |
| `y_expected.hex` | Đáp án Y, mỗi dòng một số INT8 (2 ký tự hex) |
| `tre_vao.hex` | Số nhịp TVALID = 0 trước mỗi beat vào (thử gián đoạn) |
| `tre_ra.hex` | Số nhịp phía nhận giữ TREADY = 0 cho mỗi beat Y (thử chặn ngược) |
| `config.txt` | PHIEN_BAN, MODE, K, N, N_DEM, LAN, S, số beat X/W/Y |
