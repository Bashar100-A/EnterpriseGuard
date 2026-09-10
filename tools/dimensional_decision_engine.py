"""
Dimensional Decision Engine - Calibrated Version.
Reads central state and decides action with improved logic.
Classifies dimensions into critical and statistical, handles operational deviations.
Thresholds are provisional and will be calibrated after Phase 3 data collection.
"""
import sys
from pathlib import Path

sys.dont_write_bytecode = True

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dimensional_state import DimensionalState

# ------------------------------------------------------------
# PROVISIONAL THRESHOLDS - will be adjusted after calibration
# ------------------------------------------------------------
CRITICAL_HIGH_THRESHOLD = 0.8
STATISTICAL_HIGH_THRESHOLD = 0.9
TOTAL_DEVIATION_THRESHOLD = 3.5  # temporary

CRITICAL_DIMENSIONS = ["spatial", "identity", "negentropic"]
STATISTICAL_DIMENSIONS = ["temporal", "relational", "behavioral", "syntropic"]

LOW_DEV = 0.3
MID_DEV = 0.7  # > 0.7 considered high


def compute_deviation(score: float) -> float:
    """Convert score (0-1) to deviation (0-1)."""
    if score is None:
        return 1.0
    if score < 0:
        score = 0.0
    elif score > 1.0:
        score = 1.0
    return 1.0 - score


def is_operational(metadata: dict) -> bool:
    """Return True if metadata indicates operational deviation."""
    if not metadata:
        return False
    return metadata.get("operational", False)


def decision_rule(dimensions: dict) -> str:
    """Return 'CONTINUE', 'WARNING', or 'SHUTDOWN' based on calibrated logic."""
    if not dimensions:
        print("No dimensions collected.")
        return "SHUTDOWN"

    critical_deviations = []
    statistical_deviations = []
    total_deviation = 0.0

    for name, info in dimensions.items():
        score = info.get("score")
        metadata = info.get("details", {})
        deviation = compute_deviation(score)
        op_flag = is_operational(metadata)

        if name in CRITICAL_DIMENSIONS:
            critical_deviations.append((name, deviation, op_flag))
            total_deviation += deviation  # critical deviations always count fully
        else:
            statistical_deviations.append((name, deviation, op_flag))
            # operational deviations count half
            if op_flag:
                total_deviation += deviation * 0.5
            else:
                total_deviation += deviation

    # Count high deviations
    high_critical = [(n, d) for n, d, op in critical_deviations if d >= CRITICAL_HIGH_THRESHOLD and not op]
    mid_critical = [(n, d) for n, d, op in critical_deviations if MID_DEV <= d < CRITICAL_HIGH_THRESHOLD and not op]
    high_statistical = [(n, d) for n, d, op in statistical_deviations if d >= STATISTICAL_HIGH_THRESHOLD and not op]
    mid_statistical = [(n, d) for n, d, op in statistical_deviations if MID_DEV <= d < STATISTICAL_HIGH_THRESHOLD and not op]

    print(f"Total deviation (weighted): {total_deviation:.2f}")
    print(f"High critical deviations: {len(high_critical)}")
    print(f"Mid critical deviations: {len(mid_critical)}")
    print(f"High statistical deviations: {len(high_statistical)}")
    print(f"Mid statistical deviations: {len(mid_statistical)}")

    # Decision rules
    if high_critical:
        print("SHUTDOWN: high critical deviation detected.")
        return "SHUTDOWN"

    if mid_critical and high_statistical:
        print("SHUTDOWN: mid critical deviation combined with high statistical deviation.")
        return "SHUTDOWN"

    if len(high_statistical) >= 3:
        print("SHUTDOWN: three or more high statistical deviations.")
        return "SHUTDOWN"

    if total_deviation > TOTAL_DEVIATION_THRESHOLD:
        print("SHUTDOWN: total deviation exceeds threshold.")
        return "SHUTDOWN"

    if len(mid_statistical) >= 3:
        print("WARNING: multiple mid statistical deviations.")
        return "WARNING"

    return "CONTINUE"


def main():
    state = DimensionalState()
    tick = state.current_tick_data
    if not tick or "dimensions" not in tick:
        print("ERROR: Invalid or empty state data.")
        return

    dims = tick["dimensions"]
    print("Current dimensions state:")
    for name, info in dims.items():
        print(f"  {name}: score={info['score']}, operational={info.get('details', {}).get('operational', False)}, reason={info.get('details', {}).get('reason', '')}")

    verdict = decision_rule(dims)
    print(f"\nDecision: {verdict}")


if __name__ == "__main__":
    main()
