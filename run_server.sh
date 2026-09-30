#!/bin/bash
cd /working_dir/c_26ecb9670945136c/drunix_pay
export PYTHONPATH=/working_dir/c_26ecb9670945136c/drunix_pay
python3 server.py &
PID=$!
echo "DRUNIX Pay server started with PID $PID on port 8000"
