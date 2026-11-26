`timescale 1ns / 1ps
// =============================================================================
// core_v1.v  -  Chip BitLinear hoan chinh, ban v1 (W 2 bit, R = 4 lane, T = 1 token).  0 DSP.
//
// Dac ta: docs/dac_ta_muc_bit.md muc 4 (thu tu), 6 (beat Y), 7 (AXI4-Stream), 8 (loi).
// Mo hinh tham chieu: golden/bitnet_golden/mo_hinh_giao_dich.py
//
// Khung vao tren s_axis (mot lan chay = mot token x mot lop):
//     [ K/64 beat X ][ ceil(N/4) x K/64 beat W ]     TLAST o beat W cuoi cung
// Cong ra m_axis: ceil(N/64) beat Y, TLAST o beat Y cuoi.
//
// Duong ong (moi tang 1 nhip):
//   T0  nhan beat:  X -> ghi BRAM X  |  W -> giu beat W, doc khuc X thu k tu BRAM
//   T1  giai ma W (w_decode_v1), chep X ra 4 ban sao (moi lane mot ban, dont_touch)
//   T2  4 lane, nua dau: 64 sign_sel + 3 tang cong -> thanh ghi ong dan
//   T3  4 lane, nua sau: 3 tang cong + cong don Acc
//   T4  het hang (khuc cuoi) -> 4 requant
//   T5  dua cac Y cua hang THAT vao hang doi Y (bo hang dem)
//   ra  du 64 Y (hoac het) -> dong goi beat Y, giu toi khi phia nhan lay
//
// Cau hinh (cfg_*) se noi tu thanh ghi AXI4-Lite o vo ngoai (chua lam).
// =============================================================================
module core_v1 #(
    parameter KHUC       = 64,                 // so cot moi khuc = so byte X moi beat
    parameter R          = 4,                  // so lane = so hang W moi beat (v1)
    parameter ACC_W      = 24,                 // do rong Acc
    parameter K_TOI_DA   = 6912,               // K lon nhat (lop Down cua BitNet 2B)
    parameter HANG_DOI_Y = 128                 // hang doi Y: 2 nua, moi nua 64 so
) (
    input  wire          clk,
    input  wire          rst,                  // reset dong bo, muc cao

    // ---- cau hinh + dieu khien ----
    input  wire [12:0]   cfg_k,                // K, boi so cua 64, 64..6912
    input  wire [15:0]   cfg_n,                // N = so hang THAT, 1..65535
    input  wire [4:0]    cfg_s,                // S, 1..23
    input  wire          start,                // xung 1 nhip: bat dau
    output reg           busy,
    output reg           done,                 // giu toi lan start sau
    output reg  [2:0]    err_code,             // 0 = khong loi; 1 cau hinh, 2 ma W, 3 ma X, 4 TLAST
    output reg  [31:0]   cycles,               // so nhip tu start toi done

    // ---- cong vao AXI4-Stream (X roi W) ----
    input  wire [511:0]  s_axis_tdata,
    input  wire          s_axis_tvalid,
    output wire          s_axis_tready,
    input  wire          s_axis_tlast,

    // ---- cong ra AXI4-Stream (Y) ----
    output reg  [511:0]  m_axis_tdata,
    output reg           m_axis_tvalid,
    input  wire          m_axis_tready,
    output reg           m_axis_tlast
);

    localparam SO_KHUC_TOI_DA = K_TOI_DA / KHUC;      // 108
    localparam KW = 7;                                // du dem 0..108
    localparam NW = 15;                               // so nhom hang: toi da ceil(65535/4) = 16384
    localparam LOI_CAU_HINH = 3'd1, LOI_MA_W = 3'd2, LOI_MA_X = 3'd3, LOI_TLAST = 3'd4;

    // =========================================================================
    // 0) Cau hinh chot luc start
    // =========================================================================
    reg  [KW-1:0]  so_khuc;            // K / 64
    reg  [15:0]    n_that;             // N
    reg  [4:0]     s_r;                // S
    reg  [NW-1:0]  so_nhom;            // ceil(N / 4)
    reg  [10:0]    so_beat_y;          // ceil(N / 64)

    wire cau_hinh_dung = (cfg_k[5:0] == 6'd0) && (cfg_k >= 13'd64) && (cfg_k <= K_TOI_DA[12:0]) &&
                         (cfg_n != 16'd0) && (cfg_s >= 5'd1) && (cfg_s <= 5'd23);
    // Chi dung cac bit cao (chia 4, chia 64), bit thap bo di la co y
    /* verilator lint_off UNUSEDSIGNAL */
    wire [16:0] n_cong_3  = {1'b0, cfg_n} + 17'd3;      // ceil(N/4)  = (N+3)  >> 2
    wire [16:0] n_cong_63 = {1'b0, cfg_n} + 17'd63;     // ceil(N/64) = (N+63) >> 6
    /* verilator lint_on UNUSEDSIGNAL */

    // =========================================================================
    // Dieu khien chung
    // =========================================================================
    reg            pha_w;              // 0: dang nhan X, 1: dang nhan W
    reg            het_vao;            // da nhan du khung vao
    reg  [KW-1:0]  dem_x;              // so beat X da nhan
    reg  [KW-1:0]  k;                  // khuc hien tai trong nhom
    reg  [NW-1:0]  nhom;               // nhom hang hien tai
    reg  [7:0]     dem_y;              // so Y dang nam trong hang doi
    reg  [7:0]     giu_cho;            // cho da giu cho cac nhom dang trong duong ong

    // Chi nhan beat khi con du cho trong hang doi Y cho nhom ke (dac ta 7.3 muc 4).
    // Khong phu thuoc s_axis_tvalid (quy tac R24).
    wire cho_trong = ({1'b0, dem_y} + {1'b0, giu_cho} + 9'd4) <= HANG_DOI_Y[8:0];
    assign s_axis_tready = busy && !het_vao && (!pha_w || cho_trong);

    wire nhan     = s_axis_tvalid && s_axis_tready;     // quy tac R21: dung DUY NHAT day nay
    wire khuc_cuoi = (k == so_khuc - 1'b1);
    wire nhom_cuoi = (nhom == so_nhom - 1'b1);
    wire nhan_w_cuoi_nhom = nhan && pha_w && khuc_cuoi;

    // =========================================================================
    // T0a) BRAM X: ghi khi nhan beat X; doc khuc k khi nhan beat W
    // =========================================================================
    reg [8*KHUC-1:0] bo_nho_x [0:SO_KHUC_TOI_DA-1];
    reg [8*KHUC-1:0] x_doc;

    // Ma X 0x80 (-128) bi cam: doi thanh 0x81 (-127) va bao loi (dac ta muc 8, LOI_MA_X)
    reg [8*KHUC-1:0] x_sach;
    reg              co_x_80;
    integer b;
    always @(*) begin
        x_sach  = s_axis_tdata;
        co_x_80 = 1'b0;
        for (b = 0; b < KHUC; b = b + 1)
            if (s_axis_tdata[8*b +: 8] == 8'h80) begin
                x_sach[8*b +: 8] = 8'h81;
                co_x_80 = 1'b1;
            end
    end

    always @(posedge clk) begin
        if (nhan && !pha_w)
            bo_nho_x[dem_x] <= x_sach;
    end

    always @(posedge clk) begin
        x_doc <= bo_nho_x[k];          // doc dong bo -> Vivado suy ra BRAM
    end

    // =========================================================================
    // T0b) Giu beat W + thong tin dieu khien cho tang sau
    // =========================================================================
    reg [511:0]    s1_w;
    reg            s1_valid, s1_dau, s1_cuoi;
    reg [NW-1:0]   s1_nhom;

    always @(posedge clk) begin
        s1_w     <= s_axis_tdata;
        s1_dau   <= (k == {KW{1'b0}});
        s1_cuoi  <= khuc_cuoi;
        s1_nhom  <= nhom;
    end

    // =========================================================================
    // T1) Giai ma W + ban sao X
    // =========================================================================
    wire [R*KHUC-1:0] khac0_w, am_w;
    wire              loi_ma_w;

    w_decode_v1 #(.R(R), .KHUC(KHUC)) u_giai_ma (
        .w_beat(s1_w), .khac_0(khac0_w), .am(am_w), .loi_ma(loi_ma_w)
    );

    reg [R*KHUC-1:0] s2_khac0, s2_am;
    reg              s2_valid, s2_dau, s2_cuoi;
    reg [NW-1:0]     s2_nhom;

    always @(posedge clk) begin
        s2_khac0 <= khac0_w;
        s2_am    <= am_w;
        s2_dau   <= s1_dau;
        s2_cuoi  <= s1_cuoi;
        s2_nhom  <= s1_nhom;
    end

    // =========================================================================
    // T2, T3) R lane + R requant
    // =========================================================================
    reg             s2b_valid, s3_valid;          // s2b: cho them 1 nhip vi lane co ong dan 2 tang
    reg [NW-1:0]    s2b_nhom, s3_nhom;
    wire [8*R-1:0]  y_rq;              // R so Y sau requant
    /* verilator lint_off UNUSEDSIGNAL */
    wire [R-1:0]    rq_valid;          // 4 requant chay dong bo: chi can rq_valid[0]
    /* verilator lint_on UNUSEDSIGNAL */

    genvar lan;
    generate
        for (lan = 0; lan < R; lan = lan + 1) begin : g_lan
            // Ban sao X rieng cho lane nay: giam fanout tu BRAM toi 4 lane (quy tac R19).
            // dont_touch de Vivado KHONG gop 4 ban sao lai thanh 1.
            (* dont_touch = "true" *) reg [8*KHUC-1:0] x_ban;
            always @(posedge clk) x_ban <= x_doc;

            wire signed [ACC_W-1:0] acc;

            lane #(.KHUC(KHUC), .ACC_W(ACC_W)) u_lane (
                .clk(clk), .rst(rst),
                .in_valid (s2_valid),
                .khuc_dau (s2_dau),
                .x_khuc   (x_ban),
                .khac_0   (s2_khac0[KHUC*lan +: KHUC]),
                .am       (s2_am[KHUC*lan +: KHUC]),
                .acc      (acc)
            );

            requant #(.ACC_W(ACC_W)) u_rq (
                .clk(clk), .rst(rst),
                .in_valid (s3_valid),
                .acc      (acc),
                .shift    (s_r),
                .out_valid(rq_valid[lan]),
                .y        (y_rq[8*lan +: 8])
            );
        end
    endgenerate

    always @(posedge clk) begin
        s2b_nhom <= s2_nhom;
        s3_nhom  <= s2b_nhom;
    end

    // =========================================================================
    // T4) Dua Y cua hang THAT vao hang doi (bo hang dem o nhom cuoi)
    // =========================================================================
    reg  [NW-1:0]  s4_nhom;
    always @(posedge clk) begin
        if (s3_valid) s4_nhom <= s3_nhom;
    end

    wire        day_vao   = rq_valid[0];
    wire [16:0] hang_dau  = {s4_nhom, 2'b00};                 // hang dau tien cua nhom
    wire [16:0] con_hang  = {1'b0, n_that} - hang_dau;        // so hang that con lai
    wire [2:0]  so_that   = (con_hang >= 17'd4) ? 3'd4 : con_hang[2:0];

    // Hang doi Y: 32 o, moi o 4 so (= 1 nhom). Nua 0 = o 0..15, nua 1 = o 16..31.
    // Con tro ghi luon chia het cho 4 (chi nhom cuoi moi co the thieu), nen ghi theo o.
    reg  [8*R-1:0] o_y [0:HANG_DOI_Y/R-1];
    reg  [4:0]     o_ghi;              // o se ghi ke tiep
    reg            nua_doc;            // nua se dong goi ke tiep
    reg  [15:0]    y_chua_dong;        // so Y chua dong goi ra beat
    reg  [10:0]    beat_y_dong;        // so beat Y da dong goi
    reg  [10:0]    beat_y_gui;         // so beat Y da duoc phia nhan lay

    // Y cua nhom: lane khong phai hang that -> 0 (de byte thua o beat cuoi = 0x00)
    reg  [8*R-1:0] y_nhom;
    integer l;
    always @(*) begin
        for (l = 0; l < R; l = l + 1)
            y_nhom[8*l +: 8] = (l < so_that) ? y_rq[8*l +: 8] : 8'h00;
    end

    // Dong goi: du 64 so, hoac da het Y (beat cuoi)
    wire        ra_trong  = !m_axis_tvalid || m_axis_tready;   // thanh ghi ra trong (hoac dang duoc lay)
    wire        du_64     = (dem_y >= 8'd64);
    wire        het_y     = (dem_y != 8'd0) && ({8'd0, dem_y} == y_chua_dong);
    wire        dong_goi  = busy && ra_trong && (du_64 || het_y);
    wire [6:0]  so_dong   = du_64 ? 7'd64 : dem_y[6:0];

    reg  [511:0] nua_data;
    integer o;
    always @(*) begin
        for (o = 0; o < 16; o = o + 1)
            nua_data[32*o +: 32] = o_y[{nua_doc, o[3:0]}];
    end

    integer z;
    always @(posedge clk) begin
        if (start && !busy) begin
            for (z = 0; z < HANG_DOI_Y / R; z = z + 1) o_y[z] <= {8*R{1'b0}};
        end else begin
            if (dong_goi)                                  // xoa nua vua dong goi
                for (z = 0; z < 16; z = z + 1) o_y[{nua_doc, z[3:0]}] <= {8*R{1'b0}};
            if (day_vao)
                o_y[o_ghi] <= y_nhom;
        end
    end

    // =========================================================================
    // Thanh ghi dieu khien: bo dem, pha, hang doi, cong ra, loi, done
    // =========================================================================
    wire [7:0] dem_y_moi   = dem_y + (day_vao ? {5'd0, so_that} : 8'd0) - (dong_goi ? {1'b0, so_dong} : 8'd0);
    wire [7:0] giu_cho_moi = giu_cho + (nhan_w_cuoi_nhom ? 8'd4 : 8'd0) - (day_vao ? 8'd4 : 8'd0);
    wire       tlast_dung  = pha_w && khuc_cuoi && nhom_cuoi;   // beat dang nhan co phai beat cuoi?
    wire       nhan_y      = m_axis_tvalid && m_axis_tready;

    always @(posedge clk) begin
        if (rst) begin
            busy <= 1'b0;  done <= 1'b0;  err_code <= 3'd0;  cycles <= 32'd0;
            pha_w <= 1'b0; het_vao <= 1'b0;
            dem_x <= {KW{1'b0}}; k <= {KW{1'b0}}; nhom <= {NW{1'b0}};
            dem_y <= 8'd0; giu_cho <= 8'd0; o_ghi <= 5'd0; nua_doc <= 1'b0;
            y_chua_dong <= 16'd0; beat_y_dong <= 11'd0; beat_y_gui <= 11'd0;
            s1_valid <= 1'b0; s2_valid <= 1'b0; s2b_valid <= 1'b0; s3_valid <= 1'b0;
            m_axis_tvalid <= 1'b0; m_axis_tlast <= 1'b0;
        end else if (start && !busy) begin
            // ---- bat dau mot lan chay ----
            done <= 1'b0;  err_code <= 3'd0;  cycles <= 32'd0;
            pha_w <= 1'b0; het_vao <= 1'b0;
            dem_x <= {KW{1'b0}}; k <= {KW{1'b0}}; nhom <= {NW{1'b0}};
            dem_y <= 8'd0; giu_cho <= 8'd0; o_ghi <= 5'd0; nua_doc <= 1'b0;
            beat_y_dong <= 11'd0; beat_y_gui <= 11'd0;
            s1_valid <= 1'b0; s2_valid <= 1'b0; s2b_valid <= 1'b0; s3_valid <= 1'b0;
            m_axis_tvalid <= 1'b0; m_axis_tlast <= 1'b0;
            so_khuc     <= cfg_k[12:6];
            n_that      <= cfg_n;
            s_r         <= cfg_s;
            so_nhom     <= n_cong_3[16:2];
            so_beat_y   <= n_cong_63[16:6];
            y_chua_dong <= cfg_n;
            if (cau_hinh_dung) begin
                busy <= 1'b1;
            end else begin
                done <= 1'b1;  err_code <= LOI_CAU_HINH;     // khong chay
            end
        end else begin
            if (busy) cycles <= cycles + 32'd1;

            // ---- T0: nhan beat ----
            s1_valid <= nhan && pha_w;
            if (nhan) begin
                if (!pha_w) begin
                    dem_x <= dem_x + 1'b1;
                    if (dem_x == so_khuc - 1'b1) pha_w <= 1'b1;
                end else begin
                    if (khuc_cuoi) begin
                        k <= {KW{1'b0}};
                        nhom <= nhom + 1'b1;
                        if (nhom_cuoi) het_vao <= 1'b1;
                    end else begin
                        k <= k + 1'b1;
                    end
                end
            end

            // ---- T1, T2, T3 ----
            s2_valid  <= s1_valid;
            s2b_valid <= s2_valid && s2_cuoi;     // het hang: lane can them 1 nhip (ong dan)
            s3_valid  <= s2b_valid;

            // ---- hang doi Y ----
            dem_y   <= dem_y_moi;
            giu_cho <= giu_cho_moi;
            if (day_vao) o_ghi <= o_ghi + 1'b1;
            if (dong_goi) begin
                nua_doc     <= ~nua_doc;
                y_chua_dong <= y_chua_dong - {9'd0, so_dong};
                beat_y_dong <= beat_y_dong + 1'b1;
            end

            // ---- cong ra ----
            if (dong_goi) begin
                m_axis_tdata  <= nua_data;
                m_axis_tvalid <= 1'b1;
                m_axis_tlast  <= (beat_y_dong == so_beat_y - 1'b1);
            end else if (nhan_y) begin
                m_axis_tvalid <= 1'b0;
            end

            // ---- xong ----
            if (nhan_y) begin
                beat_y_gui <= beat_y_gui + 1'b1;
                if (beat_y_gui == so_beat_y - 1'b1) begin
                    busy <= 1'b0;
                    done <= 1'b1;
                end
            end

            // ---- loi (giu ma loi DAU TIEN) ----
            if (err_code == 3'd0) begin
                if (nhan && (s_axis_tlast != tlast_dung))     err_code <= LOI_TLAST;
                else if (nhan && !pha_w && co_x_80)            err_code <= LOI_MA_X;
                else if (s1_valid && loi_ma_w)                 err_code <= LOI_MA_W;
            end
        end
    end

endmodule
