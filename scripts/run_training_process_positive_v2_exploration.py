"""Run post-v1-failure PSD-candidate exploration."""
from __future__ import annotations
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from odsp.training_process_positive_v2_exploratory_panel import run_psd_candidate_exploration

result = run_psd_candidate_exploration()
print("TRAINING_PROCESS_V2_EXPLORATION=" + json.dumps(result, sort_keys=True))
