# generate_certs.py - Generate SSL certificates
import os
import subprocess
from pathlib import Path

def main():
    # Create cert directory
    cert_dir = Path('cert')
    cert_dir.mkdir(exist_ok=True)
    
    cert_path = cert_dir / 'cert.pem'
    key_path = cert_dir / 'key.pem'
    
    print('🔐 Generating SSL certificates...\n')
    
    try:
        cmd = [
            'openssl', 'req', '-x509',
            '-newkey', 'rsa:4096',
            '-keyout', str(key_path),
            '-out', str(cert_path),
            '-days', '365',
            '-nodes',
            '-subj', '/CN=localhost'
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        
        print('✅ Certificates generated successfully!')
        print(f'   📁 Location: {cert_dir.absolute()}')
        print('   📄 cert.pem')
        print('   🔑 key.pem\n')
        
    except FileNotFoundError:
        print('❌ OpenSSL not found!')
        print('\n💡 Install OpenSSL:')
        print('   • Windows: https://slproweb.com/products/Win32OpenSSL.html')
        print('   • Mac: brew install openssl')
        print('   • Linux: sudo apt-get install openssl')
        exit(1)
    except Exception as e:
        print(f'❌ Error: {e}')
        exit(1)

if __name__ == '__main__':
    main()