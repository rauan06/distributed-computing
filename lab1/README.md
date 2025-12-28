# RPC Implementation - Remote Procedure Call System

A complete Remote Procedure Call (RPC) system implementation in Go, designed for AWS EC2 deployment. This project implements a custom RPC protocol with JSON serialization, UDP transport, and demonstrates key distributed computing concepts.

## 📋 Project Overview

This lab implements a minimal RPC system consisting of:

- **RPC Server**: Exposes remote functions and handles requests
- **RPC Client**: Makes remote calls with timeout and retry logic
- **Custom Protocol**: JSON-based request/response format
- **Failure Handling**: Demonstrates timeout, retry, and at-most-once semantics

### Lab Objectives Achieved

✅ Implement RPC protocol in Go  
✅ Understand RPC components (client stub, server stub, marshalling)  
✅ Deploy on AWS EC2 instances  
✅ Observe communication failures and retry logic  
✅ Evaluate at-least-once vs at-most-once semantics

## 🏗️ Architecture

```
┌─────────────────┐                      ┌─────────────────┐
│  Client Node    │  UDP/JSON Request    │  Server Node    │
│ (EC2 Instance)  │ ──────────────────>  │ (EC2 Instance)  │
│                 │ <──────────────────  │                 │
└─────────────────┘      Response        └─────────────────┘
```

## 📁 Project Structure

```
rpc-system/
├── server/
│   └── main.go              # RPC Server implementation
├── client/
│   └── main.go              # RPC Client implementation
├── go.mod                   # Go module file
├── README.md                # This file
├── debug_network.sh         # Network troubleshooting script
└── batch_examples.sh        # Example batch commands
```

## 🚀 Quick Start

### Prerequisites

- Go 1.21 or later
- Two AWS EC2 instances (Ubuntu 22.04 recommended)
- Basic network connectivity between instances

### Installation

1. **Clone/Download the project** to both EC2 instances:

```bash
git clone <repository-url> rpc-system
cd rpc-system
```

2. **Compile the server**:

```bash
cd server
go build -o rpc-server
```

3. **Compile the client**:

```bash
cd ../client
go build -o rpc-client
```

## 🔧 Configuration

### Server Configuration

The server accepts command-line arguments:

```bash
# Default: 0.0.0.0:5000
./rpc-server

# Custom host and port
./rpc-server 0.0.0.0 6000

# Show help
./rpc-server --help
```

### Client Configuration

The client supports multiple modes:

```bash
# Interactive mode (default)
./rpc-client --host 127.0.0.1 --port 5000

# Test suite mode
./rpc-client --host 127.0.0.1 --port 5000 --test

# Batch mode (single command)
./rpc-client --host 127.0.0.1 --port 5000 --batch add 5 7

# With custom settings
./rpc-client --host 127.0.0.1 --port 5000 --timeout 5 --retries 3
```

### Client Options

| Flag | Default | Description |
|------|---------|-------------|
| `--host` | `127.0.0.1` | Server hostname or IP |
| `--port` | `5000` | Server port |
| `--timeout` | `2` | Request timeout in seconds |
| `--retries` | `2` | Number of retry attempts |
| `--test` | `false` | Run test suite |
| `--batch` | - | Execute single command and exit |

## 🌐 AWS EC2 Deployment Guide

### Step 1: Launch EC2 Instances

1. Launch 2 Ubuntu 22.04 instances (t2.micro or t3.micro)
2. Name them:
   - `rpc-server-node`
   - `rpc-client-node`
3. Create/use a key pair for SSH access

### Step 2: Configure Security Groups

**For the SERVER instance's security group**, add these inbound rules:

| Type | Protocol | Port Range | Source | Description |
|------|----------|------------|--------|-------------|
| SSH | TCP | 22 | 0.0.0.0/0 | SSH access |
| Custom UDP | UDP | 5000 | 0.0.0.0/0 | RPC Server port |
| All ICMP - IPv4 | ICMP | All | 0.0.0.0/0 | Ping testing |

**For the CLIENT instance**:
- Allow SSH (port 22) from your IP
- Outbound: Allow all traffic

### Step 3: Install Dependencies

On **both instances**:

```bash
sudo apt update
sudo apt install -y golang-go git netcat-openbsd net-tools
```

### Step 4: Deploy the Code

**On the SERVER instance** (e.g., 3.236.41.153):

```bash
# Create project directory
mkdir -p ~/rpc-system/server
cd ~/rpc-system/server

# Copy server/main.go to this directory
# Then compile
go mod init rpc-system/server
go build -o rpc-server

# Start the server
./rpc-server 0.0.0.0 5000
```

**On the CLIENT instance**:

```bash
# Create project directory
mkdir -p ~/rpc-system/client
cd ~/rpc-system/client

# Copy client/main.go to this directory
# Then compile
go mod init rpc-system/client
go build -o rpc-client

# Test connection to server (replace with your server's public IP)
./rpc-client --host 3.236.41.153 --port 5000 --test
```

## 🔌 Available RPC Methods

The server exposes the following methods:

### 1. `add`
Adds two numbers.

```bash
# Interactive mode
> add 5 7
Result: 12

# Batch mode
./rpc-client --host SERVER_IP --port 5000 --batch add 5 7
```

### 2. `subtract`
Subtracts second number from first.

```bash
> subtract 10 3
Result: 7
```

### 3. `multiply`
Multiplies two numbers.

```bash
> multiply 6 7
Result: 42
```

### 4. `divide`
Divides first number by second.

```bash
> divide 20 4
Result: 5.0
```

### 5. `sort`
Sorts a list of numbers.

