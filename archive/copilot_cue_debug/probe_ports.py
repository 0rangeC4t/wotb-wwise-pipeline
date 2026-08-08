import socket

ports = [8080, 8090, 11987, 11988, 8095, 39485, 42571, 11434]
for port in ports:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1.0)
    result = s.connect_ex(('127.0.0.1', port))
    if result == 0:
        print(f"Port {port} is OPEN")
        # Try to send a test message or just print
    else:
        print(f"Port {port} is closed")
    s.close()
