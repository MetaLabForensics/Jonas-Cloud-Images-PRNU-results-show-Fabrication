import rawpy
import numpy as np
import cv2
import glob
import matplotlib.pyplot as plt
import os

"""
FULL PRNU PIPELINE
------------------
This script implements the complete PRNU fingerprinting process as recommended
in academic literature (Lukas, Fridrich, Goljan; Hany Farid).

Steps:
1. Extract noise residuals from 20+ CR2 reference images.
2. Average residuals to build a stable PRNU fingerprint.
3. Normalize the fingerprint.
4. Compare a test image residual against the reference fingerprint
   using normalized cross-correlation.
5. Print correlation scores and save residuals for inspection.

Reference Images:
-----------------
- Reference images are CR2 files captured directly from the **same physical camera** under test.
- They must be mapped to the camera source, with documented chain of custody proof.
- The original camera body should remain available for independent inspection.
- Reference images must meet the bar described in forensic literature: minimum of 10–20 untouched RAWs under varying conditions, directly from the camera.

Usage:
python3 full_prnu_pipeline.py /path/to/ref_folder/ /path/to/test_image.CR2
"""

def extract_residual(img_path):
    with rawpy.imread(img_path) as raw:
        rgb = raw.postprocess(use_camera_wb=True, no_auto_bright=True, output_bps=16)

    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(np.float32)
    denoised = cv2.GaussianBlur(gray, (5,5), 0)
    residual = gray - denoised
    residual /= np.std(residual)
    return residual

def build_fingerprint(ref_folder):
    ref_files = glob.glob(os.path.join(ref_folder, "*.CR2"))
    if len(ref_files) < 10:
        raise ValueError("Need at least 10 reference CR2 files for reliable fingerprint")

    residuals = []
    for f in ref_files:
        try:
            res = extract_residual(f)
            residuals.append(res)
            print(f"[+] Processed {f}")
        except Exception as e:
            print(f"[!] Skipping {f}, error: {e}")

    # Align shapes
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

    corr = np.sum(res_test * fingerprint) / (np.sqrt(np.sum(res_test**2)) * np.sqrt(np.sum(fingerprint**2)))

    # Save visualization
    plt.figure(figsize=(12,5))
    plt.subplot(1,2,1)
    plt.imshow(fingerprint, cmap='gray')
    plt.title("Reference PRNU Fingerprint")
    plt.axis("off")

    plt.subplot(1,2,2)
    plt.imshow(res_test, cmap='gray')
    plt.title("Test Image Residual")
    plt.axis("off")

    outname = f"PRNU_test_{os.path.basename(test_img)}.png"
    plt.savefig(outname, dpi=200, bbox_inches="tight")
    plt.close()

    print(f"[+] Saved residual comparison: {outname}")
    print(f"[+] Normalized correlation score: {corr:.4f}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python3 full_prnu_pipeline.py /path/to/ref_folder/ /path/to/test_image.CR2")
        sys.exit(1)

    ref_folder = sys.argv[1]
    test_img = sys.argv[2]

    fp = build_fingerprint(ref_folder)
    compare_to_fingerprint(test_img, fp)
