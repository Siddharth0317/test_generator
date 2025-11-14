from typing import List, Dict
import pandas as pd
import io

def tc_list_to_csv(testcases: List[Dict]) -> str:
    rows = []
    for tc in testcases:
        tc_id = tc.get("id", "")
        title = tc.get("title", "")
        for step in tc.get("steps", []):
            rows.append({
                "tc_id": tc_id,
                "title": title,
                "step": step.get("step"),
                "action": step.get("action"),
                "target": step.get("target") or "",
                "value": step.get("value") or "",
                "expected": step.get("expected") or "",
                "note": step.get("note") or ""
            })
    df = pd.DataFrame(rows)
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    return buffer.getvalue()
