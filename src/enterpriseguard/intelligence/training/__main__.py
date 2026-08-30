"""
EnterpriseGuard Training Package
================================


Command-line entry point for the training subsystem.


Usage
-----
python -m enterpriseguard.intelligence.training
"""


from __future__ import annotations


from enterpriseguard.intelligence.training.training_service import (
    TrainingService,
)




def main() -> int:
    """Run the TrainingService self-test."""
    TrainingService._self_test()
    return 0




if __name__ == "__main__":
    raise SystemExit(main())