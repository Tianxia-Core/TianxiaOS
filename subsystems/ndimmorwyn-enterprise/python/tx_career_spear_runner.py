#!/usr/bin/env python3
# ffp: FFP-CAREER-SPEAR-RUNNER concurrent-daemon python
# File: tx_career_spear.py
# Compliance: DSS-14.2 (PARAMASIVA) + SLECO-SO++ + ENHAN3
"""
tx_career_spear.py -- Top-level executable runner for tx_career_spear.
"""
import sys
from pathlib import Path

# Add workspace to sys.path
WORKSPACE = Path(__file__).resolve().parent.parent.parent
if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))

from tx_career_spear.cli import main

if __name__ == "__main__":
    sys.exit(main())
