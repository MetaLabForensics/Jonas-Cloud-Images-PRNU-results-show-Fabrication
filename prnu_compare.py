import rawpy
import numpy as np
import cv2
import matplotlib.pyplot as plt
import os

def extract_noise_residual(cr2_path):
    with rawpy.imread(cr2_path) as raw:
        rgb = raw.postprocess(use_camera_wb=True, no_auto_bright=True, output_bps=16)

    # Convert to grayscale
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(np.float32)

    # Denoise (wavelet or gaussian blur as proxy)
    denoised = cv2.GaussianBlur(gray, (5,5), 0)

    # Residual = original - denoised
    residual = gray - denoised
    residual /= np.std(residual)  # normalize

    return residual

def compare_prnu(cr2_a, cr2_b):
    res_a = extract_noise_residual(cr2_a)
    res_b = extract_noise_residual(cr2_b)

    # Cross-correlation
    corr = np.sum(res_a * res_b) / (np.sqrt(np.sum(res_a**2)) * np.sqrt(np.sum(res_b**2)))

    # Save residuals for visual inspection
    plt.figure(figsize=(12,5))
    plt.subplot(1,2,1)
    plt.imshow(res_a, cmap='gray')
    plt.title(os.path.basename(cr2_a) + " residual")
    plt.axis("off")

    plt.subplot(1,2,2)
    plt.imshow(res_b, cmap='gray')
    plt.title(os.path.basename(cr2_b) + " residual")
    plt.axis("off")

    outname = f"PRNU_compare_{os.path.basename(cr2_a)}_{os.path.basename(cr2_b)}.png"
    plt.savefig(outname, dpi=200, bbox_inches="tight")
    plt.close()

    print(f"[+] Residuals saved: {outname}")
    print(f"[+] Normalized correlation score: {corr:.4f}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python prnu_compare.py file1.CR2 file2.CR2")
        sys.exit(1)

    compare_prnu(sys.argv[1], sys.argv[2])