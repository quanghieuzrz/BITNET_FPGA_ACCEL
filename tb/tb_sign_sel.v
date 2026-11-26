`timescale 1ns / 1ps
// =============================================================================
// tb_sign_sel.v  -  Testbench tu kiem tra cho rtl/sign_sel.v
//
// Thu HET moi truong hop hop le: x tu -127 den 127 (255 gia tri) x 4 to hop (khac_0, am)
//   = 1020 phep thu. Dap an tinh ngay trong testbench bang so nguyen (giong Python bai 1).
// Khong can file vector vi so truong hop it.
// =============================================================================
module tb_sign_sel;

    reg  signed [7:0] x;
    reg               khac_0, am;
    wire signed [7:0] y;

    sign_sel dut (.x(x), .khac_0(khac_0), .am(am), .y(y));

    integer xi, k, a, dap_an, so_thu, so_loi;

    initial begin
        so_thu = 0;
        so_loi = 0;
        for (xi = -127; xi <= 127; xi = xi + 1) begin
            for (k = 0; k <= 1; k = k + 1) begin
                for (a = 0; a <= 1; a = a + 1) begin
                    x = xi; khac_0 = k; am = a;
                    #1;                                   // cho mach to hop on dinh

                    if (k == 0)      dap_an = 0;          // trong so 0
                    else if (a == 1) dap_an = -xi;        // trong so -1
                    else             dap_an = xi;         // trong so +1

                    so_thu = so_thu + 1;
                    if (y !== dap_an[7:0]) begin
                        so_loi = so_loi + 1;
                        if (so_loi <= 5)
                            $display("SAI: x=%0d khac_0=%0d am=%0d -> mach y=%0d, dap an=%0d",
                                     xi, k, a, y, dap_an);
                    end
                end
            end
        end

        if (so_loi == 0)
            $display("DAT: %0d/%0d phep thu khop", so_thu, so_thu);
        else
            $display("KHONG DAT: %0d/%0d phep thu sai", so_loi, so_thu);
        $finish;
    end

endmodule
