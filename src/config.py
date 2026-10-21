"""
ShikshaSignal Configuration & Assumptions Registry

DISCLAIMER & GOVERNANCE:
Thresholds, benchmark ratios, and scoring formulas defined here are
configurable SYNTHETIC DEMO ASSUMPTIONS designed for software prototyping.
They are NOT official policy cut-offs, NIPUN Bharat standards, or validated
pedagogical thresholds.
"""

from pathlib import Path

# Base Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SYNTHETIC_DIR = DATA_DIR / "synthetic"
TEMPLATES_DIR = DATA_DIR / "templates"
FIXTURES_DIR = DATA_DIR / "fixtures"
RAW_DIR = DATA_DIR / "raw"
DATABASE_PATH = DATA_DIR / "shikshasignal.db"

# Threshold Rule:
# Score ratio = score / max_score
# Review Trigger Condition: ratio < BENCHMARK_THRESHOLD_RATIO
# Note on boundary condition:
# For example, with BENCHMARK_THRESHOLD_RATIO = 0.60:
# A score of exactly 3/5 = 0.60 (60%).
# 0.60 < 0.60 evaluates to FALSE.
# Therefore, 3/5 DOES NOT trigger a review flag (it meets the benchmark).
# A score strictly below 3/5 (e.g., 2/5 = 40%, 1/5 = 20%, 0/5 = 0%) DOES trigger "Needs Teacher Review".
DEFAULT_BENCHMARK_THRESHOLD_RATIO = 0.60

# Assessment Version Baseline for Demo
CURRENT_ASSESSMENT_VERSION = "FLN-MVP-v1"

# Supported Grades
SUPPORTED_GRADES = {1, 2, 3}

# Supported Domains
SUPPORTED_DOMAINS = {"literacy", "numeracy"}
