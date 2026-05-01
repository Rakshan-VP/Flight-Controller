import socket
import json
import base64
import numpy as np
import cv2

UDP_IP = "127.0.0.1"
UDP_PORT = 9004

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

cv2.namedWindow("Drone Feed", cv2.WINDOW_NORMAL)
# Set the window to a standard high-res size
cv2.resizeWindow("Drone Feed", 800, 800)

print("Viewer active (Press 'q' to quit)...")

while True:
    try:
        data, _ = sock.recvfrom(65535)
        packet = json.loads(data.decode())
        
        img_bytes = base64.b64decode(packet['img'])
        np_arr = np.frombuffer(img_bytes, dtype=np.uint8)
        img_np = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if img_np is not None:
            # INTER_CUBIC interpolation fixes the blocky/pixelated look
            high_res_img = cv2.resize(img_np, (800, 800), interpolation=cv2.INTER_CUBIC)
            cv2.imshow("Drone Feed", high_res_img)
        
    except Exception as e:
        print(f"Decode error: {e}")
        
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()