# Final paper/seminar update applied on top of the original editable deck.
# This version keeps the original visual language while replacing legacy-v10
# result claims with the validated live FP16 + official TrackEval results.

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
        "search": "HOTA*: internal proxy combining detection and association terms; it is not official HOTA.",
        "replace": "HOTA: official TrackEval metric balancing detection and association quality.",
    },
    {
        "action": "replace_text",
        "slide": 16,
        "search": "Recorded full-17 run: A3 = 28.9 FPS; A0 = 30.8 FPS on T4, actual FP32.",
        "replace": "Final live run: AC-MOT = 37.69 processing FPS; baseline = 44.18 processing FPS on a Tesla T4, actual FP16.",
    },
    {
        "action": "replace_text",
        "slide": 16,
        "search": "A3 runs at 28.9 FPS -> real-time for a 25 FPS stream. A0 runs at 30.8 FPS -> the adaptive cost is only 6.3%.",
        "replace": "AC-MOT runs at 37.69 processing FPS, so one core frame takes about 26.5 ms - safely below the 40 ms budget of a 25 FPS stream.",
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
        "search": "match_thresh = 0.86 - used by ByteTrack to match detections with existing tracks. This value stays fixed.",
        "replace": "match_thresh = 0.88 - used by ByteTrack to associate detections with existing tracks. It is tuned once and remains fixed during inference.",
    },
    {
        "action": "replace_text",
        "slide": 40,
        "search": "Tracker side - tuned once, then frozen",
        "replace": "Tracker side - final selected configuration, tuned once then frozen",
    },

    # Updated runtime result on the stabilizer slide.
    {
        "action": "replace_text",
        "slide": 44,
        "search": "The recorded run measures A3 at 28.9 FPS versus A0 at 30.8 FPS: a 6.3% speed cost while remaining above the 25 FPS real-time line.",
        "replace": "The final live FP16 benchmark measures AC-MOT at 37.69 processing FPS versus 44.18 FPS for the baseline. The adaptive system is slower, but still retains 12.69 FPS of headroom above the 25 FPS real-time threshold.",
    },

    # Experimental setup wording.
    {
        "action": "replace_text",
        "slide": 45,
        "search": "five ablations",
        "replace": "one live baseline and three final tracker candidates",
    },
    {
        "action": "replace_text",
        "slide": 49,
        "search": "Why exactly these five",
        "replace": "Why these selected targets",
    },
    {
        "action": "replace_text",
        "slide": 51,
        "search": "main: Hungarian IoU assignment with no minimum overlap gate",
        "replace": "main: official TrackEval HOTA, CLEAR and Identity evaluation at IoU threshold 0.50",
    },
    {
        "action": "replace_text",
        "slide": 51,
        "search": "report main metrics; replay diagnostic separately uses IoU ≥ 0.50",
        "replace": "report official HOTA, MOTA, IDF1 and IDSW from TrackEval",
    },
    {
        "action": "replace_text",
        "slide": 51,
        "search": "Hardware: Google Colab Tesla T4, batch 1. FP16 was requested, but the predictor reported actual_model_fp16=False; this recorded run is therefore labelled FP32. HOTA* is a proxy, not official HOTA.",
        "replace": "Hardware: Google Colab Tesla T4, batch 1, YOLOv8n actual FP16. Dataset staging and warm-up are outside timing. JPEG decode is measured separately. Drive writes, report generation and TrackEval are excluded from processing FPS. Accuracy uses official TrackEval HOTA/CLEAR/Identity.",
    },

    # Replace legacy A0-A4 design with final live comparison protocol.
    {
        "action": "replace_text",
        "slide": 52,
        "search": "A0 - Baseline_Default Used with the default settings: confidence = 0.25 and image size = 640. It is the baseline used for comparison.",
        "replace": "Baseline_Default - the same YOLOv8n FP16 detector and live timing protocol, used as the controlled reference point.",
    },
    {
        "action": "replace_text",
        "slide": 52,
        "search": "A1 - Baseline_Tuned Same detector, only the ByteTrack config corrected for UAV footage. No adaptive logic at all.",
        "replace": "TRK_MATCH_090 - finalist 1: high 0.18, low 0.04, new 0.20, buffer 45, match 0.90.",
    },
    {
        "action": "replace_text",
        "slide": 52,
        "search": "A2 - AdaptThresh Tuned tracker + scene-adaptive confidence and NMS IoU. Resolution remains fixed at 640.",
        "replace": "TRK_BUFFER60_NEW22_MATCH88 - finalist 2: new 0.22, buffer 60, match 0.88.",
    },
    {
        "action": "replace_text",
        "slide": 52,
        "search": "A3 - AdaptResolution (ours) A2 plus adaptive input resolution. This is the adopted AC-MOT system.",
        "replace": "TRK_NEW24_MATCH88 - FINAL AC-MOT: new 0.24, buffer 45, match 0.88. Selected after passing the real-time, MOTA and IDS gates.",
    },
    {
        "action": "replace_text",
        "slide": 52,
        "search": "A0-A4 run the IDENTICAL YOLOv8n detector, with no retraining anywhere. So every measured improvement has to come from the architecture - it cannot come from a bigger or better-trained detector.",
        "replace": "All compared systems run the IDENTICAL YOLOv8n detector, the same 17 sequences, the same GT filter, the same Tesla T4 and the same official TrackEval protocol. No retraining is used.",
    },
    {
        "action": "replace_text",
        "slide": 52,
        "search": "Five systems × 17 sequences = 85 recorded system-sequence runs. A3 is adopted; A4 is reported as a negative ablation.",
        "replace": "Final selection rule: processing FPS >= 25, MOTA above the live baseline, IDS below the live baseline; tie-break by higher MOTA, then lower IDS, then higher processing FPS.",
    },

    # Headline results: exact final live comparison.
    {
        "action": "replace_text",
        "slide": 54,
        "search": "Full-17 Main Results — A0 to Adopted A3",
        "replace": "Final Live Results — Baseline to Selected AC-MOT",
    },
    {
        "action": "replace_text",
        "slide": 54,
        "search": "+32.1% MOTA",
        "replace": "+3.281 MOTA points",
    },
    {
        "action": "replace_text",
        "slide": 54,
        "search": "+21.2% IDF1",
        "replace": "+7.305 IDF1 points",
    },
    {
        "action": "replace_text",
        "slide": 54,
        "search": "+15.9% HOTA*",
        "replace": "+4.599 HOTA points",
    },
    {
        "action": "replace_text",
        "slide": 54,
        "search": "-17.0% false negatives",
        "replace": "244 fewer ID switches",
    },
    {
        "action": "replace_text",
        "slide": 54,
        "search": "17 / 17 MOTA wins",
        "replace": "37.69 FPS processing",
    },
    {
        "action": "replace_text",
        "slide": 54,
        "search": "E X A M P L E A3 delivers the strongest MOTA and HOTA*. A4 adds only +0.0007 IDF1, while MOTA and HOTA* fall and IDS rises by 42, so A3 remains the adopted system.",
        "replace": "E X A M P L E The final AC-MOT system raises MOTA from 19.718 to 22.999, HOTA from 28.418 to 33.017 and IDF1 from 32.716 to 40.021, while reducing IDS from 1238 to 994. It still processes 37.69 frames/s.",
    },
    {
        "action": "replace_text",
        "slide": 54,
        "search": "Unweighted mean over 17 sequences; IDS/FN/FP are summed. Legacy-v10 internal evaluator, HOTA* proxy, T4 actual FP32.",
        "replace": "All values come from the same final live FP16 run over 17 VisDrone test-dev sequences using official TrackEval. Processing FPS excludes JPEG decode, which is reported separately.",
    },

    # Graphical comparison slide: baseline versus winner first, finalists as context.
    {
        "action": "replace_text",
        "slide": 55,
        "search": "Full-17 Results, Presented Graphically",
        "replace": "Same-Protocol Comparison: Baseline vs Final AC-MOT",
    },
    {"action": "replace_text", "slide": 55, "search": "A0", "replace": "Baseline"},
    {"action": "replace_text", "slide": 55, "search": ".3585", "replace": "19.718"},
    {"action": "replace_text", "slide": 55, "search": "A1", "replace": "MATCH90"},
    {"action": "replace_text", "slide": 55, "search": ".3850", "replace": "22.953"},
    {"action": "replace_text", "slide": 55, "search": "A2", "replace": "BUF60"},
    {"action": "replace_text", "slide": 55, "search": ".4095", "replace": "22.998"},
    {"action": "replace_text", "slide": 55, "search": "A3 adopted", "replace": "AC-MOT FINAL"},
    {"action": "replace_text", "slide": 55, "search": ".4737", "replace": "22.999"},
    {"action": "replace_text", "slide": 55, "search": "2508", "replace": "1238"},
    {"action": "replace_text", "slide": 55, "search": "2148", "replace": "946"},
    {"action": "replace_text", "slide": 55, "search": "2136", "replace": "1023"},
    {"action": "replace_text", "slide": 55, "search": "2695", "replace": "994"},
    {"action": "replace_text", "slide": 55, "search": "30.8 FPS", "replace": "44.18 FPS"},
    {"action": "replace_text", "slide": 55, "search": "29.8 FPS", "replace": "37.17 FPS"},
    {"action": "replace_text", "slide": 55, "search": "28.9 FPS — highest accuracy", "replace": "37.69 FPS — selected"},
    {
        "action": "replace_text",
        "slide": 55,
        "search": "E X A M P L E A3 moves accuracy furthest while remaining above 25 FPS. The cost is visible too: IDS rises after adaptive resolution, so the claim is better detection and association balance — not fewer switches under every evaluator.",
        "replace": "E X A M P L E Against the controlled live baseline, final AC-MOT improves every headline tracking metric: +4.599 HOTA, +3.281 MOTA, +7.305 IDF1 and 244 fewer IDS, while remaining 12.69 FPS above the real-time threshold.",
    },

    # Attribution / finalist selection.
    {
        "action": "replace_text",
        "slide": 56,
        "search": "Ablation Study: Contribution of Each Component",
        "replace": "Finalist Selection: Why TRK_NEW24_MATCH88 Wins",
    },
    {
        "action": "replace_text",
        "slide": 56,
        "search": "A0 to A1 +0.0265 MOTA and 360 fewer IDS. Tracker tuning is a clean first gain.",
        "replace": "Baseline -> MATCH90: MOTA 19.718 -> 22.953, IDS 1238 -> 946, processing 38.03 FPS. A strong identity-preserving finalist.",
    },
    {
        "action": "replace_text",
        "slide": 56,
        "search": "A1 to A2 +0.0245 MOTA and 12 fewer IDS. Adaptive thresholding improves recall without an identity penalty.",
        "replace": "Baseline -> BUFFER60: MOTA 22.998, IDS 1023, processing 37.17 FPS. Slightly higher MOTA, but weaker identity result than MATCH90.",
    },
    {
        "action": "replace_text",
        "slide": 56,
        "search": "A2 to A3 +0.0642 MOTA — the largest step. It also adds 559 IDS and costs ~1 FPS; A3 is adopted with this trade-off disclosed.",
        "replace": "FINAL NEW24/MATCH88: MOTA 22.999, IDS 994, processing 37.69 FPS. It passes all gates and has the highest MOTA of the eligible candidates.",
    },
    {
        "action": "replace_text",
        "slide": 56,
        "search": "A3 to A4 MOTA -0.0002, IDF1 +0.0007, HOTA* -0.0002 and +42 IDS. No meaningful benefit: rejected.",
        "replace": "Selection is not 'best at every metric'. MATCH90 has lower IDS and higher IDF1; NEW24/MATCH88 is selected by the predefined priority: real-time gate, then MOTA, then IDS, then FPS.",
    },
    {
        "action": "replace_text",
        "slide": 56,
        "search": "A3 is adopted because adaptive resolution provides the decisive accuracy gain. A4 is preserved as a negative ablation, not presented as the final system.",
        "replace": "Scientific takeaway: the winner is chosen by a declared decision rule, not after looking for whichever metric makes AC-MOT look best.",
    },

    # Re-purpose per-sequence slide into the strongest controlled gain summary.
    {
        "action": "replace_text",
        "slide": 57,
        "search": "Per-Sequence Behaviour",
        "replace": "What the Controlled Baseline Comparison Proves",
    },
    {
        "action": "replace_text",
        "slide": 57,
        "search": "Largest gain — s0188 MOTA +0.2287; IDF1 0.3505 → 0.5359. This tiny-object case shows the value of adaptive resolution.",
        "replace": "Tracking quality improves: HOTA 28.418 -> 33.017, MOTA 19.718 -> 22.999, IDF1 32.716 -> 40.021.",
    },
    {
        "action": "replace_text",
        "slide": 57,
        "search": "Consistency and trade-off A3 improves MOTA and IDF1 on 17/17 sequences. IDS improves on 6/17 and worsens on 11/17 under the legacy evaluator.",
        "replace": "Identity continuity improves too: IDS drops from 1238 to 994 - 244 fewer switches, a 19.7% reduction.",
    },
    {
        "action": "replace_text",
        "slide": 57,
        "search": "Scene coverage 12 crowded · 2 night · 2 tiny · 1 clear",
        "replace": "Speed remains real-time: 37.69 processing FPS, equivalent to 26.5 ms/frame against a 40 ms budget for 25 FPS video.",
    },
    {
        "action": "replace_text",
        "slide": 57,
        "search": "E X A M P L E Full rows come from the recorded run. Matching videos are in presentation_videos; each video has a JSON sidecar and the folder has video_index.json.",
        "replace": "E X A M P L E The baseline is actually faster at 44.18 FPS. AC-MOT intentionally spends some of that speed headroom to obtain better tracking, but still remains comfortably above the real-time target.",
    },

    # Real-time / speed slide.
    {
        "action": "replace_text",
        "slide": 58,
        "search": "Accuracy–Speed Operating Point on the T4",
        "replace": "Accuracy–Speed Operating Point: Final Live FP16 Run",
    },
    {"action": "replace_text", "slide": 58, "search": "A0  30.8 FPS", "replace": "Baseline  44.18 FPS"},
    {"action": "replace_text", "slide": 58, "search": "A1  30.1 FPS", "replace": "MATCH90   38.03 FPS"},
    {"action": "replace_text", "slide": 58, "search": "A2  29.8 FPS", "replace": "BUFFER60  37.17 FPS"},
    {"action": "replace_text", "slide": 58, "search": "A3  28.9 FPS", "replace": "AC-MOT FINAL  37.69 FPS"},
    {"action": "replace_text", "slide": 58, "search": "+32.1% MOTA vs A0", "replace": "+16.64% relative MOTA vs baseline"},
    {"action": "replace_text", "slide": 58, "search": "28.9 FPS — live", "replace": "37.69 FPS — real-time processing"},
    {
        "action": "replace_text",
        "slide": 58,
        "search": "All five systems remain real-time The recorded run ranges from 28.9 to 30.8 FPS on the T4. A3's accuracy gain costs only 6.3% speed versus A0.",
        "replace": "All final candidates remain real-time by the 25 FPS processing criterion. Final AC-MOT runs at 37.69 FPS - 12.69 FPS above the threshold - while improving all headline tracking metrics over the live baseline.",
    },
    {
        "action": "replace_text",
        "slide": 58,
        "search": "Identity result depends on the evaluation gate Legacy main: A3 IDS 2695 vs A0 2508. IoU ≥ 0.50 replay: A3 IDS 1092 vs A0 1237. Report both; do not overclaim.",
        "replace": "Timing is reported transparently: core processing = 37.69 FPS; JPEG-decode-inclusive throughput = 19.17 FPS. The paper therefore claims real-time processing throughput, not full JPEG-file end-to-end real time.",
    },
    {
        "action": "replace_text",
        "slide": 58,
        "search": "E X A M P L E A3 is the best operating point among the tested ablations: the largest accuracy gain, still above 25 FPS, and no useful improvement from A4.",
        "replace": "E X A M P L E A 25 FPS stream gives 40 ms per frame. Final AC-MOT needs about 26.5 ms for SCI + YOLOv8n + ByteTrack, leaving about 13.5 ms of processing headroom.",
    },

    # Video evidence slide: avoid legacy metric claims while preserving the visual example.
    {
        "action": "replace_text",
        "slide": 59,
        "search": "Baseline → Full AC-MOT: Largest Visible Gain",
        "replace": "Baseline → Final AC-MOT: Qualitative Evidence",
    },
    {
        "action": "replace_text",
        "slide": 59,
        "search": "Largest MOTA gain among all 17 sequences. A3 recovers many more tiny targets through adaptive resolution; this is the clearest direct A0-to-A3 example.",
        "replace": "This clip remains a qualitative example of why adaptive resolution helps tiny targets. Quantitative claims in this version come from the final official TrackEval live benchmark shown on the preceding slides.",
    },

    # Reproducibility.
    {
        "action": "replace_text",
        "slide": 61,
        "search": "Same hardware for all Every system ran on the same Tesla T4 with batch 1. The predictor reported actual_model_fp16=False, so this run is labelled FP32. Like-for-like by construction.",
        "replace": "Same hardware and precision Every final system ran on the same Tesla T4 with batch 1 and actual YOLOv8n FP16 confirmed. Like-for-like by construction.",
    },
    {
        "action": "replace_text",
        "slide": 61,
        "search": "Local SSD copy Sequences were copied to local disk before inference, so the FPS reading is not polluted by network delays.",
        "replace": "Local SSD staging Sequences were copied from Drive to local disk before benchmarking. Warm-up is outside timing; JPEG decode is timed separately from SCI + YOLO + ByteTrack processing.",
    },
    {
        "action": "replace_text",
        "slide": 61,
        "search": "Per-sequence CSVs The run records tracks, settings, timing, per-sequence metrics, hashes, checkpoints and JSON sidecars for all 85 cases.",
        "replace": "Traceable outputs The final run records trial configs, per-sequence timing, official TrackEval outputs, comparison CSVs and the final selection JSON.",
    },

    # Scope / scientific caveat.
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

    # Conclusion.
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

    # Future work: connect directly to embedded deployment.
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

    # Final slide.
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
        "replace": "IF YOU REMEMBER ONE THING AC-MOT spends available compute where the scene is difficult: better tracking than the same-protocol baseline, while preserving real-time processing.",
    },
]
