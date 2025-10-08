#!/usr/bin/env python3
# client_working.py - Working HTTP/3 client for Kali Linux
import asyncio
import json
import ssl
from aioquic.asyncio.client import connect
from aioquic.h3.connection import H3_ALPN, H3Connection
from aioquic.quic.configuration import QuicConfiguration
from aioquic.asyncio.protocol import QuicConnectionProtocol
from aioquic.h3.events import HeadersReceived, DataReceived

class HttpClient(QuicConnectionProtocol):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._http = H3Connection(self._quic)
        self._request_events = {}
        self._request_waiter = {}
        
    async def get(self, path):
        stream_id = self._quic.get_next_available_stream_id()
        
        headers = [
            (b':method', b'GET'),
            (b':scheme', b'https'),
            (b':authority', b'localhost:4433'),
            (b':path', path.encode()),
            (b'user-agent', b'Python-HTTP3-Client'),
        ]
        
        self._http.send_headers(stream_id=stream_id, headers=headers, end_stream=True)
        
        waiter = self._loop.create_future()
        self._request_events[stream_id] = {'headers': None, 'data': b''}
        self._request_waiter[stream_id] = waiter
        
        self.transmit()
        
        return await asyncio.wait_for(waiter, timeout=5.0)
    
    def quic_event_received(self, event):
        for http_event in self._http.handle_event(event):
            if isinstance(http_event, HeadersReceived):
                stream_id = http_event.stream_id
                if stream_id not in self._request_events:
                    self._request_events[stream_id] = {'headers': None, 'data': b''}
                self._request_events[stream_id]['headers'] = dict(http_event.headers)
                
            elif isinstance(http_event, DataReceived):
                stream_id = http_event.stream_id
                if stream_id not in self._request_events:
                    self._request_events[stream_id] = {'headers': None, 'data': b''}
                self._request_events[stream_id]['data'] += http_event.data
                
                if http_event.stream_ended:
                    if stream_id in self._request_waiter and not self._request_waiter[stream_id].done():
                        self._request_waiter[stream_id].set_result(self._request_events[stream_id])

async def test_endpoint(path):
    config = QuicConfiguration(
        alpn_protocols=H3_ALPN,
        is_client=True,
        verify_mode=ssl.CERT_NONE,  # Accept self-signed certificates
    )
    
    print(f"\n🔄 Testing: {path}")
    
    try:
        async with connect(
            host='127.0.0.1',  # Use IP directly
            port=4433,
            configuration=config,
            create_protocol=HttpClient,
        ) as client:
            # Small delay to let connection establish
            await asyncio.sleep(0.1)
            
            # Make request
            response = await client.get(path)
            
            # Parse response
            headers = response.get('headers', {})
            data = response.get('data', b'').decode('utf-8')
            
            status = headers.get(b':status', b'???').decode()
            
            print(f"   ✅ Status: {status}")
            
            # Try to format JSON
            try:
                json_data = json.loads(data)
                print(f"   📦 Response:")
                for line in json.dumps(json_data, indent=6).split('\n'):
                    print(f"      {line}")
            except:
                print(f"   📦 Response: {data[:150]}")
            
            return True
            
    except asyncio.TimeoutError:
        print(f"   ❌ Timeout - Server not responding")
        return False
    except ConnectionRefusedError:
        print(f"   ❌ Connection Refused")
        print(f"   💡 Is server running? Check: sudo netstat -tulpn | grep 4433")
        return False
    except Exception as e:
        print(f"   ❌ Error: {type(e).__name__}")
        if str(e):
            print(f"   Details: {str(e)}")
        return False

async def main():
    print('╔════════════════════════════════════════╗')
    print('║   HTTP/3 Client Test (Python/Kali)    ║')
    print('╚════════════════════════════════════════╝\n')
    
    # Check aioquic
    try:
        import aioquic
        print(f"📚 aioquic version: {aioquic.__version__}")
    except ImportError:
        print("❌ aioquic not found")
        return
    
    # Run tests
    results = []
    
    results.append(await test_endpoint('/api/status'))
    await asyncio.sleep(0.5)
    
    results.append(await test_endpoint('/api/data'))
    
    # Summary
    print(f'\n{"="*44}')
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f'✅ SUCCESS: All {total} tests passed!')
        print('\n🎉 Your HTTP/3 server is working perfectly!')
    else:
        print(f'⚠️  PARTIAL: {passed}/{total} tests passed')
        print('\n💡 Try testing with curl instead:')
        print('   curl --http3-only https://localhost:4433/api/status -k')

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('\n\n⚠️  Interrupted by user')
    except Exception as e:
        print(f'\n❌ Fatal error: {e}')
        import traceback
        traceback.print_exc()
