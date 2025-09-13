import cv2
import numpy as np

def convert_mp4_to_rgb32_stream(mp4_path, output_path, alpha=0x00, fmt='XRGB', max_frames=None):
    """
    MP4를 RGB32 (XRGB8888 or ARGB8888) 형식의 RAW 픽셀 스트림으로 변환하여
    하나의 바이너리 파일로 저장.

    :param mp4_path: 입력 MP4 파일 경로
    :param output_path: 출력 .bin 파일 경로
    :param alpha: MSB (0x00 for XRGB, 0xFF for ARGB)
    :param fmt: 'XRGB' or 'ARGB'
    :param max_frames: 최대 변환 프레임 수 (None이면 전체)
    :return: 총 저장된 프레임 수
    """
    cap = cv2.VideoCapture(mp4_path)
    if not cap.isOpened():
        raise IOError(f"Cannot open video: {mp4_path}")

    frame_count = 0
    with open(output_path, 'wb') as f_out:
        while True:
            ret, frame_bgr = cap.read()
            if not ret or (max_frames is not None and frame_count >= max_frames):
                break

            frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            R = frame_rgb[:, :, 0].astype(np.uint32)
            G = frame_rgb[:, :, 1].astype(np.uint32)
            B = frame_rgb[:, :, 2].astype(np.uint32)

            if fmt == 'XRGB':
                pixel32 = (alpha << 24) | (R << 16) | (G << 8) | B
            elif fmt == 'ARGB':
                pixel32 = (alpha << 24) | (R << 16) | (G << 8) | B
            else:
                raise ValueError("Unsupported format. Use 'XRGB' or 'ARGB'.")

            rgb32_flat = pixel32.flatten().astype(np.uint32)
            f_out.write(rgb32_flat.tobytes())

            frame_count += 1
            if frame_count % 30 == 0:
                print(f"[INFO] Processed {frame_count} frames...")

    cap.release()
    print(f"[DONE] Total frames written: {frame_count}")
    print(f"[SAVED] Output file: {output_path}")
    return frame_count

def convert_mp4_to_bgr24_stream(mp4_path, output_path, max_frames=None):
    cap = cv2.VideoCapture(mp4_path)
    if not cap.isOpened():
        raise IOError(f"Cannot open video: {mp4_path}")

    frame_count = 0
    with open(output_path, "wb") as f_out:
        while True:
            ret, frame_bgr = cap.read()
            if not ret:
                break

            f_out.write(frame_bgr.tobytes())  # 그대로 저장 (BGR888)

            frame_count += 1
            if max_frames is not None and frame_count >= max_frames:
                break

            if frame_count % 30 == 0:
                print(f"[INFO] Processed {frame_count} frames...")

    cap.release()
    print(f"[DONE] Total frames written: {frame_count}")
    print(f"[SAVED] Output file: {output_path}")
    return frame_count

# 사용 예
#if __name__ == "__main__":
#    mp4_path = "mp4_2_raw/akaps_320_180_60fps.mp4"
#    output_bin_path = "mp4_2_raw/akaps_bgr24_stream.bin"
#    convert_mp4_to_rgb32_stream(mp4_path, output_bin_path, alpha=0x00, fmt='XRGB', max_frames=None)

if __name__ == "__main__":
    # 변환할 MP4 파일 경로
    mp4_path = "mp4_2_raw/akaps_320_180_60fps.mp4"    
    # 출력 RAW/BIN 파일 경로
    output_path = "mp4_2_raw/akaps_bgr24_10frame_stream.bin"
    # 변환 실행
    convert_mp4_to_bgr24_stream(
        mp4_path, 
        output_path, 
        max_frames=10     # None이면 전체 프레임
    )