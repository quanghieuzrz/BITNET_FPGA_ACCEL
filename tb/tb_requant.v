// =============================================================================
// tb_requant.v  —  Testbench cho rtl/requant.v
//
// Đọc vectors/requant/requant_vectors.hex (do golden/tao_vector_requant.py tạo),
// mỗi dòng 40 bit = {Acc[23:0], S[7:0], Y_dap_an[7:0]}.
// Đưa từng phép thử vào mạch, chờ 1 nhịp, so Y của mạch với đáp án.
// =============================================================================
`timescale 1ns / 1ps

module tb_requant;

    parameter ACC_W   = 24;
    parameter MAX_VEC = 10000;

    // ---- Tín hiệu nối vào mạch cần thử (DUT: Device Under Test) ----
    reg                     clk = 1'b0;
    reg                     rst = 1'b1;
    reg                     in_valid = 1'b0;
    reg  signed [ACC_W-1:0] acc = 0;
    reg         [4:0]       shift = 5'd1;
    wire                    out_valid;
    wire signed [7:0]       y;

    requant #(.ACC_W(ACC_W)) dut (
        .clk(clk), .rst(rst),
        .in_valid(in_valid), .acc(acc), .shift(shift),
        .out_valid(out_valid), .y(y)
    );

    // ---- Đồng hồ 100 MHz: đảo mỗi 5 ns -> chu kỳ 10 ns ----
    always #5 clk = ~clk;

    // ---- Bộ nhớ chứa các phép thử ----
    reg [39:0] vec [0:MAX_VEC-1];
    integer i, so_vec, so_loi;
    reg signed [7:0] y_dap_an;

    initial begin
        // Đánh dấu mọi ô là "chưa có" để đếm số dòng thật sự đọc được
        for (i = 0; i < MAX_VEC; i = i + 1) vec[i] = 40'hx;
        $readmemh("vectors/requant/requant_vectors.hex", vec);
        so_vec = 0;
        while (so_vec < MAX_VEC && vec[so_vec] !== 40'hx) so_vec = so_vec + 1;
        $display("Doc duoc %0d phep thu", so_vec);

        so_loi = 0;
        repeat (2) @(posedge clk);
        rst = 1'b0;

        for (i = 0; i < so_vec; i = i + 1) begin
            // Đặt đầu vào ngay SAU sườn lên, để sườn lên kế tiếp chụp được
            @(negedge clk);
            acc      = vec[i][39:16];
            shift    = vec[i][12:8];
            y_dap_an = vec[i][7:0];
            in_valid = 1'b1;

            @(posedge clk);         // mạch chụp kết quả ở sườn này
            #1;                     // chờ thanh ghi ổn định rồi mới đọc
            if (!out_valid || y !== y_dap_an) begin
                so_loi = so_loi + 1;
                if (so_loi <= 10)
                    $display("SAI #%0d: Acc=%0d S=%0d -> mach Y=%0d, dap an Y=%0d",
                             i, acc, shift, y, y_dap_an);
            end
        end

        @(negedge clk) in_valid = 1'b0;

        if (so_loi == 0)
            $display("DAT: %0d/%0d phep thu khop golden model", so_vec, so_vec);
        else
            $display("KHONG DAT: %0d/%0d phep thu sai", so_loi, so_vec);
        $finish;
    end

endmodule
