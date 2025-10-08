# server.py - Improved HTTP/3 Server
import asyncio
import json
import logging
from datetime import datetime
from aioquic.asyncio import serve
from aioquic.asyncio.protocol import QuicConnectionProtocol
from aioquic.h3.connection import H3_ALPN, H3Connection
from aioquic.h3.events import HeadersReceived, DataReceived, H3Event
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.events import QuicEvent

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class HttpServerProtocol(QuicConnectionProtocol):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._http = H3Connection(self._quic)
        logger.info("New client connected")
        
    def quic_event_received(self, event: QuicEvent):
        try:
            for http_event in self._http.handle_event(event):
                if isinstance(http_event, HeadersReceived):
                    self.handle_request(http_event)
                elif isinstance(http_event, DataReceived):
                    pass  # We don't expect data for GET requests
        except Exception as e:
            logger.error(f"Error handling event: {e}")
    
    def handle_request(self, event: HeadersReceived):
        try:
            headers = dict(event.headers)
            path = headers.get(b':path', b'/').decode('utf-8')
            method = headers.get(b':method', b'GET').decode('utf-8')
            
            logger.info(f"{method} {path}")
            
            if path == '/':
                self.send_response(event.stream_id, 200, self.get_homepage())
            elif path == '/api/status':
                self.send_json_response(event.stream_id, 200, {
                    'status': 'healthy',
                    'protocol': 'HTTP/3',
                    'timestamp': datetime.now().isoformat()
                })
            elif path == '/api/data':
                self.send_json_response(event.stream_id, 200, {
                    'message': 'Sample data from HTTP/3 server',
                    'items': [
                        {'id': 1, 'name': 'Item 1', 'value': 100},
                        {'id': 2, 'name': 'Item 2', 'value': 200},
                        {'id': 3, 'name': 'Item 3', 'value': 300}
                    ]
                })
            else:
                self.send_json_response(event.stream_id, 404, {
                    'error': 'Not Found',
                    'path': path
                })
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            try:
                self.send_json_response(event.stream_id, 500, {
                    'error': 'Internal Server Error',
                    'message': str(e)
                })
            except:
                pass
    
    def send_response(self, stream_id, status_code, body, content_type='text/html'):
        try:
            headers = [
                (b':status', str(status_code).encode()),
                (b'content-type', content_type.encode()),
                (b'content-length', str(len(body)).encode()),
                (b'server', b'HTTP/3-Python-Server'),
            ]
            self._http.send_headers(stream_id=stream_id, headers=headers)
            self._http.send_data(stream_id=stream_id, data=body.encode(), end_stream=True)
            self.transmit()
            logger.debug(f"Sent {status_code} response to stream {stream_id}")
        except Exception as e:
            logger.error(f"Error sending response: {e}")
    
    def send_json_response(self, stream_id, status_code, data):
        body = json.dumps(data, indent=2)
        self.send_response(stream_id, status_code, body, 'application/json')
    
    def get_homepage(self):
        return """<!DOCTYPE html>
<html>
<head>
    <title>HTTP/3 Server</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; background: #f5f5f5; }
        h1 { color: #333; }
        .info { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin: 20px 0; }
        .protocol { color: #4CAF50; font-weight: bold; font-size: 1.2em; }
        .endpoint { background: #fff; padding: 15px; margin: 10px 0; border-left: 4px solid #4CAF50; border-radius: 4px; }
        .endpoint strong { color: #2196F3; }
    </style>
</head>
<body>
    <h1>🚀 HTTP/3 Server Running on Kali Linux</h1>
    <div class="info">
        <p>Protocol: <span class="protocol">HTTP/3 (QUIC)</span></p>
        <p>Port: 4433</p>
        <p>Status: ✅ Active and Ready</p>
    </div>
    <h2>📡 Available Endpoints:</h2>
    <div class="endpoint">
        <strong>GET /api/status</strong><br>
        Returns server health status and timestamp
    </div>
    <div class="endpoint">
        <strong>GET /api/data</strong><br>
        Returns sample JSON data
    </div>
</body>
</html>"""

async def main():
    try:
        # Configuration
        configuration = QuicConfiguration(
            alpn_protocols=H3_ALPN,
            is_client=False,
            max_datagram_frame_size=65536,
        )
        
        # Load SSL certificates
        try:
            configuration.load_cert_chain('cert/cert.pem', 'cert/key.pem')
            logger.info("✅ SSL certificates loaded successfully")
        except FileNotFoundError as e:
            logger.error("❌ Certificate files not found!")
            logger.error("💡 Run: python generate_certs.py")
            return
        
        print('╔════════════════════════════════════════╗')
        print('║     HTTP/3 Server Started              ║')
        print('╠════════════════════════════════════════╣')
        print('║  Protocol: HTTP/3 (QUIC)               ║')
        print('║  Port: 4433                            ║')
        print('║  URL: https://localhost:4433           ║')
        print('╚════════════════════════════════════════╝')
        logger.info("Server is ready to accept connections")
        
        # Start server
        await serve(
            '0.0.0.0',
            4433,
            configuration=configuration,
            create_protocol=HttpServerProtocol,
        )
        
        # Keep server running
        await asyncio.Future()
        
    except OSError as e:
        if 'Address already in use' in str(e):
            logger.error("❌ Port 4433 is already in use!")
            logger.error("💡 Kill the other process or change the port")
        else:
            logger.error(f"❌ OS Error: {e}")
    except Exception as e:
        logger.error(f"❌ Failed to start server: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('\n✅ Server stopped gracefully')
        logger.info("Server shutdown complete")
