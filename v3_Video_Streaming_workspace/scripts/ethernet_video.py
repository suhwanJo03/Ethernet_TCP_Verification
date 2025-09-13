#!/usr/bin/env python3
"""
TCP full-duplex threaded streamer for FPGA
- Send 320x180 BGR24 frames
- Receive 1280x720 ABGR32 frames
- Save first N frames as HEX (AABBGGRR per pixel)
- Save all frames to binary (.bin)
"""

import os
import sys
import socket
import threading
from pathlib import Path
import numpy as np

# ---- Protocol ----
IN_W, IN_H, IN_BPP = 320, 180, 3
IN_FRAME_BYTES = IN_W * IN_H * IN_BPP

OUT_W, OUT_H, OUT_BPP = 1280, 720, 4
OUT_FRAME_BYTES = OUT_W * OUT_H * OUT_BPP

DEFAULT_CHUNK = 1460
DEFAULT_PORT = 6001
DEFAULT_IP = "192.168.1.20"

SAVE_HEX_N = 10
SOCK_TIMEOUT_S = 15

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

def sender_thread(sock: socket.socket, f, num_frames: int, stop_event: threading.Event):
    try:
        total_sent = 0
        for i in range(num_frames):
            if stop_event.is_set():
                break
            frame = f.read(IN_FRAME_BYTES)
            if not frame or len(frame) < IN_FRAME_BYTES:
                print(f"[TX] EOF or short read at frame {i}")
                stop_event.set()
                break

            view = memoryview(frame)
            off = 0
            while off < IN_FRAME_BYTES:
                if stop_event.is_set():
                    break
                n = sock.send(view[off:off+DEFAULT_CHUNK])
                if n <= 0:
                    print("[ERROR][TX] Socket closed during send")
                    stop_event.set()
                    return
                off += n
            total_sent += IN_FRAME_BYTES
            print(f"[TX] frame {i+1}/{num_frames} total={human(total_sent)}")

        try:
            sock.shutdown(socket.SHUT_WR)
        except Exception:
            pass

    except Exception as e:
        print(f"[ERROR][TX] {e}")
        stop_event.set()

def receiver_thread(sock: socket.socket, num_frames: int, out_dir: Path, stop_event: threading.Event):
    try:
        total_recv = 0
        bin_path = out_dir / "output_frames.bin"

        with open(bin_path, "wb") as fout:
            for i in range(num_frames):
                if stop_event.is_set():
                    break

                buf = bytearray(OUT_FRAME_BYTES)
                view = memoryview(buf)
                got = 0
                while got < OUT_FRAME_BYTES:
                    if stop_event.is_set():
                        break
                    chunk = sock.recv(OUT_FRAME_BYTES - got)
                    if not chunk:
                        print(f"[ERROR][RX] Socket closed early: got {got} < {OUT_FRAME_BYTES}")
                        stop_event.set()
                        return
                    view[got:got+len(chunk)] = chunk
                    got += len(chunk)

                frame_out = bytes(buf)
                total_recv += got
                fout.write(frame_out)

                if i < SAVE_HEX_N:
                    save_txt_frame_hex_abgr(frame_out, i, out_dir)

                print(f"[RX] frame {i+1}/{num_frames} total={human(total_recv)}")

    except socket.timeout:
        print("[ERROR][RX] recv timeout")
        stop_event.set()
    except Exception as e:
        print(f"[ERROR][RX] {e}")
        stop_event.set()

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
            try:
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            except Exception:
                pass
            try:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, IN_FRAME_BYTES)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, OUT_FRAME_BYTES)
            except Exception:
                pass
            if SOCK_TIMEOUT_S and SOCK_TIMEOUT_S > 0:
                sock.settimeout(SOCK_TIMEOUT_S)

            print(f"[INFO] Connecting to {DEFAULT_IP}:{DEFAULT_PORT} ...")
            sock.connect((DEFAULT_IP, DEFAULT_PORT))
            print("[INFO] Connected.")

            stop_event = threading.Event()
            try:
                with open(src, "rb") as f:
                    tx_thread = threading.Thread(target=sender_thread, args=(sock, f, num_frames, stop_event), daemon=True)
                    rx_thread = threading.Thread(target=receiver_thread, args=(sock, num_frames, out_dir, stop_event), daemon=True)

                    tx_thread.start()
                    rx_thread.start()

                    tx_thread.join()
                    rx_thread.join()
            finally:
                pass

        print("[SUCCESS] Stream finished.")
        print(f"[INFO] Output binary: {out_dir / 'output_frames.bin'}")

    except KeyboardInterrupt:
        print("\n[INFO] Interrupted.")
    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == "__main__":
    main()
# D:/FSRCNN/Ethernet_py/mp4_2_raw/video_rgb32_stream.bin
# D:/FSRCNN/Ethernet_py/mp4_2_raw/akaps_bgr24_stream.bin
# D:/FSRCNN/Ethernet_py/mp4_2_raw/akaps_rgb24_stream.bin