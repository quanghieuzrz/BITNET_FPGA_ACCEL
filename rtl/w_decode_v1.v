`timescale 1ns / 1ps
// =============================================================================
// w_decode_v1.v  —  Giải mã một beat W phiên bản v1 (2 bit / trọng số, R = 4 hàng / beat)
//
// Đặc tả: docs/dac_ta_muc_bit.md mục 3.1
//     bit [128r + 2c + 1 : 128r + 2c] = W[hàng r][cột c]      r = 0..3, c = 0..63
//     00 = 0     01 = +1     10 = -1     11 = cấm
//
// Đầu ra cho trọng số thứ i = 64r + c (hàng r, cột c), nằm ở bit [2i+1 : 2i] của beat:
//     khac_0[i] = 1  -> trọng số khác 0, làn được phép cộng/trừ X[c]   (0 -> zero-gating: đầu vào ép về 0)
//     am[i]     = 1  -> trọng số = -1, làn TRỪ X[c] thay vì cộng
//     loi_ma        -> có ít nhất một mã 11 trong beat (đặc tả mục 8: coi trọng số đó = 0, báo LOI_MA_W)
//
// Bảng chân lý của một trọng số (b1 b0 = 2 bit mã):
//     b1 b0 | khac_0 am | ý nghĩa
//      0  0 |   0     0 |  0
//      0  1 |   1     0 | +1
//      1  0 |   1     1 | -1
//      1  1 |   0     0 | cấm -> coi như 0, bật lỗi
//  => khac_0 = b1 XOR b0 ;  am = b1 AND (NOT b0) ;  loi = b1 AND b0
//
// Thuần tổ hợp (quy tắc R20): không xung nhịp, không thanh ghi. Thanh ghi pipeline nằm ở khối trên.
// Tài nguyên ước tính: mỗi trọng số ~1 LUT cho khac_0/am; cây OR 256 đầu vào cho loi_ma.
// =============================================================================
module w_decode_v1 #(
    parameter R    = 4,                 // số hàng (làn) mỗi beat
    parameter KHUC = 64                 // số cột mỗi khúc
) (
    input  wire [2*R*KHUC-1:0] w_beat,  // beat W, 512 bit khi R = 4, KHUC = 64
    output wire [R*KHUC-1:0]   khac_0,  // bit i = trọng số i khác 0
    output wire [R*KHUC-1:0]   am,      // bit i = trọng số i bằng -1
    output wire                loi_ma   // 1 = beat có mã 11 (cấm)
);

    wire [R*KHUC-1:0] ma_cam;           // bit i = trọng số i mang mã 11

    genvar i;
    generate
        for (i = 0; i < R*KHUC; i = i + 1) begin : g_trong_so
            wire b0 = w_beat[2*i];
            wire b1 = w_beat[2*i + 1];
            assign khac_0[i] = b1 ^ b0;
            assign am[i]     = b1 & ~b0;
            assign ma_cam[i] = b1 & b0;
        end
    endgenerate

    assign loi_ma = |ma_cam;

endmodule
