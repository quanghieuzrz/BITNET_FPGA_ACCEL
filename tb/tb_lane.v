`timescale 1ns / 1ps
// =============================================================================
// tb_lane.v  -  Testbench tu kiem tra cho rtl/lane.v
//
// Moi "hang" gom so_khuc khuc. Testbench dua tung khuc vao (X, W -1/0/+1),
// tu tinh dap an bang so nguyen (giong Python bai 3), het hang thi so Acc cua mach voi dap an.
// Thu:
//   1. Hang dai nhat 6912 (108 khuc), X toan +127, W toan +1  -> Acc = +877 824 (lon nhat)
//   2. Nhu tren nhung W toan -1                               -> Acc = -877 824 (nho nhat)
//   3. 100 hang ngau nhien, dai 1..40 khuc, co CHEN NHIP TRONG (in_valid = 0, du lieu rac)
//      giua cac khuc: Acc phai giu nguyen khi khong co beat.
// =============================================================================
module tb_lane;

    localparam KHUC = 64, ACC_W = 24;

    reg                     clk = 1'b0, rst = 1'b1;
    reg                     in_valid = 1'b0, khuc_dau = 1'b0;
    reg  [8*KHUC-1:0]       x_khuc = 0;
    reg  [KHUC-1:0]         khac_0 = 0, am = 0;
    wire signed [ACC_W-1:0] acc;

    lane #(.KHUC(KHUC), .ACC_W(ACC_W)) dut (
        .clk(clk), .rst(rst), .in_valid(in_valid), .khuc_dau(khuc_dau),
        .x_khuc(x_khuc), .khac_0(khac_0), .am(am), .acc(acc)
    );

    always #5 clk = ~clk;                       // 100 MHz

    reg  [8*KHUC-1:0] x_moi;                    // du lieu khuc vua tao
    reg  [KHUC-1:0]   k0_moi, am_moi;
    integer h, k, c, so_khuc, xv, wv, dap_an, so_hang, so_loi, seed, che_do;

    // Tao MOT khuc. che_do: 0 = ngau nhien, 1 = toan +127 / W +1, 2 = toan +127 / W -1
    task tao_khuc;
        begin
            for (c = 0; c < KHUC; c = c + 1) begin
                if (che_do == 0) begin
                    xv = $random(seed) % 128;               // -127..127
                    wv = $random(seed) % 2;                 // -1, 0, +1
                end else begin
                    xv = 127;
                    wv = (che_do == 1) ? 1 : -1;
                end
                x_moi[8*c +: 8] = xv;
                k0_moi[c]       = (wv != 0);
                am_moi[c]       = (wv == -1);
                dap_an          = dap_an + wv * xv;         // dap an kieu Python
            end
        end
    endtask

    // Dua khuc vao lane; o che do ngau nhien chen 0..3 nhip trong truoc do
    task gui_khuc(input integer dau);
        begin
            if (che_do == 0)
                repeat ($unsigned($random(seed)) % 4) begin
                    @(negedge clk);
                    in_valid = 1'b0;
                    x_khuc   = {8*KHUC{1'bx}};      // rac: lane phai bo qua
                    khac_0   = {KHUC{1'bx}};
                    am       = {KHUC{1'bx}};
                    khuc_dau = 1'bx;
                    @(posedge clk);
                end
            @(negedge clk);
            x_khuc   = x_moi;
            khac_0   = k0_moi;
            am       = am_moi;
            khuc_dau = dau;
            in_valid = 1'b1;
            @(posedge clk);                         // lane cong khuc nay vao Acc
        end
    endtask

    task chay_hang(input integer n_khuc, input integer cd);
        begin
            che_do = cd; so_khuc = n_khuc; dap_an = 0;
            for (k = 0; k < n_khuc; k = k + 1) begin
                tao_khuc;
                gui_khuc(k == 0);
            end
            @(negedge clk);
            in_valid = 1'b0;
            @(posedge clk);                         // lane co ong dan 2 tang: Acc cham them 1 nhip
            @(negedge clk);
            so_hang = so_hang + 1;
            if (acc !== dap_an[ACC_W-1:0]) begin
                so_loi = so_loi + 1;
                if (so_loi <= 5)
                    $display("SAI hang %0d (%0d khuc): mach Acc=%0d, dap an=%0d",
                             so_hang, so_khuc, acc, dap_an);
            end
        end
    endtask

    initial begin
        so_hang = 0; so_loi = 0; seed = 7;
        repeat (2) @(posedge clk);
        @(negedge clk) rst = 1'b0;

        chay_hang(108, 1);                      // Acc lon nhat  +877 824
        chay_hang(108, 2);                      // Acc nho nhat  -877 824
        for (h = 0; h < 100; h = h + 1)
            chay_hang(1 + ($unsigned($random(seed)) % 40), 0);

        if (so_loi == 0)
            $display("DAT: %0d/%0d hang khop (gom 2 hang bien +/-877824)", so_hang, so_hang);
        else
            $display("KHONG DAT: %0d/%0d hang sai", so_loi, so_hang);
        $finish;
    end

endmodule
