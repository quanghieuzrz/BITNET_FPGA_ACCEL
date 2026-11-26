`timescale 1ns / 1ps
// =============================================================================
// requant.v  —  Khối chuẩn hoá đầu ra (Re-quantization), 0 DSP
//
//   Y = Kẹp( (Acc + 2^(S-1)) >>> S , -127, 127 )
//
//   - Acc : số có dấu ACC_W bit (mặc định 24)
//   - S   : số bit dịch, 1 .. 23 (nạp từ thanh ghi Shift_Amt)
//   - Y   : INT8 có dấu, đối xứng [-127, 127]
//
// Độ trễ: 1 nhịp (kết quả được chụp vào thanh ghi ở sườn lên đồng hồ).
// Khớp từng bit với golden/bitnet_golden/chuan_hoa.py :: chuan_hoa().
// =============================================================================
module requant #(
    parameter ACC_W = 24                    // độ rộng bộ tích luỹ
) (
    input  wire                     clk,
    input  wire                     rst,        // reset đồng bộ, mức cao
    input  wire                     in_valid,   // có dữ liệu hợp lệ ở đầu vào
    input  wire signed [ACC_W-1:0]  acc,        // Acc có dấu
    input  wire        [4:0]        shift,      // S (1..23)
    output reg                      out_valid,  // Y hợp lệ (trễ 1 nhịp)
    output reg  signed [7:0]        y           // Y có dấu
);

    // ---------------- Phần TỔ HỢP: tính ngay, không có xung nhịp ----------------

    // 1) Mở rộng Acc thêm 1 bit (giữ dấu) để phép cộng làm tròn không bị tràn
    wire signed [ACC_W:0] acc_mo_rong = {acc[ACC_W-1], acc};

    // 2) Hằng số làm tròn = 2^(S-1)   (S >= 1)
    wire signed [ACC_W:0] lam_tron = $signed({{ACC_W{1'b0}}, 1'b1}) <<< (shift - 5'd1);

    // 3) Cộng làm tròn
    wire signed [ACC_W:0] tong = acc_mo_rong + lam_tron;

    // 4) Dịch phải SỐ HỌC (>>>): giữ dấu cho số âm
    wire signed [ACC_W:0] da_dich = tong >>> shift;

    // 5) Kẹp về [-127, 127]
    localparam signed [ACC_W:0] Y_MAX =  127;
    localparam signed [ACC_W:0] Y_MIN = -127;

    wire signed [7:0] y_kep = (da_dich > Y_MAX) ?  8'sd127 :
                              (da_dich < Y_MIN) ? -8'sd127 :
                                                   da_dich[7:0];

    // ---------------- Phần TUẦN TỰ: thanh ghi, cập nhật ở sườn lên ----------------
    always @(posedge clk) begin
        if (rst) begin
            out_valid <= 1'b0;
            y         <= 8'sd0;
        end else begin
            out_valid <= in_valid;
            if (in_valid)
                y <= y_kep;
        end
    end

endmodule
