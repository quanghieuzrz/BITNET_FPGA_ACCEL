`timescale 1ns / 1ps
// =============================================================================
// lane.v  -  MOT lane: tinh mot hang W x X, theo tung khuc 64 so, cong don vao Acc.  0 DSP.
//
//   x_khuc (64 so INT8) --+
//                         +--> 64 x sign_sel --> 8 cay_cong (8 -> 1)  --> 8 tong con (11 bit)
//   khac_0, am (64 cap) --+                                                 |
//                                                             [THANH GHI ong dan]   <- cat duong dai
//                                                                           v
//                                     cay_cong (8 -> 1) --> tong khuc (14 bit)
//                                                                           v
//                                         Acc <= (khuc_dau ? 0 : Acc) + tong khuc
//
// Moi beat hop le (in_valid = 1): cong tong cua khuc nay vao Acc.
//   khuc_dau = 1 : day la khuc DAU TIEN cua hang moi -> bo Acc cu, Acc = tong khuc
//   in_valid = 0 : khong co beat (DDR chua kip) -> Acc GIU NGUYEN
//
// Ong dan 2 tang (tu ban sua sau lan tong hop Vivado dau tien):
//   Ban 1 tang: chon dau + 6 tang cong + cong Acc trong 1 nhip = 13,95 ns > 10 ns (WNS -3,97 ns).
//   Cat sau tang cong thu 3 -> moi nua ~7 ns. Gia: Acc co ket qua CHAM THEM 1 NHIP (do tre 2 nhip
//   thay vi 1). Thong luong khong doi: van nhan 1 beat moi nhip.
//
// Tuong duong Python (learning/buoc3_chia_khuc.py):
//     acc = 0                                   # khuc_dau
//     for k in cac_khuc: acc += cong_tru(w_khuc, x_khuc)
//
// Acc rong ACC_W = 24 bit: hang dai nhat 6912 -> |Acc| <= 6912 x 127 = 877 824 < 2^20.
// Do tre: Acc moi co o suon len thu 2 sau beat (TRE_LANE = 2).
// =============================================================================
module lane #(
    parameter KHUC  = 64,                      // so cot moi khuc
    parameter ACC_W = 24                       // do rong Acc
) (
    input  wire                     clk,
    input  wire                     rst,        // reset dong bo, muc cao
    input  wire                     in_valid,   // 1 = co beat hop le o nhip nay
    input  wire                     khuc_dau,   // 1 = khuc dau tien cua hang moi
    input  wire [8*KHUC-1:0]        x_khuc,     // 64 so X, so c o bit [8c +: 8]
    input  wire [KHUC-1:0]          khac_0,     // tu w_decode: bit c = trong so c khac 0
    input  wire [KHUC-1:0]          am,         // tu w_decode: bit c = trong so c bang -1
    output reg  signed [ACC_W-1:0]  acc         // tong don cua hang
);

    localparam TONG_W = 8 + $clog2(KHUC);      // 14 bit khi KHUC = 64

    // ---------------- 1) 64 bo chon dau, chay song song ----------------
    wire [8*KHUC-1:0] da_chon;                 // 64 so: 0, +x hoac -x

    genvar c;
    generate
        for (c = 0; c < KHUC; c = c + 1) begin : g_chon
            sign_sel u_chon (
                .x      (x_khuc[8*c +: 8]),
                .khac_0 (khac_0[c]),
                .am     (am[c]),
                .y      (da_chon[8*c +: 8])
            );
        end
    endgenerate

    // ---------------- 2a) Nua dau cay cong: 8 cay nho, moi cay 8 -> 1 (3 tang) ----------------
    localparam NHOM_CON = 8;                           // so tong con
    localparam CON_N    = KHUC / NHOM_CON;             // 8 so moi tong con
    localparam CON_W    = 8 + $clog2(CON_N);           // 11 bit

    wire [NHOM_CON*CON_W-1:0] tong_con;                // 8 tong con, ghep thanh mot bus

    genvar g;
    generate
        for (g = 0; g < NHOM_CON; g = g + 1) begin : g_con
            cay_cong #(.N(CON_N), .IN_W(8)) u_cay_con (
                .vao  (da_chon[8*CON_N*g +: 8*CON_N]),
                .tong (tong_con[CON_W*g +: CON_W])
            );
        end
    endgenerate

    // ---------------- Thanh ghi ong dan: cat duong dai lam doi ----------------
    reg [NHOM_CON*CON_W-1:0] tong_con_r;               // du lieu: khong can reset (quy tac R8)
    reg                      valid_r, dau_r;

    always @(posedge clk) begin
        tong_con_r <= tong_con;
        dau_r      <= khuc_dau;
    end

    always @(posedge clk) begin
        if (rst) valid_r <= 1'b0;
        else     valid_r <= in_valid;
    end

    // ---------------- 2b) Nua sau cay cong: 8 -> 1 (3 tang) ----------------
    wire signed [TONG_W-1:0] tong_khuc;

    cay_cong #(.N(NHOM_CON), .IN_W(CON_W)) u_cay_cuoi (
        .vao  (tong_con_r),
        .tong (tong_khuc)
    );

    // ---------------- 3) Thanh ghi Acc: cong don qua cac khuc ----------------
    wire signed [ACC_W-1:0] tong_mo_rong = {{(ACC_W-TONG_W){tong_khuc[TONG_W-1]}}, tong_khuc};  // mo rong dau 14 -> 24 bit

    always @(posedge clk) begin
        if (rst)
            acc <= {ACC_W{1'b0}};
        else if (valid_r)
            acc <= (dau_r ? {ACC_W{1'b0}} : acc) + tong_mo_rong;
        // valid_r = 0: giu nguyen acc
    end

endmodule
