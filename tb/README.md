# tb/

Testbench tự kiểm tra: đọc vector do golden model sinh (`vectors/...`) bằng `$readmemh`, tự báo `ĐẠT` / `LỖI`.

| File | Kiểm khối | Chạy |
|---|---|---|
| `tb_requant.v` | `rtl/requant.v` | `bash scripts/chay_tb_requant.sh` |
| `tb_w_decode_v1.v` | `rtl/w_decode_v1.v` | `bash scripts/chay_tb_w_decode_v1.sh` |

Testbench khối đỉnh (sau này) chạy mỗi bộ vector hai lần: không trễ và có trễ (`tre_vao.hex`, `tre_ra.hex`).
