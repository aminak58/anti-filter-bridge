@echo off
echo Starting Anti-Filter Bridge Server...
python -m anti_filter_bridge.server --certfile certs/cert.pem --keyfile certs/key.pem --host 0.0.0.0 --port 8443
pause
