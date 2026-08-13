# Golden-set status

The 50 scoring fixtures are draft calibration material. Every case has `reviewed: false` until Arman Khachatryan checks the Armenian text and all five dimension scores. Automated validation must not present the draft set as an expert-reviewed benchmark.

After review, run three independent `hy-score` passes per case and store the outputs outside user-authored source text. Version 1.0 requires total-score deviation within ±0.7 and per-dimension deviation within ±1.0 from the reviewed median.
