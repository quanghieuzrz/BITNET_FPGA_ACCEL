`timescale 1ns / 1ps
// =============================================================================
// tb_core_v1_loi.v  -  Kiem tra 4 truong hop LOI cua core_v1 (dac ta muc 8)
//
// Dung du lieu vectors/v1_mac_dinh (K = 128, N = 8: 2 beat X + 4 beat W, 1 beat Y), lam hong co chu y:
//   1. Cau hinh sai (K = 100)      -> khong chay, DONE = 1, ERR = 1 (LOI_CAU_HINH), khong nhan beat nao
//   2. Mot byte X = 0x80 (-128)    -> van chay het, ERR = 3 (LOI_MA_X)
//   3. Mot ma W = 11 (cam)         -> van chay het, ERR = 2 (LOI_MA_W)
//   4. TLAST o beat X dau (sai)    -> van chay het, ERR = 4 (LOI_TLAST)
// Nguyen tac: loi du lieu KHONG lam treo bus: chip van nhan het khung va xuat du beat Y, roi bao DONE.
// =============================================================================
module tb_core_v1_loi;

    reg          clk = 1'b0, rst = 1'b1;
    reg  [12:0]  cfg_k = 0;
    reg  [15:0]  cfg_n = 0;
    reg  [4:0]   cfg_s = 0;
    reg          start = 1'b0;
    wire         busy, done;
    wire [2:0]   err_code;
    wire [31:0]  cycles;
    reg  [511:0] s_tdata = 0;
    reg          s_tvalid = 1'b0, s_tlast = 1'b0;
    wire         s_tready;
    wire [511:0] m_tdata;
    wire         m_tvalid, m_tlast;
    wire         m_tready = 1'b1;               // ben nhan luon san sang

    core_v1 dut (
        .clk(clk), .rst(rst),
        .cfg_k(cfg_k), .cfg_n(cfg_n), .cfg_s(cfg_s), .start(start),
        .busy(busy), .done(done), .err_code(err_code), .cycles(cycles),
        .s_axis_tdata(s_tdata), .s_axis_tvalid(s_tvalid), .s_axis_tready(s_tready), .s_axis_tlast(s_tlast),
        .m_axis_tdata(m_tdata), .m_axis_tvalid(m_tvalid), .m_axis_tready(m_tready), .m_axis_tlast(m_tlast)
    );

    always #5 clk = ~clk;

    reg [511:0] vao [0:5];                      // 2 beat X + 4 beat W
    reg [511:0] tam [0:3];
    integer i, so_beat_y, so_dat, so_ca;

    always @(posedge clk) if (m_tvalid && m_tready) so_beat_y = so_beat_y + 1;

    // Chay mot lan: cfg_k = kk; ca = 2: hong X, 3: hong W, 4: TLAST sai
    task chay(input integer kk, input integer ca, input [2:0] ma_mong_doi, input integer phai_chay);
        integer cho;
        begin
            so_ca = so_ca + 1;
            so_beat_y = 0;
            @(negedge clk);
            cfg_k = kk; cfg_n = 8; cfg_s = 6; start = 1'b1;
            @(negedge clk);
            start = 1'b0;
            if (phai_chay) begin
                for (i = 0; i < 6; i = i + 1) begin
                    s_tdata = vao[i];
                    if (ca == 2 && i == 0) s_tdata[8*5 +: 8] = 8'h80;      // X[5] = -128
                    if (ca == 3 && i == 3) s_tdata[2*17 +: 2] = 2'b11;     // ma W cam
                    s_tlast  = (ca == 4) ? (i == 0) : (i == 5);            // ca 4: TLAST o beat dau
                    s_tvalid = 1'b1;
                    while (!s_tready) @(negedge clk);
                    @(posedge clk);
                    @(negedge clk);
                end
                s_tvalid = 1'b0; s_tlast = 1'b0;
            end
            cho = 0;
            while (!done && cho < 1000) begin @(negedge clk); cho = cho + 1; end

            if (done && err_code == ma_mong_doi && so_beat_y == (phai_chay ? 1 : 0)) begin
                so_dat = so_dat + 1;
                $display("DAT ca %0d: ma loi %0d, %0d beat Y, DONE = 1", ca, err_code, so_beat_y);
            end else
                $display("KHONG DAT ca %0d: done=%b ma loi=%0d (mong %0d), %0d beat Y",
                         ca, done, err_code, ma_mong_doi, so_beat_y);
        end
    endtask

    initial begin
        so_dat = 0; so_ca = 0;
        $readmemh("vectors/v1_mac_dinh/x_in.hex", tam, 0, 1);
        vao[0] = tam[0]; vao[1] = tam[1];
        $readmemh("vectors/v1_mac_dinh/w_in.hex", tam, 0, 3);
        for (i = 0; i < 4; i = i + 1) vao[2 + i] = tam[i];

        repeat (3) @(posedge clk);
        @(negedge clk) rst = 1'b0;

        chay(100, 1, 3'd1, 0);      // cau hinh sai
        chay(128, 2, 3'd3, 1);      // X = 0x80
        chay(128, 3, 3'd2, 1);      // ma W 11
        chay(128, 4, 3'd4, 1);      // TLAST sai cho

        if (so_dat == so_ca) $display("DAT: %0d/%0d ca loi xu ly dung", so_dat, so_ca);
        else                 $display("KHONG DAT: %0d/%0d ca loi", so_dat, so_ca);
        $finish;
    end

endmodule
