from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from typing import List, Dict
import io

def tc_list_to_pdf_bytes(testcases: List[Dict]) -> bytes:
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 50
    for tc in testcases:
        c.setFont("Helvetica-Bold", 14)
        c.drawString(40, y, f"Testcase: {tc.get('id')} — {tc.get('title')}")
        y -= 20
        c.setFont("Helvetica", 11)
        for step in tc.get("steps", []):
            line = f"Step {step.get('step')}: {step.get('action')} | target: {step.get('target')} | value: {step.get('value') or ''} | expect: {step.get('expected') or ''}"
            c.drawString(50, y, line[:120])
            y -= 15
            if y < 80:
                c.showPage()
                y = height - 50
        y -= 10
        if y < 120:
            c.showPage()
            y = height - 50
    c.save()
    buffer.seek(0)
    return buffer.read()
