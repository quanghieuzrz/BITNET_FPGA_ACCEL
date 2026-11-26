`timescale 1ns / 1ps
// =============================================================================
// tb_w_decode_v1.v  —  Testbench tự kiểm tra cho rtl/w_decode_v1.v
//
// Đọc vectors/w_decode_v1/w_decode_vectors.hex (do golden/tao_vector_w_decode.py tạo).
// Mỗi dòng 1028 bit = {3'b0, loi_ma, am[255:0], khac_0[255:0], w_beat[511:0]}.
// Mạch thuần tổ hợp: đặt beat vào, chờ 1 ns cho tín hiệu ổn định, so 3 đầu ra với đáp án.
// =============================================================================
module tb_w_decode_v1;

    localparam R = 4, KHUC = 64, SO_TS = R*KHUC;
    localparam MAX_VEC = 4000;

    reg  [2*SO_TS-1:0] w_beat = 0;
    wire [SO_TS-1:0]   khac_0, am;
    wire               loi_ma;

    w_decode_v1 #(.R(R), .KHUC(KHUC)) dut (
        .w_beat(w_beat), .khac_0(khac_0), .am(am), .loi_ma(loi_ma)
    );

    reg [1027:0] vec [0:MAX_VEC-1];
    integer i, so_vec, so_loi, so_beat_loi;

    initial begin
        for (i = 0; i < MAX_VEC; i = i + 1) vec[i] = {1028{1'bx}};
        $readmemh("vectors/w_decode_v1/w_decode_vectors.hex", vec);
        so_vec = 0;
        while (so_vec < MAX_VEC && vec[so_vec][0] !== 1'bx) so_vec = so_vec + 1;
        if (so_vec == 0) begin
            $display("LOI: khong doc duoc file vector. Chay golden/tao_vector_w_decode.py truoc.");
            $finish;
        end

        so_loi = 0; so_beat_loi = 0;
        for (i = 0; i < so_vec; i = i + 1) begin
            w_beat = vec[i][511:0];
            #1;
            if (vec[i][1024]) so_beat_loi = so_beat_loi + 1;
            if (khac_0 !== vec[i][767:512] || am !== vec[i][1023:768] || loi_ma !== vec[i][1024]) begin
                so_loi = so_loi + 1;
                if (so_loi <= 5)
                    $display("SAI beat %0d: khop khac_0=%b, khop am=%b, loi_ma mach=%b dap an=%b", i,
                             khac_0 === vec[i][767:512], am === vec[i][1023:768], loi_ma, vec[i][1024]);
            end
        end

        if (so_loi == 0)
            $display("DAT: %0d/%0d beat khop golden model (%0d beat co ma 11 deu duoc bao loi)",
                     so_vec, so_vec, so_beat_loi);
        else
            $display("LOI: %0d/%0d beat sai", so_loi, so_vec);
        $finish;
    end

endmodule
