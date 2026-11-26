`timescale 1ns / 1ps
// =============================================================================
// sign_sel.v  -  Chon dau cho MOT trong so: y = 0, +x hoac -x.  Thuan to hop, 0 DSP.
//
// Nhan 2 tin hieu tu w_decode_v1 (dac ta muc 3.1):
//     khac_0 am | trong so | y
//       0    x  |    0     | 0        (zero-gating: bo qua X)
//       1    0  |   +1     | +x
//       1    1  |   -1     | -x
//
// Vi sao -x khong bi tran: X chi nam trong -127..127 (mau -128 bi cam),
// nen -x cung nam trong -127..127, van vua 8 bit co dau.
//
// Tuong duong Python (learning/buoc1_mot_hang.py):
//     if W == +1: y = x  elif W == -1: y = -x  else: y = 0
// =============================================================================
module sign_sel (
    input  wire signed [7:0] x,        // X, INT8 doi xung -127..127
    input  wire              khac_0,   // 1 = trong so khac 0
    input  wire              am,       // 1 = trong so bang -1
    output wire signed [7:0] y         // 0, +x hoac -x
);

    assign y = (khac_0 == 1'b0) ? 8'sd0 :
               (am     == 1'b1) ? -x    :
                                   x;

endmodule
