from typing import Dict, Any, List
import uuid
import logging

logger = logging.getLogger(__name__)

def generate_testcases(struct: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Convert structured dict into list of testcases (currently one testcase per input).
    Ensures step indices are consistent and returns Pydantic-friendly dicts.
    """
    tc_id = f"tc_{uuid.uuid4().hex[:8]}"
    title = struct.get("title", "Auto-generated Testcase")
    steps = struct.get("steps", []) or []
    # Normalize steps: keep only expected keys
    normalized = []
    for idx, s in enumerate(steps, start=1):
        normalized.append({
            "step": idx,
            "action": s.get("action", "unknown"),
            "target": s.get("target"),
            "value": s.get("value"),
            "expected": s.get("expected"),
            "note": s.get("note")
        })
    logger.debug("Generated testcase %s with %d steps", tc_id, len(normalized))
    return [{"id": tc_id, "title": title, "steps": normalized}]
