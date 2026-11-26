`timescale 1ns / 1ps
// =============================================================================
// cay_cong.v  -  Cay cong N dau vao (mac dinh 64), cong tung cap theo tang. Thuan to hop, 0 DSP.
//
//   Tang 0: 64 so 8 bit  (dau ra cua 64 sign_sel)
//   Tang 1: 32 so 9 bit  = cong tung cap cua tang 0
//   Tang 2: 16 so 10 bit
//   ...
//   Tang 6:  1 so 14 bit = tong cua ca khuc
//
// Moi tang rong them 1 bit vi cong 2 so co the lon gap doi:
//   |tong| <= 64 x 127 = 8128 < 2^13  -> 14 bit co dau la du.
//
// Tuong duong Python: tong = sum(cac_so)   (learning/buoc3_chia_khuc.py, ham cong_tru)
//
// Ghi chu: ban nay CHUA co thanh ghi pipeline giua cac tang. Neu tong hop tren Vivado
// khong dat 100 MHz thi se them thanh ghi (sau khi do timing).
// =============================================================================
module cay_cong #(
    parameter N    = 64,                       // so dau vao, phai la luy thua cua 2
    parameter IN_W = 8                         // do rong moi dau vao (co dau)
) (
    input  wire [N*IN_W-1:0]                  vao,   // N so, so thu i o bit [IN_W*i +: IN_W]
    output wire signed [IN_W+$clog2(N)-1:0]   tong   // tong N so
);

    localparam L = $clog2(N);                  // so tang cong: 64 -> 6

    genvar lv, i;
    generate
        for (lv = 0; lv <= L; lv = lv + 1) begin : tang
            localparam W = IN_W + lv;          // do rong o tang nay
            localparam M = N >> lv;            // so phan tu o tang nay
            wire signed [W-1:0] s [0:M-1];

            if (lv == 0) begin : nap
                // Tang 0: cat bus vao thanh N so
                for (i = 0; i < M; i = i + 1) begin : cat
                    assign s[i] = vao[IN_W*i +: IN_W];
                end
            end else begin : cong
                // Tang lv: cong tung cap cua tang truoc (tu mo rong dau len W bit)
                for (i = 0; i < M; i = i + 1) begin : cap
                    assign s[i] = tang[lv-1].s[2*i] + tang[lv-1].s[2*i+1];
                end
            end
        end
    endgenerate

    assign tong = tang[L].s[0];

endmodule
