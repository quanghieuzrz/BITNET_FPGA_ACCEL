# Tong hop core_v1 tren Vivado (out-of-context), lay so LUT / FF / BRAM / DSP va timing o 100 MHz.
#
# Cach chay (dung o thu muc goc repo, trong cua so lenh co Vivado):
#     vivado -mode batch -source scripts/tong_hop_core_v1.tcl
# Doi chip: them  -tclargs xc7z020clg400-1   (Zybo Z7-20)   hoac   xck26-sfvc784-2LV-c  (KV260)
# Mac dinh: xc7a100tcsg324-1 (Arty A7-100T, dong cham nhat, quy tac R28).
#
# Ket qua: build/tong_hop/<chip>/tai_nguyen.txt va timing.txt

# Tu chuyen ve thu muc goc repo (thu muc cha cua scripts/), de chay duoc ca bang
# menu Tools > Run Tcl Script ma khong can cd truoc.
cd [file dirname [file dirname [file normalize [info script]]]]

set chip [expr {[info exists argv] && [llength $argv] > 0 ? [lindex $argv 0] : "xc7a100tcsg324-1"}]
set ra   "build/tong_hop/$chip"
file mkdir $ra

read_verilog {
    rtl/sign_sel.v
    rtl/cay_cong.v
    rtl/lane.v
    rtl/requant.v
    rtl/w_decode_v1.v
    rtl/core_v1.v
}

# Out-of-context: chi tong hop loi, khong gan chan (cong 512 bit nhieu hon so chan cua chip).
synth_design -top core_v1 -part $chip -mode out_of_context

# Dong ho 100 MHz = chu ky 10 ns
create_clock -period 10.000 -name clk [get_ports clk]

opt_design
place_design
route_design

report_utilization    -file $ra/tai_nguyen.txt
report_timing_summary -file $ra/timing.txt -max_paths 10

# In nhanh ra man hinh
set wns [get_property SLACK [get_timing_paths -max_paths 1 -setup]]
puts "=============================================="
puts " Chip: $chip"
puts " WNS = $wns ns   (>= 0: dat 100 MHz, < 0: khong dat)"
puts " Chi tiet: $ra/tai_nguyen.txt, $ra/timing.txt"
puts "=============================================="
