#!/usr/bin/env python3
"""
TCP half-duplex streamer for FPGA
- Send 320x180 BGR24 frames (one by one)
- Receive corresponding 1280x720 ABGR32 frames
- Save first N frames as HEX (AABBGGRR per pixel)
- Save all frames to binary (.bin)
"""

import os
import sys
import socket
from pathlib import Path
import numpy as np

# ---- Protocol ----
IN_W, IN_H, IN_BPP = 320, 180, 3
IN_FRAME_BYTES = IN_W * IN_H * IN_BPP

OUT_W, OUT_H, OUT_BPP = 1280, 720, 4
OUT_FRAME_BYTES = OUT_W * OUT_H * OUT_BPP

TX_CHUNK = 1460          # send chunk size (16 KB for efficiency)
DEFAULT_PORT = 6001
DEFAULT_IP = "192.168.1.20"

SAVE_HEX_N = 10
SOCK_TIMEOUT_S = 60

def human(n: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    i, f = 0, float(n)
    while f >= 1024 and i < len(units) - 1:
        f /= 1024.0
        i += 1
    return f"{f:.1f}{units[i]}"

def save_txt_frame_hex_abgr(frame_bytes: bytes, frame_idx: int, save_dir: Path) -> Path:
    abgr = np.frombuffer(frame_bytes, dtype=np.uint8).reshape((OUT_H, OUT_W, OUT_BPP))
    out_path = save_dir / f"frame_{frame_idx:06d}.txt"
    with open(out_path, "w") as f:
        for y in range(OUT_H):
            line = " ".join(
                f"{abgr[y, x, 0]:02X}{abgr[y, x, 1]:02X}{abgr[y, x, 2]:02X}{abgr[y, x, 3]:02X}"
                for x in range(OUT_W)
            )
            f.write(line + "\n")
    return out_path

def main():
    try:
        file_path = input("Input file path: ").strip()
        src = Path(file_path)
        if not src.exists():
            print(f"[ERROR] File not found: {src}")
            return

        file_size = src.stat().st_size
        if file_size == 0 or file_size % IN_FRAME_BYTES != 0:
            print("[ERROR] Invalid file size.")
            return

        num_frames = file_size // IN_FRAME_BYTES
        total_out = num_frames * OUT_FRAME_BYTES
        out_dir = src.parent / "recv_out"
        out_dir.mkdir(parents=True, exist_ok=True)

        print(f"[INFO] Input: {src} ({human(file_size)})")
        print(f"[INFO] Frames: {num_frames}")
        print(f"[INFO] Expect RX: {human(total_out)}")

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            sock.settimeout(SOCK_TIMEOUT_S)

            print(f"[INFO] Connecting to {DEFAULT_IP}:{DEFAULT_PORT} ...")
            sock.connect((DEFAULT_IP, DEFAULT_PORT))
            print("[INFO] Connected.")

            with open(src, "rb") as f, open(out_dir / "output_frames.bin", "wb") as fout:
                for i in range(num_frames):
                    # ---- TX: send input frame ----
                    frame = f.read(IN_FRAME_BYTES)
                    if not frame or len(frame) < IN_FRAME_BYTES:
                        print(f"[TX] EOF at frame {i}")
                        break

                    off = 0
                    while off < IN_FRAME_BYTES:
                        n = sock.send(frame[off:off+TX_CHUNK])
                        if n <= 0:
                            raise RuntimeError("Socket closed during send")
                        off += n

                    # ---- RX: receive output frame ----
                    buf = bytearray(OUT_FRAME_BYTES)
                    view = memoryview(buf)
                    got = 0
                    while got < OUT_FRAME_BYTES:
                        chunk = sock.recv(OUT_FRAME_BYTES - got)
                        if not chunk:
                            raise RuntimeError(f"Socket closed early (got {got}/{OUT_FRAME_BYTES})")
                        view[got:got+len(chunk)] = chunk
                        got += len(chunk)

                    fout.write(buf)

                    if i < SAVE_HEX_N:
                        save_txt_frame_hex_abgr(buf, i, out_dir)

                    print(f"[FRAME {i+1}/{num_frames}] TX+RX OK")

        print("[SUCCESS] Stream finished.")
        print(f"[INFO] Output binary: {out_dir / 'output_frames.bin'}")

    except KeyboardInterrupt:
        print("\n[INFO] Interrupted.")
    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == "__main__":
    main()
# D:/FSRCNN/Ethernet_py/mp4_2_raw/akaps_bgr24_stream.bin
# D:/FSRCNN/Ethernet_py/mp4_2_raw/video_rgb32_stream.bin
# D:/FSRCNN/Ethernet_py/mp4_2_raw/akaps_rgb24_row_stream.bin