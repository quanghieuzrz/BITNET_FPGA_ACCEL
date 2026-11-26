`timescale 1ns / 1ps
// =============================================================================
// tb_core_v1.v  -  Testbench tu kiem tra cho rtl/core_v1.v, dung bo vector cua golden model
//
// Cach chay (dung o thu muc goc repo):
//     vvp -n build/tb_core_v1.vvp +THU_MUC=vectors/v1_mac_dinh            (khong gian doan)
//     vvp -n build/tb_core_v1.vvp +THU_MUC=vectors/v1_mac_dinh +TRE=1     (co gian doan)
//     them +CHAN_THEM=40: ben nhan Y giu TREADY = 0 them 40 nhip moi beat, de ep chip phai
//     chan dau vao khi hang doi Y day (dac ta 7.3 muc 4)
//
// Doc trong THU_MUC: config.txt (K, N, S, SO_BEAT_*), x_in.hex, w_in.hex, y_out.hex,
//                    tre_vao.hex, tre_ra.hex.
// Ben gui: dua X roi W len s_axis, TLAST o beat cuoi; che do TRE: ha TVALID truoc beat i
//          dung tre_vao[i] nhip.
// Ben nhan: so tung beat Y voi y_out.hex; che do TRE: giu TREADY = 0 dung tre_ra[j] nhip
//          khi beat Y thu j da san sang.
// Ket qua phai GIONG HET du co gian doan hay khong (dac ta 7.3).
// =============================================================================
module tb_core_v1;

    localparam MAX_VAO = 20000, MAX_RA = 2000;

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
    reg          m_tready = 1'b0;

    core_v1 dut (
        .clk(clk), .rst(rst),
        .cfg_k(cfg_k), .cfg_n(cfg_n), .cfg_s(cfg_s), .start(start),
        .busy(busy), .done(done), .err_code(err_code), .cycles(cycles),
        .s_axis_tdata(s_tdata), .s_axis_tvalid(s_tvalid), .s_axis_tready(s_tready), .s_axis_tlast(s_tlast),
        .m_axis_tdata(m_tdata), .m_axis_tvalid(m_tvalid), .m_axis_tready(m_tready), .m_axis_tlast(m_tlast)
    );

    always #5 clk = ~clk;                       // 100 MHz

    // ---------------- du lieu vector ----------------
    reg [511:0] vao [0:MAX_VAO-1];              // X roi W
    reg [511:0] ra_dung [0:MAX_RA-1];           // beat Y dap an
    reg [7:0]   tre_vao [0:MAX_VAO-1];
    reg [7:0]   tre_ra  [0:MAX_RA-1];
    reg [511:0] tam [0:MAX_VAO-1];

    reg [1023:0] thu_muc;
    reg [8*80-1:0] dong;
    integer fd, r, K, N, S, so_bx, so_bw, so_by, tong_vao, co_tre;
    integer i, j, so_loi, cho, chan_them;
    integer so_nhip_chan = 0;                   // so nhip ben gui co beat ma chip chua nhan

    always @(posedge clk)
        if (busy && s_tvalid && !s_tready) so_nhip_chan = so_nhip_chan + 1;

    // ---------------- doc config.txt ----------------
    task doc_cau_hinh;
        integer gt;
        begin
            fd = $fopen({thu_muc, "/config.txt"}, "r");
            if (fd == 0) begin
                $display("LOI: khong mo duoc %0s/config.txt", thu_muc);
                $finish;
            end
            while (!$feof(fd)) begin
                r = $fgets(dong, fd);
                if ($sscanf(dong, "K=%d", gt) == 1)         K = gt;
                if ($sscanf(dong, "N=%d", gt) == 1)         N = gt;
                if ($sscanf(dong, "S=%d", gt) == 1)         S = gt;
                if ($sscanf(dong, "SO_BEAT_X=%d", gt) == 1) so_bx = gt;
                if ($sscanf(dong, "SO_BEAT_W=%d", gt) == 1) so_bw = gt;
                if ($sscanf(dong, "SO_BEAT_Y=%d", gt) == 1) so_by = gt;
            end
            $fclose(fd);
        end
    endtask

    // ---------------- ben gui ----------------
    task gui_khung;
        begin
            for (i = 0; i < tong_vao; i = i + 1) begin
                if (co_tre)
                    repeat (tre_vao[i]) begin
                        @(negedge clk);
                        s_tvalid = 1'b0;
                        s_tdata  = {512{1'bx}};          // rac: chip khong duoc dung
                    end
                @(negedge clk);
                s_tdata  = vao[i];
                s_tlast  = (i == tong_vao - 1);
                s_tvalid = 1'b1;
                while (!s_tready) @(negedge clk);       // giu nguyen du lieu khi chip chan
                @(posedge clk);                         // bat tay xay ra o suon nay
            end
            @(negedge clk);
            s_tvalid = 1'b0;
            s_tlast  = 1'b0;
        end
    endtask

    // ---------------- ben nhan ----------------
    integer da_dem;      // 1 = da nap so nhip cho cho beat Y hien tai
    initial begin
        j = 0; so_loi = 0; da_dem = 0; cho = 0;
        forever begin
            @(negedge clk);
            if (m_tvalid) begin
                if (!da_dem) begin
                    cho = (co_tre ? tre_ra[j] : 0) + chan_them;
                    da_dem = 1;
                end
                if (cho > 0) begin
                    m_tready = 1'b0;
                    cho = cho - 1;
                end else begin
                    m_tready = 1'b1;
                end
            end else begin
                m_tready = 1'b0;
            end
            @(posedge clk);
            if (m_tvalid && m_tready) begin
                if (m_tdata !== ra_dung[j] || m_tlast !== (j == so_by - 1)) begin
                    so_loi = so_loi + 1;
                    if (so_loi <= 3)
                        $display("SAI beat Y %0d: tlast mach=%b\n  mach   =%h\n  dap an =%h",
                                 j, m_tlast, m_tdata, ra_dung[j]);
                end
                j = j + 1;
                da_dem = 0;
            end
        end
    end

    // ---------------- chuong trinh chinh ----------------
    initial begin
        if (!$value$plusargs("THU_MUC=%s", thu_muc)) thu_muc = "vectors/v1_mac_dinh";
        if (!$value$plusargs("TRE=%d", co_tre))      co_tre = 0;
        if (!$value$plusargs("CHAN_THEM=%d", chan_them)) chan_them = 0;

        doc_cau_hinh;
        tong_vao = so_bx + so_bw;

        // X va W nam o 2 file: doc rieng roi ghep thanh mot khung
        $readmemh({thu_muc, "/x_in.hex"}, tam, 0, so_bx - 1);
        for (i = 0; i < so_bx; i = i + 1) vao[i] = tam[i];
        $readmemh({thu_muc, "/w_in.hex"}, tam, 0, so_bw - 1);
        for (i = 0; i < so_bw; i = i + 1) vao[so_bx + i] = tam[i];
        $readmemh({thu_muc, "/y_out.hex"}, ra_dung, 0, so_by - 1);
        $readmemh({thu_muc, "/tre_vao.hex"}, tre_vao, 0, tong_vao - 1);
        $readmemh({thu_muc, "/tre_ra.hex"}, tre_ra, 0, so_by - 1);

        repeat (3) @(posedge clk);
        @(negedge clk);
        rst   = 1'b0;
        cfg_k = K;  cfg_n = N;  cfg_s = S;
        start = 1'b1;
        @(negedge clk);
        start = 1'b0;

        gui_khung;

        // cho chip xong (co gioi han de khong treo mai)
        i = 0;
        while (!done && i < 1000000) begin
            @(posedge clk);
            i = i + 1;
        end

        if (!done)
            $display("LOI: chip khong bao DONE");
        else if (j != so_by)
            $display("LOI: nhan %0d/%0d beat Y", j, so_by);
        else if (err_code != 0)
            $display("LOI: chip bao ma loi %0d", err_code);
        else if (so_loi == 0)
            $display("DAT: %0s %0s K=%0d N=%0d: %0d/%0d beat Y khop, %0d nhip, chip chan dau vao %0d nhip",
                     thu_muc, co_tre ? "(co tre)" : "(khong tre)", K, N, so_by, so_by, cycles, so_nhip_chan);
        else
            $display("KHONG DAT: %0s: %0d/%0d beat Y sai", thu_muc, so_loi, so_by);
        $finish;
    end

endmodule