```bash
> sort 5 2 8 1 9
Result: [1, 2, 5, 8, 9]
```

### 6. `get_time`
Returns current server time.

```bash
> get_time
Result: 2025-12-28 14:30:45
```

## 🧪 Testing

### Run Test Suite

The client includes a comprehensive test suite:

```bash
./rpc-client --host SERVER_IP --port 5000 --test
```

This will test:
- Basic arithmetic operations
- Edge cases (division by zero, etc.)
- Timeout scenarios
- Retry logic
- Invalid requests

### Manual Testing

```bash
# Start server
./rpc-server 0.0.0.0 5000

# In another terminal, run client in interactive mode
./rpc-client --host SERVER_IP --port 5000

# Try commands:
> add 10 20
> sort 5 2 8 1
> get_time
> help
> exit
```

## 🐛 Troubleshooting

### Issue: Cannot Connect to Server

**Most common cause: AWS Security Group not configured**

1. Go to AWS Console → EC2 → Security Groups
2. Find the security group attached to your server instance
3. Edit inbound rules and add:
   - Custom UDP Rule, Port 5000, Source 0.0.0.0/0
   - All ICMP - IPv4, Source 0.0.0.0/0

### Issue: Connection Timeout

**Check if server is running:**

```bash
# On server
ps aux | grep rpc-server
netstat -ulpn | grep :5000
```

**Check firewall (UFW):**

```bash
# On server
sudo ufw status

# If active, allow port 5000
sudo ufw allow 5000/udp
sudo ufw allow proto icmp

# Or disable for testing
sudo ufw disable
```

### Issue: Server Not Binding Correctly

**Verify binding address:**

```bash
# On server, check what interface it's listening on
ss -ulpn | grep :5000

# Should show 0.0.0.0:5000, not 127.0.0.1:5000
```

### Network Debugging Script

Create `debug_network.sh` on both instances:

```bash
#!/bin/bash
echo "=== Network Debug Information ==="
echo "Current IP: $(curl -s ifconfig.me)"
echo "Internal IP: $(hostname -I)"
echo ""
echo "=== Checking Port 5000 ==="
netstat -tulpn | grep :5000 || echo "Port 5000 not found"
echo ""
echo "=== Checking Firewall ==="
sudo ufw status
echo ""
echo "=== Testing Connection ==="
timeout 2 nc -zvu 127.0.0.1 5000 2>&1
```

Run it:

```bash
chmod +x debug_network.sh
./debug_network.sh
```

### Quick Connection Test

**From client to server:**

```bash
# Test ping
ping 3.236.41.153

# Test UDP port
nc -zvu 3.236.41.153 5000

# Test with timeout
timeout 3 nc -zvu 3.236.41.153 5000
```

## 📊 Protocol Specification

### Request Format (JSON)

```json
{
  "request_id": "unique-uuid",
  "method": "add",
  "params": [5, 7]
}
```

### Response Format (JSON)

**Success:**
```json
{
  "request_id": "unique-uuid",
  "status": "OK",
  "result": 12,
  "error": ""
}
```

**Error:**
```json
{
  "request_id": "unique-uuid",
  "status": "ERROR",
  "result": null,
  "error": "division by zero"
}
```

## 🔄 Failure Handling

### Timeout Behavior

- Client waits for configurable timeout (default: 2 seconds)
- After timeout, client retries the request
- Maximum retries configurable (default: 2)

### Retry Logic

```
Request → Timeout → Retry #1 → Timeout → Retry #2 → Give Up
```

### At-Most-Once Semantics

- Each request has a unique UUID
- Server can implement idempotency checks using request_id
- Prevents duplicate execution of non-idempotent operations

## 📈 Performance Considerations

### UDP vs TCP

This implementation uses UDP for:
- Low latency
- Simplified protocol demonstration
- Learning about unreliable transport

**Production considerations:**
- Use TCP for reliability
- Implement connection pooling
- Add authentication/encryption

### Scalability

Current limitations:
- Single-threaded server (Go handles concurrency automatically)
- No load balancing
- No connection pooling

**Improvements for production:**
- Add reverse proxy (nginx)
- Implement rate limiting
- Use connection pooling
- Add monitoring/metrics

## 🎓 Learning Outcomes

By completing this lab, you've learned:

1. **RPC Fundamentals**: Client stub, server stub, marshalling/unmarshalling
2. **Network Programming**: UDP sockets, request/response patterns
3. **Error Handling**: Timeouts, retries, failure scenarios
4. **Distributed Systems**: At-least-once vs at-most-once semantics
5. **Cloud Deployment**: AWS EC2, security groups, network configuration

## 📚 Additional Resources

### Official Documentation

- [Go net package](https://pkg.go.dev/net)
- [Go encoding/json](https://pkg.go.dev/encoding/json)
- [AWS EC2 Documentation](https://docs.aws.amazon.com/ec2/)

### Further Reading

- "Designing Data-Intensive Applications" by Martin Kleppmann
- "Distributed Systems" by Maarten van Steen and Andrew S. Tanenbaum
- [gRPC Documentation](https://grpc.io/) - Production RPC framework

## 🤝 Contributing

Improvements welcome! Consider adding:

- TCP transport option
- TLS/encryption
- Authentication
- Load balancing
- Monitoring/metrics
- More complex data types

## 📝 License

This is an educational project for learning purposes.

## 🆘 Support

If you encounter issues:

1. Check the Troubleshooting section above
2. Verify AWS Security Group settings (most common issue)
3. Review server logs for errors
4. Test with the debug script provided

---

**Happy RPC Learning! 🚀**