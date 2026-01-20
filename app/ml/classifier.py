"""Lightweight classifier used by the MCP server.

This module provides a simple, deterministic `classify` function that accepts
an event dictionary and returns a classification and confidence score.
It is intentionally small so it can be replaced later with a scikit-learn model.
"""

from typing import Dict, Any


def classify(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Classify an event dict and return a result dict.

    Uses rule-based classification as a placeholder for ML model:
    - vehicle_count < 5 -> "low" traffic
    - vehicle_count < 15 -> "medium" traffic
    - vehicle_count >= 15 -> "high" traffic

    Score is adjusted based on average speed heuristics:
    - Low speed (< 20) increases confidence
    - High speed (> 80) decreases confidence

    Args:
        event: Dictionary containing event data with keys:
            - vehicle_count: int
            - avg_speed: float
            - (other fields are ignored)

    Returns:
        Dictionary with keys:
            - classification: str ("low", "medium", or "high")
            - score: float (0.0 to 1.0)
            - model_version: str

    Raises:
        None: Function is designed to handle missing/invalid data gracefully
    """
    # Extract and sanitize inputs with defaults
    vehicle_count = int(event.get("vehicle_count", 0) or 0)
    avg_speed = float(event.get("avg_speed", 0.0) or 0.0)

    # Primary classification based on vehicle count
    if vehicle_count < 5:
        classification = "low"
        score = 0.2
    elif vehicle_count < 15:
        classification = "medium"
        score = 0.6
    else:
        classification = "high"
        score = 0.9

    # Score adjustment based on speed (simple heuristic)
    # Low speed suggests congestion, high speed suggests free flow
    if avg_speed < 20:
        score = min(1.0, score + 0.1)
    elif avg_speed > 80:
        score = max(0.0, score - 0.1)

    return {
        "classification": classification,
        "score": round(score, 3),
        "model_version": "rule_v1",
    }
