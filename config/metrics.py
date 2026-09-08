"""
Official final live FP16 / TrackEval comparison results.

These are the authoritative numbers for the AC-MOT final paper.
Every chart, table label, and Slide 59 metric block must reference this module.
DO NOT hard-code these values in individual slide scripts.
"""
from __future__ import annotations

# ── Official final results ────────────────────────────────────────────────────
# Source: live FP16 / TrackEval run; Tesla T4; YOLOv8n; VisDrone2019-MOT test-dev
# all 17 sequences; classes: person, car, bus, truck (occlusion<3, score≥1)

OFFICIAL_RESULTS: dict[str, dict[str, float | int]] = {
    "baseline": {
        "mota": 19.718,   # MOTA %
        "hota": 28.418,   # HOTA %
        "idf1": 32.716,   # IDF1 %
        "ids":  1238,     # Identity switches (lower is better)
        "fps":  44.181,   # Processing frames per second
    },
    "acmot": {
        "mota": 22.999,
        "hota": 33.017,
        "idf1": 40.021,
        "ids":  994,
        "fps":  37.686,
    },
}

# ── Derived deltas (computed once from OFFICIAL_RESULTS) ─────────────────────
_b = OFFICIAL_RESULTS["baseline"]
_a = OFFICIAL_RESULTS["acmot"]

DELTAS: dict[str, float | int] = {
    "mota":  round(_a["mota"] - _b["mota"], 3),   # +3.281
    "hota":  round(_a["hota"] - _b["hota"], 3),   # +4.599
    "idf1":  round(_a["idf1"] - _b["idf1"], 3),   # +7.305
    "ids":   _a["ids"] - _b["ids"],                # -244
    "fps":   round(_a["fps"] - _b["fps"], 3),      # -6.495
}

# ── Development ablation (A0–A3, legacy-v10 evaluator) ───────────────────────
# Used in ablation story slides 54–58; NOT the final paper headline numbers.
ABLATION: dict[str, dict] = {
    "A0": {
        "label": "Baseline_Default",
        "mota":  0.3585,
        "idf1":  None,
        "hota":  None,
        "ids":   2508,
        "fps":   30.8,
    },
    "A1": {
        "label": "Baseline_Tuned",
        "mota":  0.3850,
        "idf1":  None,
        "hota":  None,
        "ids":   2148,
        "fps":   30.1,
    },
    "A2": {
        "label": "AdaptThresh",
        "mota":  0.4095,
        "idf1":  None,
        "hota":  None,
        "ids":   2136,
        "fps":   29.8,
    },
    "A3": {
        "label": "AdaptResolution (adopted)",
        "mota":  0.4737,
        "idf1":  None,
        "hota":  None,
        "ids":   2695,
        "fps":   28.9,
    },
}

# ── Per-sequence best case (uav0000188, largest MOTA gain) ───────────────────
BEST_SEQUENCE = {
    "id":       "uav0000188_00000_v",
    "a0_mota":  0.2161,
    "a3_mota":  0.4449,
    "a0_idf1":  0.3505,
    "a3_idf1":  0.5359,
    "mota_gain": 0.2287,
    "idf1_gain": 0.1854,
}

# ── Tracker configuration (live values from repository) ──────────────────────
BYTETRACK_CONFIG = {
    "track_high_thresh": 0.18,
    "track_low_thresh":  0.04,
    "new_track_thresh":  0.24,   # live value from current repository
    "track_buffer":      45,
    "match_thresh":      0.88,   # live value from current repository
}

# ── Smart Calibrator parameter bounds ────────────────────────────────────────
CALIBRATOR_BOUNDS = {
    "conf_min": 0.19,
    "conf_max": 0.28,
    "conf_default": 0.245,
    "conf_slope": 0.050,
    "iou_min":  0.40,
    "iou_max":  0.52,
    "iou_default": 0.490,
    "iou_slope": 0.050,
    "imgsz_default": 640,
    "imgsz_medium":  736,
    "imgsz_large":   832,
}
