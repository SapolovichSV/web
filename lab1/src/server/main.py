import socket
from src.models import REQUEST_BYTES_SIZE, Request
print("Starting server")
HOST = "127.0.0.1"
PORT = 8000
with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as s:
    s.bind((HOST,PORT))
    s.listen()
    conn,addr = s.accept()
    with conn:
        print(f"Connected by {addr}")
        while True:
            try:
                data = Request.deserialize( conn.recv(REQUEST_BYTES_SIZE))
            except Exception as e:
                print(f"error {e}")
                continue
            print(data)
