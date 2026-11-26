#!/usr/bin/env bash
# Kiểm tra khối giải mã W v1: tạo vector -> lint -> biên dịch -> chạy testbench.
# Cách dùng (đứng ở thư mục gốc repo):  bash scripts/chay_tb_w_decode_v1.sh
set -e
cd "$(dirname "$0")/.."
(cd golden && python3 tao_vector_v1.py >/dev/null && python3 tao_vector_bien.py >/dev/null \
            && python3 tao_vector_768.py >/dev/null && python3 tao_vector_w_decode.py)
if command -v verilator >/dev/null; then
    verilator --lint-only -Wall rtl/w_decode_v1.v && echo "Lint: sạch"
else
    echo "Lint: bỏ qua (chưa cài verilator)"
fi
mkdir -p build
iverilog -g2012 -Wall -o build/tb_w_decode_v1.vvp rtl/w_decode_v1.v tb/tb_w_decode_v1.v
vvp -n build/tb_w_decode_v1.vvp
