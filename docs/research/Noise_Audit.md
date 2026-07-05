# Phase 5C Investigation: Noise Audit

I have thoroughly investigated the current noise metrics for the `KEEP` set and performed a comparative analysis against `A7R4 (2475 of 10539).jpg`. 

Here are the mathematical truths behind why the classifier retained this image, and why a simple threshold tweak won't solve the issue.

## 1. Noise Distribution For KEEP
Across the 71 photos that the classifier assigned to `KEEP`, the noise metrics are surprisingly broad:
*   **Minimum noise:** `1.20`
*   **Maximum noise:** `6.68`
*   **Average noise:** `3.78`
*   **Median noise:** `3.81`

## 2. Comparative Analysis: A7R4 (2475)
*   `A7R4 (2475)` scored a `3.74` for Noise.
*   Its Base Classification Score was `64.2` (enough to pass the `60.0` KEEP threshold).
*   It scored `225.7` for Subject Sharpness.

**Answers to your questions:**
1.  **Is its noise score significantly higher than the rest of the KEEP set?**
    No. In fact, its noise score (`3.74`) is slightly *below* the average (`3.78`) for the `KEEP` set. Mathematically, it looks like a perfectly average photo in terms of noise.
2.  **Would a steeper penalty for extreme noise have moved it into REVIEW or REJECT?**
    No. Because its noise is "average", we would have to penalize *average* noise heavily to reject it. Doing so would destroy the current classification curve and reject over half of the valid `KEEP` set.
3.  **Is this an isolated outlier or are there multiple highly noisy images currently classified as KEEP?**
    It is not an isolated outlier. There are multiple highly noisy images currently surviving into the `KEEP` bucket because their extreme Subject Sharpness overpowers the linear noise penalty.

## 3. Outlier Analysis: Top 10 Noisiest KEEP Photos
Here is a snapshot of the actual noisiest photos that survived into `KEEP`:
1.  `Canon EOS 750D (181).jpg` | Noise: `6.68` | Score: `72.1`
2.  `Canon EOS 750D (180).jpg` | Noise: `6.67` | Score: `75.1`
3.  `NIKON 5600 (47).jpg` | Noise: `6.37` | Score: `62.4`
4.  `AERO Canon EOS R5m2 (13).jpg` | Noise: `6.07` | Score: `68.2`
5.  `Canon EOS 750D (91).jpg` | Noise: `5.71` | Score: `66.6`

*(Notice how high the scores are despite the noise. This is because their Subject Sharpness was high enough to offset the noise penalty).*

## 4. Recommendation

> [!WARNING]
> Do **NOT** increase the current noise penalty.

**Why?**
The current `luminance_noise` metric is mathematically "blind" to the perceived editability of the photo. `A7R4 (2475)` likely has a high amount of *shadow noise* due to underexposure, which explodes when you try to edit it (pushing the exposure up). The current noise metric treats it as a "clean" image because the shadows are crushed to black, hiding the noise from the simple mathematical evaluation.

**Recommendation:**
**1. No changes are needed to the current linear noise penalty.**
The problem isn't the *weight* of the penalty; the problem is that our current metric cannot see "hidden" noise in shadows, nor can it detect if noise is aesthetically destroying the subject. 

At a later phase, if we want to address this, we should consider evaluating **Underexposure + Noise** together (e.g., a "Recovery Penalty" where high ISO + Underexposure = massive penalty), rather than just penalizing noise in isolation.
