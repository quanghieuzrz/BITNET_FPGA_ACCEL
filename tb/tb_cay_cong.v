`timescale 1ns / 1ps
// =============================================================================
// tb_cay_cong.v  -  Testbench tu kiem tra cho rtl/cay_cong.v (N = 64, 8 bit)
//
// Khong the thu het (255^64 truong hop), nen thu:
//   1. Cac ca bien: toan 0, toan +127, toan -127, xen ke +127/-127,
//      chi MOT so khac 0 o tung vi tri 0..63 (kiem tra noi day dung cho)
//   2. 20 000 bo ngau nhien trong -127..127
// Dap an tinh ngay trong testbench bang vong lap cong so nguyen (giong Python sum()).
// =============================================================================
module tb_cay_cong;

    localparam N = 64, IN_W = 8;

    reg  [N*IN_W-1:0]      vao;
    wire signed [13:0]     tong;

    cay_cong #(.N(N), .IN_W(IN_W)) dut (.vao(vao), .tong(tong));

    integer so[0:N-1];
    integer i, j, dap_an, so_thu, so_loi, seed;

    // Nap mang so[] vao bus, tinh dap an, cho mach on dinh, so sanh
    task thu;
        begin
            dap_an = 0;
            for (j = 0; j < N; j = j + 1) begin
                vao[IN_W*j +: IN_W] = so[j];
                dap_an = dap_an + so[j];
            end
            #1;
            so_thu = so_thu + 1;
            if (tong !== dap_an[13:0]) begin
                so_loi = so_loi + 1;
                if (so_loi <= 5)
                    $display("SAI phep thu %0d: mach tong=%0d, dap an=%0d", so_thu, tong, dap_an);
            end
        end
    endtask

    initial begin
        so_thu = 0; so_loi = 0; seed = 2026;

        // 1. Ca bien
        for (j = 0; j < N; j = j + 1) so[j] = 0;            thu;   // toan 0
        for (j = 0; j < N; j = j + 1) so[j] = 127;          thu;   // tong lon nhat  +8128
        for (j = 0; j < N; j = j + 1) so[j] = -127;         thu;   // tong nho nhat  -8128
        for (j = 0; j < N; j = j + 1) so[j] = (j % 2) ? -127 : 127;  thu;   // xen ke -> 0
        for (i = 0; i < N; i = i + 1) begin                         // mot so khac 0 o vi tri i
            for (j = 0; j < N; j = j + 1) so[j] = 0;
            so[i] = (i % 2) ? -(i + 1) : (i + 1);
            thu;
        end

        // 2. Ngau nhien
        for (i = 0; i < 20000; i = i + 1) begin
            for (j = 0; j < N; j = j + 1) so[j] = ($random(seed) % 128);   // -127..127
            thu;
        end

        if (so_loi == 0)
            $display("DAT: %0d/%0d phep thu khop", so_thu, so_thu);
        else
            $display("KHONG DAT: %0d/%0d phep thu sai", so_loi, so_thu);
        $finish;
    end

endmodule
