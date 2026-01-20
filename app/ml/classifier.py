from typing import Dict, Any

def classify(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Lightweight rule-based classifier used as a placeholder MCP model.
    Returns a dict with classification label, score and optional metadata.
    """
    vehicle_count = int(event.get("vehicle_count", 0) or 0)
    avg_speed = float(event.get("avg_speed", 0.0) or 0.0)

    if vehicle_count < 5:
        classification = "low"
        score = 0.2
    elif vehicle_count < 15:
        classification = "medium"
        score = 0.6
    else:
        classification = "high"
        score = 0.9

    # slight score adjustment based on speed (simple heuristic)
    if avg_speed < 20:
        score = min(1.0, score + 0.1)
    elif avg_speed > 80:
        score = max(0.0, score - 0.1)

    return {
        "classification": classification,
        "score": round(score, 3),
        "model_version": "rule_v1",
    }

"""
Lightweight classifier used by the MCP server.

This module provides a simple, deterministic `classify` function that accepts
an event dictionary and returns a classification and confidence score.
It is intentionally small so it can be replaced later with a scikit-learn model.
"""
from typing import Dict, Any
from datetime import datetime


def classify(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Classify an event dict and return a result dict.

    Rules (placeholder):
    - vehicle_count < 5 -> "low"
    - otherwise -> "high"

    Returns:
        {"classification": str, "score": float, "processed_at": datetime.isoformat()}
    """
    vc = event.get("vehicle_count", 0)
    classification = "low" if vc < 5 else "high"
    # Simple confidence heuristic: more vehicles -> higher confidence in "high"
    score = min(1.0, max(0.0, (vc / 20)))
    return {
        "classification": classification,
        "score": float(score),
        "processed_at": datetime.utcnow().isoformat(),
    }

