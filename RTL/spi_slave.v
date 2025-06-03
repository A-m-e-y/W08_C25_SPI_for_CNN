// spi_slave.v
module spi_slave (
    input         clk,
    input         rst_n,
    input         sclk,
    input         cs_n,
    input         mosi,
    output        miso,

    output reg [31:0] data_out,
    output reg        valid,
    output reg        response_ready
);

    reg [5:0] bit_cnt_rx;
    reg [31:0] shift_rx;
    reg [31:0] tx_buffer;
    reg [31:0] shift_tx;

    reg tx_load;
    reg tx_valid;

    reg sclk_d;
    wire sclk_rising  = (sclk == 1'b1 && sclk_d == 1'b0);
    wire sclk_falling = (sclk == 1'b0 && sclk_d == 1'b1);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            shift_rx        <= 32'd0;
            shift_tx        <= 32'd0;
            tx_buffer       <= 32'd0;
            bit_cnt_rx      <= 6'd0;
            data_out        <= 32'd0;
            valid           <= 1'b0;
            response_ready  <= 1'b0;
            tx_load         <= 1'b0;
            tx_valid        <= 1'b0;
            sclk_d          <= 1'b0;
        end else begin
            sclk_d <= sclk;
            valid <= 1'b0;
            response_ready <= 1'b0;

            // Reset TX valid on new transaction
            if (cs_n) begin
                bit_cnt_rx <= 6'd0;
                tx_valid   <= 1'b0;
            end

            // --- SPI RX Logic (sample on rising edge)
            if (!cs_n && sclk_rising) begin
                shift_rx <= {shift_rx[30:0], mosi};
                bit_cnt_rx <= bit_cnt_rx + 1;

                if (bit_cnt_rx == 6'd31) begin
                    data_out <= {shift_rx[30:0], mosi};
                    valid    <= 1'b1;

                    // Prepare response
                    tx_buffer <= {shift_rx[30:0], mosi} + 1;
                    tx_load <= 1'b1;
                end else begin
                    tx_load <= 1'b0;
                end
            end else begin
                tx_load <= 1'b0;
            end

            // --- Load TX shift register when ready
            if (tx_load) begin
                shift_tx <= tx_buffer;
                tx_valid <= 1'b1;
                response_ready <= 1'b1;
            end

            // --- SPI TX Logic (shift on falling edge)
            if (!cs_n && sclk_falling && tx_valid) begin
                // $display("shift_tx = %08h", shift_tx);
                shift_tx <= {shift_tx[30:0], 1'b0};  // left shift
            end
        end
    end

    assign miso = shift_tx[31];  // MSB first

endmodule
