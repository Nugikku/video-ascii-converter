import cv2
import numpy as np
import os

# Karakter ASCII gradient gelap → terang (70 level)
ASCII_CHARS = " .'`^\",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"

# Font monospace untuk render
FONT_SCALE = 0.42
FONT = cv2.FONT_HERSHEY_PLAIN
CHAR_W = 7    # lebar karakter dalam piksel output
CHAR_H = 13   # tinggi karakter dalam piksel output


def resize_frame(frame, char_width: int):
    """Resize frame sesuai jumlah karakter horizontal"""
    h, w = frame.shape[:2]
    aspect = h / w
    char_h = int(char_width * aspect * 0.48)
    return cv2.resize(frame, (char_width, char_h))


def frame_to_ascii_image(frame, char_width: int, colored: bool) -> np.ndarray:
    """
    Konversi satu frame video → gambar ASCII art (numpy array BGR)
    """
    resized = resize_frame(frame, char_width)
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    char_rows, char_cols = resized.shape[:2]

    # Ukuran canvas output
    canvas_w = char_cols * CHAR_W
    canvas_h = char_rows * CHAR_H
    canvas = np.zeros((canvas_h, canvas_w, 3), dtype=np.uint8)

    n = len(ASCII_CHARS) - 1

    for y in range(char_rows):
        for x in range(char_cols):
            intensity = int(gray[y, x])
            char_idx = int(intensity / 255.0 * n)
            ch = ASCII_CHARS[char_idx]

            if colored:
                b, g, r = resized[y, x]
                color = (int(b), int(g), int(r))
            else:
                v = intensity
                color = (v, v, v)

            px = x * CHAR_W
            py = y * CHAR_H + CHAR_H - 2  # baseline

            cv2.putText(
                canvas, ch,
                (px, py),
                FONT, FONT_SCALE,
                color, 1,
                cv2.LINE_AA
            )

    return canvas


def save_preview(frame, job_id: str, output_dir: str, char_width: int, colored: bool):
    """Simpan frame pertama sebagai JPEG preview"""
    ascii_frame = frame_to_ascii_image(frame, char_width, colored)
    preview_path = os.path.join(output_dir, f"{job_id}_preview.jpg")
    cv2.imwrite(preview_path, ascii_frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
    return preview_path


def convert_video_to_ascii(
    input_path: str,
    output_path: str,
    char_width: int = 100,
    colored: bool = True,
    output_fps: int = 15,
    progress_callback=None,
):
    """
    Konversi full video ke ASCII art video MP4.
    
    Args:
        input_path   : Path video input
        output_path  : Path video output (.mp4)
        char_width   : Jumlah karakter per baris (resolusi ASCII)
        colored      : True = ASCII berwarna, False = hitam putih
        output_fps   : FPS video output
        progress_callback : fungsi(pct: int) dipanggil tiap update progress
    """
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise RuntimeError(f"Tidak bisa membuka video: {input_path}")

    src_fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    if src_fps <= 0:
        src_fps = 30.0

    # Hitung frame skip agar output sesuai output_fps
    frame_skip = max(1, round(src_fps / output_fps))

    # Baca frame pertama untuk tentukan ukuran canvas output
    ret, first_frame = cap.read()
    if not ret:
        raise RuntimeError("Video tidak bisa dibaca.")

    sample = frame_to_ascii_image(first_frame, char_width, colored)
    out_h, out_w = sample.shape[:2]

    # Simpan preview dari frame pertama
    output_dir = os.path.dirname(output_path)
    job_id = os.path.basename(output_path).replace("_ascii.mp4", "")
    preview_path = os.path.join(output_dir, f"{job_id}_preview.jpg")
    cv2.imwrite(preview_path, sample, [cv2.IMWRITE_JPEG_QUALITY, 85])

    # Setup VideoWriter
    fourcc = cv2.VideoWriter_fourcc(*"avc1")
    out = cv2.VideoWriter(output_path, fourcc, output_fps, (out_w, out_h))

    if not out.isOpened():
        raise RuntimeError("Gagal membuat file output video.")

    # Tulis frame pertama
    out.write(sample)

    frame_idx = 1
    written = 1

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_idx += 1

        # Skip frame sesuai frame_skip
        if (frame_idx - 1) % frame_skip != 0:
            continue

        ascii_frame = frame_to_ascii_image(frame, char_width, colored)
        out.write(ascii_frame)
        written += 1

        # Update progress
        if progress_callback and total_frames > 0:
            pct = min(99, int(frame_idx / total_frames * 100))
            progress_callback(pct)

    cap.release()
    out.release()

    if progress_callback:
        progress_callback(100)

    print(f"[OK] Konversi selesai: {written} frames → {output_path}")
    return output_path
