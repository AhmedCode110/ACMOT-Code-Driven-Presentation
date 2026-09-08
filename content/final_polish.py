"""Final presentation-only cleanup applied after the paper/realtime overrides.

This file intentionally keeps the development ablation separate from the final
live FP16 TrackEval comparison.  It only shortens/clarifies crowded Results
text and locks the official slide-59 numbers to the paper-ready values.
"""

FINAL_OVERRIDES = [
    # Slide 54: keep development evidence explicit and reduce crowding.
    {
        "action": "replace_text",
        "slide": 54,
        "search": "E X A M P L E A3 delivers the strongest MOTA and HOTA*. A4 adds only +0.0007 IDF1, while MOTA and HOTA* fall and IDS rises by 42, so A3 remains the adopted system.",
        "replace": "E X A M P L E A3 gives the largest development-stage accuracy gain. A4 adds no meaningful benefit, so the full AC-MOT architecture stops at A3 before final live tracker selection.",
    },
    {
        "action": "replace_text",
        "slide": 54,
        "search": "Development ablation over 17 sequences. It explains the contribution of each component. The final paper-ready numbers are reported later using live FP16 and official TrackEval.",
        "replace": "Development ablation over 17 sequences. Component contribution only; final paper-ready metrics appear on slide 59 using live FP16 and official TrackEval.",
    },

    # Slide 55: compact wording so chart labels/numbers have more breathing room.
    {
        "action": "replace_text",
        "slide": 55,
        "search": "E X A M P L E This is the step-by-step engineering story: tune the tracker, then add adaptive thresholding, then add adaptive resolution. A3 gives the largest accuracy jump while remaining above the 25 FPS line. The final tracker tuning is selected in the next evidence layer.",
        "replace": "E X A M P L E The progression is deliberate: Baseline -> Tuned ByteTrack -> Adaptive Threshold/NMS -> Adaptive Resolution. A3 gives the largest accuracy step and remains above 25 FPS.",
    },

    # Slide 56: preserve attribution while avoiding oversized multi-line callouts.
    {
        "action": "replace_text",
        "slide": 56,
        "search": "A0 to A1 +0.0265 MOTA and 360 fewer IDS. Tracker tuning is a clean first gain.",
        "replace": "A0 -> A1: +0.0265 MOTA and 360 fewer IDS. Tracker tuning gives the first clean gain.",
    },
    {
        "action": "replace_text",
        "slide": 56,
        "search": "A1 to A2 +0.0245 MOTA and 12 fewer IDS. Adaptive thresholding improves recall without an identity penalty.",
        "replace": "A1 -> A2: +0.0245 MOTA and 12 fewer IDS. Adaptive threshold/NMS improves recall without an identity penalty.",
    },
    {
        "action": "replace_text",
        "slide": 56,
        "search": "A2 to A3 +0.0642 MOTA — the largest step. It also adds 559 IDS and costs ~1 FPS; A3 is adopted with this trade-off disclosed.",
        "replace": "A2 -> A3: +0.0642 MOTA, the largest step. It adds 559 IDS and costs ~1 FPS; the trade-off is reported explicitly.",
    },
    {
        "action": "replace_text",
        "slide": 56,
        "search": "A3 proves the adaptive-resolution contribution. Then the final live stage keeps the same architecture and only tunes ByteTrack to choose the best publishable operating point.",
        "replace": "A3 proves the adaptive-resolution contribution. The final live stage keeps this architecture and tunes only ByteTrack for the selected operating point.",
    },

    # Slide 58: compact long callouts; this remains development evidence.
    {
        "action": "replace_text",
        "slide": 58,
        "search": "All five systems remain real-time The recorded run ranges from 28.9 to 30.8 FPS on the T4. A3's accuracy gain costs only 6.3% speed versus A0.",
        "replace": "All tested ablations remain real-time: 28.9-30.8 FPS on the T4. A3 costs 6.3% speed versus A0 while delivering the largest accuracy gain.",
    },
    {
        "action": "replace_text",
        "slide": 58,
        "search": "Identity result depends on the evaluation gate Legacy main: A3 IDS 2695 vs A0 2508. IoU ≥ 0.50 replay: A3 IDS 1092 vs A0 1237. Report both; do not overclaim.",
        "replace": "Identity is evaluator-dependent in the development run: legacy IDS A3 2695 vs A0 2508; IoU >= 0.50 replay A3 1092 vs A0 1237. Both are reported.",
    },

    # Slide 59: exact final live FP16 / official TrackEval comparison.
    {
        "action": "replace_text",
        "slide": 59,
        "search": "MOTA  baseline 19.718  ->  AC-MOT 22.999   GAIN +3.281 points",
        "replace": "MOTA   Baseline 19.718  ->  AC-MOT 22.999   (+3.281 points)",
    },
    {
        "action": "replace_text",
        "slide": 59,
        "search": "IDF1  baseline 32.716  ->  AC-MOT 40.021   GAIN +7.305 points",
        "replace": "IDF1   Baseline 32.716  ->  AC-MOT 40.021   (+7.305 points)",
    },
    {
        "action": "replace_text",
        "slide": 59,
        "search": "HOTA improves from 28.418 to 33.017. IDS drops from 1238 to 994, giving 244 fewer identity switches. Processing remains real-time at 37.69 FPS.",
        "replace": "HOTA   Baseline 28.418  ->  AC-MOT 33.017\nIDS    Baseline 1238    ->  AC-MOT 994      (244 fewer)\nProcessing FPS   Baseline 44.181  ->  AC-MOT 37.686   (real-time)",
    },
    {
        "action": "replace_text",
        "slide": 59,
        "search": "FINAL SYSTEM: TRK_NEW24_MATCH88 | new_track_thresh 0.24 | match_thresh 0.88 | selected after real-time, MOTA and IDS gates",
        "replace": "FINAL SYSTEM: Full AC-MOT + tuned ByteTrack | new_track_thresh 0.24 | match_thresh 0.88 | live FP16 official comparison",
    },
]
