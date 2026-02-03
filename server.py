from connection import server_connect
import time

port = 5001
server = server_connect(port)
server.start()

print(f"Server running on port {port} - press ctrl+c to stop")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nShutting Down...")
    server.close()