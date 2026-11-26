#!/usr/bin/env bash
# Ước lượng tài nguyên SƠ BỘ bằng Yosys (synth_xilinx, dòng 7-series) cho từng khối trong rtl/.
# Chỉ để theo dõi xu hướng và kiểm tra DSP = 0; số chính thức lấy từ Vivado (quy tắc R31).
# Cách dùng (đứng ở thư mục gốc repo):  bash scripts/uoc_luong_tai_nguyen.sh
set -e
cd "$(dirname "$0")/.."
printf "%-14s %6s %6s %6s %6s\n" "Khối" "LUT" "CARRY4" "FF" "DSP"
for f in rtl/*.v; do
    top=$(basename "$f" .v)
    yosys -q -p "read_verilog $f; synth_xilinx -family xc7 -top $top -flatten; tee -o build/yosys_$top.txt stat" >/dev/null
    lut=$(grep -E "^\s+LUT[1-6]\s" build/yosys_$top.txt | awk '{s+=$2} END {print s+0}')
    car=$(grep -E "^\s+CARRY4\s" build/yosys_$top.txt | awk '{s+=$2} END {print s+0}')
    ff=$(grep -E "^\s+FD[A-Z]*\s" build/yosys_$top.txt | awk '{s+=$2} END {print s+0}')
    dsp=$(grep -E "^\s+DSP48" build/yosys_$top.txt | awk '{s+=$2} END {print s+0}')
    printf "%-14s %6s %6s %6s %6s\n" "$top" "$lut" "$car" "$ff" "$dsp"
done
