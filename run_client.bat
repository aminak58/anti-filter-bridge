@echo off
echo Starting Anti-Filter Bridge Client...
python client.py --server wss://localhost:8443 --local-port 1080 --insecure
pause
