import socket
import struct
import threading
import time

HOST = '127.0.0.1'
RECV_PORT = 55000   # Simulink -> Python
SEND_PORT = 55001   # Python -> Simulink

last_value = 0.0

# --- TCP Server to RECEIVE from Simulink ---
def recv_thread():
    global last_value
    recv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    recv_sock.bind((HOST, RECV_PORT))
    recv_sock.listen(1)
    print(f"[RECV] Waiting for Simulink on port {RECV_PORT}...")
    conn, addr = recv_sock.accept()
    print(f"[RECV] Connected to {addr}")
    while True:
        try:
            data = conn.recv(8)
            if not data:
                break
            val = struct.unpack('>d', data)[0]
            last_value = val
            print(f"[RECV] Got: {val}")
        except Exception as e:
            print("[RECV] Error:", e)
            break
    conn.close()
    recv_sock.close()

# --- TCP Server to SEND to Simulink ---
def send_thread():
    send_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    send_sock.bind((HOST, SEND_PORT))
    send_sock.listen(1)
    print(f"[SEND] Waiting for Simulink on port {SEND_PORT}...")
    conn, addr = send_sock.accept()
    print(f"[SEND] Connected to {addr}")
    while True:
        try:
            # Vector to send
            vec = [1.0, 25.0]
            # Pack two doubles -> 16 bytes
            conn.sendall(struct.pack('>2d', *vec))
            print(f"[SEND] Sent: {vec}")
            time.sleep(0.1)
        except Exception as e:
            print("[SEND] Error:", e)
            break
    conn.close()
    send_sock.close()

# --- Run both servers ---
threading.Thread(target=recv_thread, daemon=True).start()
threading.Thread(target=send_thread, daemon=True).start()

# Keep main thread alive
while True:
    time.sleep(0.1)
