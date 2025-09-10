import socket

# ====== 설정 ======
HOST = '192.168.1.20'     # FPGA 보드 IP
PORT = 6001

WIDTH = 320
HEIGHT = 180
OUTPUT_CHANNEL = 16
NUM_FRAMES = 2

FRAME_BYTES = WIDTH * HEIGHT * OUTPUT_CHANNEL
TOTAL_BYTES = FRAME_BYTES * NUM_FRAMES

SAVE_PATH_TEMPLATE = r"D:\Github_Portfolio\ZCU102_Ethernet_TCP_Verification\v1_Header_Test_workspace\scripts\output_txt\bicubic_output_frame{}.txt"
# =================

def save_as_txt(filename, data, bytes_per_pixel=OUTPUT_CHANNEL):
    with open(filename, "w") as f:
        for i in range(0, len(data), bytes_per_pixel):
            line = " ".join(f"{b:02X}" for b in data[i:i+bytes_per_pixel])
            f.write(line + "\n")

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((HOST, PORT))

print(f"Receiving {NUM_FRAMES} frames...")
total_data = b''

while len(total_data) < TOTAL_BYTES:
    packet = sock.recv(min(4096, TOTAL_BYTES - len(total_data)))
    if not packet:
        break
    total_data += packet
    print(f"Received {len(total_data)}/{TOTAL_BYTES} bytes")

sock.close()

# 프레임 분리
for frame_idx in range(NUM_FRAMES):
    start = frame_idx * FRAME_BYTES
    end = start + FRAME_BYTES
    frame_data = total_data[start:end]
    save_as_txt(SAVE_PATH_TEMPLATE.format(frame_idx + 1), frame_data)
    print(f"Frame {frame_idx+1} saved.")

print("All frames saved successfully.")
