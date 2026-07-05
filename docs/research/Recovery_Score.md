# Research Report: Feasibility of an Editability / Recovery Score

This report addresses the feasibility of simulating "Real-World Editability" within our existing lightweight JPEG-based pipeline. The goal is to detect photos that appear clean due to crushed shadows but will fall apart when a photographer attempts to recover them.

## 1. Can a lightweight JPEG-based pipeline estimate editability?
**Yes, as a proxy.** 
A JPEG preview has already discarded the deep dynamic range of the RAW file. However, this is actually advantageous for our specific goal: if the 8-bit JPEG preview shows severe compression artifacts, blocking, and noise when its shadows are mathematically "pushed", the actual RAW file will likely also exhibit poor recovery performance (or at least, the preview provides a reliable warning flag). It acts as a worst-case scenario stress test.

## 2. Can shadow recovery be simulated efficiently on previews?
**Yes, extremely efficiently.**
Instead of a complex AI model, shadow recovery can be simulated using a simple **Non-Linear Look-Up Table (LUT)** or **Gamma Correction** via OpenCV. 
*   **Methodology:** We isolate the luminance channel (L in LAB or V in HSV). We apply a steep curve that aggressively lifts values between `0` (black) and `64` (dark gray), mimicking a `+2.0` Exposure or `+100` Shadows slider in Lightroom.
*   Because this is a vectorized operation, OpenCV can apply this curve to a 1080p preview in milliseconds.

## 3. Can noise growth be measured after virtual exposure recovery?
**Yes.**
The current pipeline measures noise across the *entire* image. To measure noise growth, the architecture would look like this:
1.  Generate a "Shadow Mask" from the original image (isolating pixels that are dark).
2.  Apply the Virtual Exposure Recovery curve.
3.  Calculate the Laplacian Variance (our current noise metric) *strictly within the bounds of the Shadow Mask*.
If the noise score in the recovered shadows spikes dramatically compared to the baseline, we know the image contains hidden noise.

## 4. Can color noise emergence be measured?
**Yes.**
Color noise (chroma noise) often manifests as ugly purple and green blotches in recovered shadows. 
*   **Methodology:** Convert the recovered image to the `YCrCb` or `LAB` color space. We then measure the variance of the chroma channels (`Cr`/`Cb` or `A`/`B`) inside the Shadow Mask. 
*   High variance in these channels indicates severe color noise emergence.

## 5. Can detail retention be measured after recovery?
**Yes, but with caveats.**
If a shadow is completely "crushed," lifting it won't reveal details—it will reveal flat, muddy blocks. 
*   **Methodology:** We can run an edge-detection filter (like Canny or Sobel) on the recovered shadow areas. If the recovered area has a high noise score but a very low high-frequency edge density, it means the recovery yielded "mush" rather than usable detail.

## 6. Computational Cost Evaluation
Hardware: **Ryzen 7 4800H (8 Cores) + RTX 3050 Laptop GPU (4GB)**

*   **CPU (Ryzen 7 4800H):** 
    OpenCV is highly optimized for multi-core CPUs using AVX2 instructions. 
    - Creating a mask + applying a LUT: `~2 - 5 ms` per image.
    - Calculating masked noise/variance: `~5 - 10 ms` per image.
    - **Total estimated overhead:** `~10 - 20 ms` per image. 
    This means it would add barely 2–4 seconds of total processing time to a 200-image dataset.
*   **GPU (RTX 3050):** 
    For these specific operations (LUTs and variance), moving the 1080p image matrix from system RAM to VRAM over the PCIe bus would actually take longer than simply computing it on the Ryzen CPU. We should stick to CPU-bound OpenCV for this.

## Architectural Recommendation
An **Editability Score** is highly practical and computationally cheap. 

**Proposed Future Pipeline Addition:**
```python
def calculate_recovery_score(image):
    # 1. Identify shadow regions (< 20% luminance)
    shadow_mask = get_shadows(image)
    
    # 2. Simulate +2.0 Exposure in shadows
    recovered_image = apply_recovery_curve(image)
    
    # 3. Measure noise & color variance ONLY in the recovered shadows
    shadow_noise = calculate_noise(recovered_image, mask=shadow_mask)
    chroma_noise = calculate_color_noise(recovered_image, mask=shadow_mask)
    
    # 4. Return penalty
    return (shadow_noise * weight) + (chroma_noise * weight)
```
This penalty could then be subtracted from the Base Classification Score, cleanly dropping heavily underexposed/noisy images from `KEEP` into `REVIEW` or `REJECT` without touching the existing linear noise penalty.
