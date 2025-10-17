# Anti-Filter Bridge - Protocols

This document describes the communication protocols and data formats used by the Anti-Filter Bridge.

## WebSocket Protocol

### Connection Establishment

1. **Handshake**
   - Client initiates WebSocket connection to server
   - Server validates connection and authenticates client
   - Connection is upgraded to WebSocket protocol

2. **Authentication**
   - Client sends authentication token in WebSocket handshake headers
   - Server validates token and establishes session
   - Session ID is assigned for tracking

### Message Format

All messages are JSON-encoded with the following structure:

```json
{
  "type": "message_type",
  "id": "unique_message_id",
  "timestamp": 1633027200,
  "data": {}
}
```

### Message Types

#### 1. Control Messages

**AUTH_REQUEST**
```json
{
  "type": "AUTH_REQUEST",
  "id": "req_12345",
  "timestamp": 1633027200,
  "data": {
    "version": "1.0",
    "token": "auth_token_here"
  }
}
```

**AUTH_RESPONSE**
```json
{
  "type": "AUTH_RESPONSE",
  "id": "req_12345",
  "timestamp": 1633027201,
  "data": {
    "status": "success",
    "session_id": "session_abc123",
    "expires_at": 1633030800
  }
}
```

#### 2. Data Transfer

**DATA**
```json
{
  "type": "DATA",
  "id": "data_78910",
  "timestamp": 1633027202,
  "data": {
    "connection_id": "conn_456",
    "payload": "base64_encoded_data"
  }
}
```

**CONNECTION_OPEN**
```json
{
  "type": "CONNECTION_OPEN",
  "id": "conn_456",
  "timestamp": 1633027203,
  "data": {
    "protocol": "tcp",
    "target_host": "example.com",
    "target_port": 80
  }
}
```

**CONNECTION_CLOSE**
```json
{
  "type": "CONNECTION_CLOSE",
  "id": "conn_456",
  "timestamp": 1633027300,
  "data": {
    "bytes_sent": 1024,
    "bytes_received": 2048,
    "duration": 97
  }
}
```

## SOCKS5 Protocol

The client implements a SOCKS5 proxy that local applications can connect to. The implementation follows RFC 1928.

### Authentication Methods
- No authentication (0x00)
- Username/Password (0x02)

### Commands
- CONNECT (0x01)
- BIND (0x02)
- UDP ASSOCIATE (0x03)

## Security Protocols

### TLS 1.3
- Required for all WebSocket connections
- Cipher suites (in order of preference):
  1. TLS_AES_256_GCM_SHA384
  2. TLS_CHACHA20_POLY1305_SHA256
  3. TLS_AES_128_GCM_SHA256

### Certificate Management
- Server requires valid certificate
- Certificate pinning support
- OCSP stapling

## Error Handling

### Error Response Format
```json
{
  "type": "ERROR",
  "id": "req_12345",
  "timestamp": 1633027400,
  "error": {
    "code": "AUTH_FAILED",
    "message": "Authentication failed: invalid token",
    "retryable": false
  }
}
```

### Error Codes
- `AUTH_FAILED`: Authentication/authorization failure
- `INVALID_REQUEST`: Malformed or invalid request
- `RATE_LIMITED`: Rate limit exceeded
- `CONNECTION_REFUSED`: Could not connect to target
- `TIMEOUT`: Operation timed out
- `INTERNAL_ERROR`: Server error

## Performance Metrics

### Connection Metrics
- Connection setup time
- Round-trip time (RTT)
- Bandwidth usage
- Error rates

### System Metrics
- CPU usage
- Memory usage
- File descriptor usage
- Network I/O

## API Endpoints

### Server API

`POST /api/v1/authenticate`
- Authenticate and get session token

`GET /api/v1/status`
- Get server status and metrics

`GET /ws`
- WebSocket endpoint for tunnel

### Management API

`GET /admin/connections`
- List active connections

`POST /admin/connections/{id}/terminate`
- Terminate a connection

`GET /admin/metrics`
- Get detailed metrics

## Versioning

API versioning is done through the URL path (`/api/v1/`).

## Deprecation Policy
- Major version changes may include breaking changes
- Deprecated features will be supported for at least 6 months
- Deprecation notices will be included in release notes and API responses
