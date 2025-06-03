module cocotb_iverilog_dump();
initial begin
    $dumpfile("sim_build/device_b.fst");
    $dumpvars(0, device_b);
end
endmodule
