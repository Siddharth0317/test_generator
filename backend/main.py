import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from typing import List
import io
import logging

from backend.schemas import GenerateRequest, RunSeleniumRequest, TestcaseModel
from backend.nlp.pipeline import extract_structure
from backend.testgen.generator import generate_testcases
from backend.exporters.csv_export import tc_list_to_csv
from backend.exporters.pdf_export import tc_list_to_pdf_bytes
from backend.selenium_runner import run_testcase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Testcase Generator API")

# allow local dev frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/generate", response_model=dict)
async def generate(req: GenerateRequest):
    start = time.time()
    try:
        struct = extract_structure(req.text)
        tcs = generate_testcases(struct)
        elapsed_ms = int((time.time() - start) * 1000)
        return {"testcases": tcs, "meta": {"elapsed_ms": elapsed_ms}}
    except Exception as e:
        logger.exception("Error in generate")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/export/csv")
async def export_csv(req: GenerateRequest):
    struct = extract_structure(req.text)
    tcs = generate_testcases(struct)
    csv_str = tc_list_to_csv(tcs)
    buffer = io.StringIO(csv_str)
    return StreamingResponse(iter([buffer.getvalue()]),
                             media_type="text/csv",
                             headers={"Content-Disposition": "attachment; filename=testcases.csv"})

@app.post("/export/pdf")
async def export_pdf(req: GenerateRequest):
    struct = extract_structure(req.text)
    tcs = generate_testcases(struct)
    pdf_bytes = tc_list_to_pdf_bytes(tcs)
    return StreamingResponse(io.BytesIO(pdf_bytes),
                             media_type="application/pdf",
                             headers={"Content-Disposition": "attachment; filename=testcases.pdf"})

@app.post("/run-selenium")
async def api_run_selenium(req: RunSeleniumRequest):
    tc = req.testcase.dict()
    try:
        results = run_testcase(tc, headless=req.headless)
        return {"results": results}
    except Exception as e:
        logger.exception("Selenium run failed")
        raise HTTPException(status_code=500, detail=str(e))
