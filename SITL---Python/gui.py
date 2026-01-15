import socket

ESP32_IP = "192.168.4.1"
PORT = 8080

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((ESP32_IP, PORT))

print("Connected to ESP32")

while True:
    try:
        a = int(input("Enter first number: "))
        b = int(input("Enter second number: "))

        cmd = f"NUM {a} {b}\n"
        sock.sendall(cmd.encode())

        response = sock.recv(1024).decode().strip()
        print("ESP32:", response)

    except KeyboardInterrupt:
        break

sock.close()
