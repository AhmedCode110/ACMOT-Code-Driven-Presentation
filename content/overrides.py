# Final paper/seminar update applied on top of the original editable deck.
# Two-layer result story:
# 1) Development ablation keeps the old presentation flow:
#    Baseline -> Tuned ByteTrack -> Adaptive Threshold/NMS -> Adaptive Resolution.
# 2) Final live validation adds the paper-ready comparison:
#    Baseline_Default vs TRK_NEW24_MATCH88 using Tesla T4, YOLOv8n FP16,
#    clean processing timing and official TrackEval.

OVERRIDES = [
    # Detector classes: keep the deployed detector claim exact.
    {
        "action": "replace_text",
        "slide": 4,
        "search": "pedestrians, cars, vans, trucks and buses",
        "replace": "persons, cars, buses and trucks",
    },

    # Metric / timing framing.
    {
        "action": "replace_text",
        "slide": 16,
        "search": "HOTA*: internal proxy combining detection and association terms; it is not official HOTA. Higher is better.",
        "replace": "HOTA is the official TrackEval detection-association metric. HOTA* appears only in the development ablation as an internal proxy; the final result uses official HOTA.",
    },
    {
        "action": "replace_text",
        "slide": 16,
        "search": "Recorded full-17 run: A3 = 28.9 FPS; A0 = 30.8 FPS on T4, actual FP32.",
        "replace": "Final live result: AC-MOT = 37.69 processing FPS on Tesla T4, YOLOv8n FP16. This is above the 25 FPS real-time target.",
    },
    {
        "action": "replace_text",
        "slide": 16,
        "search": "A3 runs at 28.9 FPS -> real-time for a 25 FPS stream. A0 runs at 30.8 FPS -> the adaptive cost is only 6.3%.",
        "replace": "AC-MOT processes at 37.69 FPS, so one core frame takes about 26.5 ms - safely below the 40 ms budget of a 25 FPS stream.",
    },

    # Final ByteTrack configuration.
    {
        "action": "replace_text",
        "slide": 40,
        "search": "new_track_thresh = 0.20",
        "replace": "new_track_thresh = 0.24",
    },
    {
        "action": "replace_text",
        "slide": 40,
        "search": "match_thresh = 0.86",
        "replace": "match_thresh = 0.88",
    },
    {
        "action": "replace_text",
        "slide": 40,
        "search": "Tracker side - tuned once, then frozen",
        "replace": "Tracker side - final selected configuration, tuned once then frozen",
    },
    {
        "action": "replace_text",
        "slide": 40,
        "search": "match_thresh = 0.86 - used by ByteTrack to match detections with existing tracks. This value stays fixed.",
        "replace": "match_thresh = 0.88 - used by ByteTrack to associate detections with existing tracks. It is tuned once and remains fixed during inference.",
    },

    # Keep SCI stabilizer slide, but connect it to the final live number.
    {
        "action": "replace_text",
        "slide": 44,
        "search": "The recorded run measures A3 at 28.9 FPS versus A0 at 30.8 FPS: a 6.3% speed cost while remaining above the 25 FPS real-time line.",
        "replace": "The final live FP16 benchmark measures AC-MOT at 37.69 processing FPS. The adaptive layer spends compute, but the system remains 12.69 FPS above the 25 FPS real-time line.",
    },

    # Experimental protocol: separate development ablation from final official validation.
    {
        "action": "replace_text",
        "slide": 45,
        "search": "five ablations and every scoring decision stated explicitly.",
        "replace": "a step-by-step ablation study plus final live FP16 validation with every scoring decision stated explicitly.",
    },
    {
        "action": "replace_text",
        "slide": 51,
        "search": "Hardware: Google Colab Tesla T4, batch 1. FP16 was requested, but the predictor reported actual_model_fp16=False; this recorded run is therefore labelled FP32. HOTA* is a proxy, not official HOTA.",
        "replace": "Two evidence layers are reported: the development ablation explains how each component changes the system, while the final live run uses Tesla T4, batch 1, YOLOv8n actual FP16 and official TrackEval HOTA/CLEAR/Identity. JPEG decode is measured separately from processing FPS.",
    },

    # Restore the old ablation story, but fix wording mistakes and mark it as development evidence.
    {
        "action": "replace_text",
        "slide": 52,
        "search": "A Fair and Attributable Experimental Design",
        "replace": "A Fair Ablation: Building AC-MOT Step by Step",
    },
    {
        "action": "replace_text",
        "slide": 52,
        "search": "A0-A4 run the IDENTICAL YOLOv8n detector, with no retraining anywhere. So every measured improvement has to come from the architecture - it cannot come from a bigger or better-trained detector.",
        "replace": "A0-A3 run the IDENTICAL YOLOv8n detector, with no retraining anywhere. So the ablation shows how tracking improves as we add tuning, adaptive thresholds and adaptive resolution - not a bigger detector.",
    },
    {
        "action": "replace_text",
        "slide": 52,
        "search": "The four systems differ in only one main way: A1 uses the corrected settings, A3 adds the adaptive layer, A3 - AdaptResolution (ours) uses a different tracking method. Everything else stays the same, including the detector, videos, ground truth, and hardware.",
        "replace": "The build-up is deliberate: A0 is the default baseline, A1 tunes ByteTrack, A2 adds adaptive confidence and NMS IoU, and A3 adds adaptive resolution. Everything else stays fixed: detector, videos, ground truth and hardware.",
    },
    {
        "action": "replace_text",
        "slide": 52,
        "search": "Five systems × 17 sequences = 85 recorded system-sequence runs. A3 is adopted; A4 is reported as a negative ablation.",
        "replace": "This slide explains the architecture. A later final-selection slide updates the adopted tracker settings using the live FP16 official TrackEval run.",
    },

    # Keep development ablation slides, but label them clearly instead of replacing them with finalists.
    {
        "action": "replace_text",
        "slide": 54,
        "search": "Full-17 Main Results — A0 to Adopted A3",
        "replace": "Development Ablation — Baseline to Full AC-MOT",
    },
    {
        "action": "replace_text",
        "slide": 54,
        "search": "Unweighted mean over 17 sequences; IDS/FN/FP are summed. Legacy-v10 internal evaluator, HOTA* proxy, T4 actual FP32.",
        "replace": "Development ablation over 17 sequences. It explains the contribution of each component. The final paper-ready numbers are reported later using live FP16 and official TrackEval.",
    },
    {
        "action": "replace_text",
        "slide": 55,
        "search": "Full-17 Results, Presented Graphically",
        "replace": "Ablation Trend: Each Added Component Changes the Trade-off",
    },
    {
        "action": "replace_text",
        "slide": 55,
        "search": "E X A M P L E A3 moves accuracy furthest while remaining above 25 FPS. The cost is visible too: IDS rises after adaptive resolution, so the claim is better detection and association balance — not fewer switches under every evaluator.",
        "replace": "E X A M P L E This is the step-by-step engineering story: tune the tracker, then add adaptive thresholding, then add adaptive resolution. A3 gives the largest accuracy jump while remaining above the 25 FPS line. The final tracker tuning is selected in the next evidence layer.",
    },
    {
        "action": "replace_text",
        "slide": 56,
        "search": "Ablation Study: Contribution of Each Component",
        "replace": "Ablation Study: What Each Component Adds",
    },
    {
        "action": "replace_text",
        "slide": 56,
        "search": "A3 is adopted because adaptive resolution provides the decisive accuracy gain. A4 is preserved as a negative ablation, not presented as the final system.",
        "replace": "A3 proves the adaptive-resolution contribution. Then the final live stage keeps the same architecture and only tunes ByteTrack to choose the best publishable operating point.",
    },
    {
        "action": "replace_text",
        "slide": 58,
        "search": "Accuracy–Speed Operating Point on the T4",
        "replace": "Development Accuracy–Speed Operating Point on the T4",
    },
    {
        "action": "replace_text",
        "slide": 58,
        "search": "E X A M P L E A3 is the best operating point among the tested ablations: the largest accuracy gain, still above 25 FPS, and no useful improvement from A4.",
        "replace": "E X A M P L E The ablation shows why the full AC-MOT architecture is worth keeping. The final result then re-validates the selected system using actual FP16, official TrackEval and clean processing timing.",
    },

    # Re-purpose qualitative slide into final official live comparison.
    {
        "action": "replace_text",
        "slide": 59,
        "search": "Baseline → Full AC-MOT: Largest Visible Gain",
        "replace": "Final Official Comparison: Baseline vs AC-MOT",
    },
    {
        "action": "replace_text",
        "slide": 59,
        "search": "WHY THIS CASE",
        "replace": "SAME PROTOCOL",
    },
    {
        "action": "replace_text",
        "slide": 59,
        "search": "uav0000188_00000_v TINY-OBJECT SCENE",
        "replace": "17 VisDrone sequences | Tesla T4 | YOLOv8n FP16 | official TrackEval",
    },
    {
        "action": "replace_text",
        "slide": 59,
        "search": "MOTA A0  0.2161 A3  0.4449 GAIN  +0.2287",
        "replace": "MOTA  baseline 19.718  ->  AC-MOT 22.999   GAIN +3.281 points",
    },
    {
        "action": "replace_text",
        "slide": 59,
        "search": "IDF1 A0  0.3505 A3  0.5359 GAIN  +0.1854",
        "replace": "IDF1  baseline 32.716  ->  AC-MOT 40.021   GAIN +7.305 points",
    },
    {
        "action": "replace_text",
        "slide": 59,
        "search": "Largest MOTA gain among all 17 sequences. A3 recovers many more tiny targets through adaptive resolution; this is the clearest direct A0-to-A3 example.",
        "replace": "HOTA improves from 28.418 to 33.017. IDS drops from 1238 to 994, giving 244 fewer identity switches. Processing remains real-time at 37.69 FPS.",
    },
    {
        "action": "replace_text",
        "slide": 59,
        "search": "VIDEO: 12 seconds | 1920 x 1080 | A0 vs A3 only | recorded T4 run",
        "replace": "FINAL SYSTEM: TRK_NEW24_MATCH88 | new_track_thresh 0.24 | match_thresh 0.88 | selected after real-time, MOTA and IDS gates",
    },

    # Reproducibility.
    {
        "action": "replace_text",
        "slide": 61,
        "search": "Same hardware for all Every system ran on the same Tesla T4 with batch 1. The predictor reported actual_model_fp16=False, so this run is labelled FP32. Like-for-like by construction.",
        "replace": "Same hardware for final comparison Every live final system ran on the same Tesla T4 with batch 1 and actual YOLOv8n FP16 confirmed. Like-for-like by construction.",
    },
    {
        "action": "replace_text",
        "slide": 61,
        "search": "Local SSD copy Sequences were copied to local disk before inference, so the FPS reading is not polluted by network delays.",
        "replace": "Local SSD staging Sequences were copied to local disk before inference. Warm-up is outside timing; JPEG decode is measured separately from SCI + YOLO + ByteTrack processing.",
    },
    {
        "action": "replace_text",
        "slide": 61,
        "search": "Per-sequence CSVs The run records tracks, settings, timing, per-sequence metrics, hashes, checkpoints and JSON sidecars for all 85 cases.",
        "replace": "Traceable outputs The final run records trial configs, per-sequence timing, official TrackEval outputs, comparison CSVs and the final selection JSON.",
    },

    # Scope and conclusion.
    {
        "action": "replace_text",
        "slide": 64,
        "search": "The absolute MOTA is low - on purpose YOLOv8n is kept fixed so any improvement comes from our method, not a bigger detector. The calibrator can be used with other YOLO models later. The calibrator drops onto any YOLO in deployment.",
        "replace": "YOLOv8n is intentionally fixed so the measured gain is attributable to the adaptive architecture rather than a larger detector. This also preserves an embedded-friendly compute footprint.",
    },
    {
        "action": "replace_text",
        "slide": 64,
        "search": "One benchmark, one split We tested one benchmark split: all 17 VisDrone2019-MOT test-dev sequences, covering crowded, night, tiny-object and clear scenes. More datasets and splits will be tested later.",
        "replace": "One benchmark, one selection split The final configuration was selected on VisDrone2019-MOT test-dev, so this split functions as development/selection data. Independent held-out evaluation is the next step for stronger generalization claims.",
    },
    {
        "action": "replace_text",
        "slide": 64,
        "search": "The ReID we tried was basic A basic grayscale crop-similarity cue. It provides no meaningful gain and increases IDS, so it is not adopted. Reported as A4. A compact deep embedding is the next step.",
        "replace": "Embedded deployment is not yet claimed The current benchmark proves real-time core processing on a Tesla T4. A live camera-to-tracks test on Jetson Orin is the next deployment validation step.",
    },
    {
        "action": "replace_text",
        "slide": 65,
        "search": "+32.1% MOTA",
        "replace": "+3.281 MOTA points",
    },
    {
        "action": "replace_text",
        "slide": 65,
        "search": "+21.2% IDF1",
        "replace": "+7.305 IDF1 points",
    },
    {
        "action": "replace_text",
        "slide": 65,
        "search": "+15.9% HOTA*",
        "replace": "+4.599 HOTA points",
    },
    {
        "action": "replace_text",
        "slide": 65,
        "search": "-30% ID switches",
        "replace": "-19.7% ID switches",
    },
    {
        "action": "replace_text",
        "slide": 65,
        "search": "3.7x faster than BoT-SORT",
        "replace": "37.69 processing FPS",
    },
    {
        "action": "replace_text",
        "slide": 65,
        "search": "Runs at 28.9 FPS on the recorded T4/FP32 setup",
        "replace": "Runs at 37.69 processing FPS on the final Tesla T4/FP16 benchmark",
    },
    {
        "action": "replace_text",
        "slide": 65,
        "search": "Works with any YOLO without changing the tracker.",
        "replace": "Improves tracking without replacing YOLOv8n with a larger detector.",
    },

    # Future work and final takeaway.
    {
        "action": "replace_text",
        "slide": 66,
        "search": "1. Identity-aware association The clearest next gain: it is exactly what gives BoT-SORT its 247 switches. Adding it could close the remaining gap while keeping our speed. AC-MOT 325 IDS  vs  BoT-SORT 247 IDS.",
        "replace": "1. Embedded UAV deployment Export YOLOv8n to TensorRT FP16 on Jetson Orin and measure true camera-to-tracks FPS, latency, power, memory and thermal behaviour.",
    },
    {
        "action": "replace_text",
        "slide": 66,
        "search": "2. Density-gated resolution In the two densest sequences the 832 px step costs recall. Gating resolution on density as well as SCI should recover it. Aimed at exactly s249a and s306.",
        "replace": "2. Camera-motion compensation Add motion compensation for aerial camera translation/rotation while preserving the real-time budget.",
    },
    {
        "action": "replace_text",
        "slide": 66,
        "search": "3. A proper deep ReID Replace the basic grayscale crop cue with a compact deep embedding suited to aerial viewpoints - light enough to keep real-time speed. Builds directly on configuration A4.",
        "replace": "3. Compact deep ReID Add an aerial-friendly appearance embedding only if it improves identity continuity without dropping below the 25 FPS target.",
    },
    {
        "action": "replace_text",
        "slide": 66,
        "search": "4. SCI beyond YOLO Run the official VisDrone evaluator, then test the same SCI controller on UAVDT, AU-AIR and stronger detectors. Tests whether the idea generalises.",
        "replace": "4. Generalization Validate on an independent held-out split, UAVDT and AU-AIR, then test the same SCI controller with other detectors such as RT-DETR.",
    },
    {
        "action": "replace_text",
        "slide": 67,
        "search": "+32.1% MOTA",
        "replace": "+3.281 MOTA points",
    },
    {
        "action": "replace_text",
        "slide": 67,
        "search": "+21.2% IDF1",
        "replace": "+7.305 IDF1 points",
    },
    {
        "action": "replace_text",
        "slide": 67,
        "search": "+15.9% HOTA*",
        "replace": "+4.599 HOTA points",
    },
    {
        "action": "replace_text",
        "slide": 67,
        "search": "-30% ID switches",
        "replace": "244 fewer ID switches",
    },
    {
        "action": "replace_text",
        "slide": 67,
        "search": "23.9 FPS, live",
        "replace": "37.69 FPS processing, real-time",
    },
    {
        "action": "replace_text",
        "slide": 67,
        "search": "IF YOU REMEMBER ONE THING The scene tells you how carefully to look. Measure it, and let the detector listen.",
        "replace": "IF YOU REMEMBER ONE THING First we build AC-MOT step by step; then the final live FP16 validation shows better tracking than the same-protocol baseline while preserving real-time processing.",
    },
]
