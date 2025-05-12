#!/bin/bash
echo 'Launching Supagrok...'
./update_logs_index.py
python3 supagrok_logger_daemon.py &
