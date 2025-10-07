# HTTP/3 Server Project

A simple HTTP/3 server implementation using Python and the QUIC protocol.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Generate Certificates
```bash
python generate_certs.py
```

### 3. Start Server
```bash
python server.py
```

### 4. Test (in another terminal)
```bash
python client.py
```

## 📡 API Endpoints

- `GET /` - Homepage
- `GET /api/status` - Server status
- `GET /api/data` - Sample data

## 🔧 Requirements

- Python 3.8+
- OpenSSL

## 📝 Project Structure

```
http3-project/
├── server.py           # Main HTTP/3 server
├── client.py           # Test client
├── generate_certs.py   # Certificate generator
├── requirements.txt    # Python dependencies
├── README.md          # This file
└── cert/              # SSL certificates (generated)
    ├── cert.pem
    └── key.pem
```

## 🌐 Access

Once running, visit: `https://localhost:4433`

## ⚠️ Note

This uses self-signed certificates for development only.

## 📄 License

MIT
