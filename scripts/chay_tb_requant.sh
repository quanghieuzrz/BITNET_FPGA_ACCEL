#!/usr/bin/env bash
# Chạy mô phỏng khối chuẩn hoá: tạo vector bằng golden model -> biên dịch -> chạy testbench.
# Cách dùng (đứng ở thư mục gốc repo):  bash scripts/chay_tb_requant.sh
set -e
cd "$(dirname "$0")/.."
python3 golden/tao_vector_requant.py
mkdir -p build
iverilog -g2012 -o build/tb_requant.vvp rtl/requant.v tb/tb_requant.v
vvp -n build/tb_requant.vvp
