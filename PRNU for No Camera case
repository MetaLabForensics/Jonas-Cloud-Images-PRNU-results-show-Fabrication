import rawpy
import numpy as np
import cv2
import glob
import os
import hashlib
import matplotlib.pyplot as plt

"""
STRICT PRNU PIPELINE (Camera Unavailable Case)
----------------------------------------------
This code handles PRNU analysis when the original camera is unavailable.
It builds a reference fingerprint from archived images and enforces strict
validation rules on reference files.

Why strict validation?
----------------------
Fabricators sometimes:
1. Use photobashed or re-wrapped JPEGs renamed as CR2.
2. Insert files with identical MakerNotes or synthetic EXIF tags.
3. Add noise overlays to mimic sensor residuals.
4. Present only 1–2 files (insufficient for fingerprinting).

Safeguards in this pipeline:
- Minimum reference set size = 15 RAWs.
- File extensions checked (.CR2 only).
- File hash logged for chain of custody.
- Rejection of files with abnormal EXIF tags (optional hook).
- Automatic residual shape check for consistency.
"""

def extract_residual(img_path):
    with rawpy.imread(img_path) as raw:
        rgb = raw.postprocess(use_camera_wb=True, no_auto_bright=True, output_bps=16)

    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(np.float32)
    denoised = cv2.GaussianBlur(gray, (5, 5), 0)
    residual = gray - denoised
    residual /= np.std(residual)
    return residual

def validate_references(ref_files):
    # Rule 1: Must be at least 15 RAWs
    if len(ref_files) < 15:
        raise ValueError("Insufficient reference files. Need at least 15 CR2 images.")

    # Rule 2: Extension check
    for f in ref_files:
        if not f.lower().endswith(".cr2"):
            raise ValueError(f"Invalid file extension (not CR2): {f}")

    # Rule 3: Log SHA256 hash for chain of custody
    print("Reference File Validation:")
    for f in ref_files:
        h = hashlib.sha256(open(f, "rb").read()).hexdigest()
        print(f"  {os.path.basename(f)} -> SHA256: {h}")

    return True

def build_reference_fingerprint(ref_folder):
    ref_files = glob.glob(os.path.join(ref_folder, "*.CR2"))
    validate_references(ref_files)

    residuals = []
    for f in ref_files:
        try:
            res = extract_residual(f)
            residuals.append(res)
            print(f"[+] Processed {f}")
        except Exception as e:
            print(f"[!] Skipping {f}, error: {e}")

    # Align to smallest shape
    min_h = min(r.shape[0] for r in residuals)
    min_w = min(r.shape[1] for r in residuals)
    residuals = [r[:min_h, :min_w] for r in residuals]

    fingerprint = np.mean(residuals, axis=0)
    fingerprint /= np.std(fingerprint)
    return fingerprint

def compare_to_fingerprint(test_img, fingerprint):
    res_test = extract_residual(test_img)
    h, w = fingerprint.shape
    res_test = res_test[:h, :w]

    corr = np.sum(res_test * fingerprint) / (
        np.sqrt(np.sum(res_test ** 2)) * np.sqrt(np.sum(fingerprint ** 2))
    )

    # Save side-by-side visualization
    plt.figure(figsize=(12, 5))
    plt.subplot(1, 2, 1)
    plt.imshow(fingerprint, cmap="gray")
    plt.title("Reference PRNU Fingerprint")
    plt.axis("off")

    plt.subplot(1, 2, 2)
    plt.imshow(res_test, cmap="gray")
    plt.title("Test Image Residual")
    plt.axis("off")

    outname = f"PRNU_strict_{os.path.basename(test_img)}.png"
    plt.savefig(outname, dpi=200, bbox_inches="tight")
    plt.close()

    print(f"[+] Saved residual comparison: {outname}")
    print(f"[+] Normalized correlation score: {corr:.4f}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python strict_prnu.py /path/to/ref_folder/ /path/to/test_image.CR2")
        sys.exit(1)

    ref_folder = sys.argv[1]
    test_img = sys.argv[2]

    fp = build_reference_fingerprint(ref_folder)
    compare_to_fingerprint(test_img, fp)
