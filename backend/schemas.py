from pydantic import BaseModel
from typing import List, Optional, Any, Dict

class GenerateRequest(BaseModel):
    text: str

class StepModel(BaseModel):
    step: int
    action: str
    target: Optional[str] = None
    value: Optional[str] = None
    expected: Optional[str] = None
    note: Optional[str] = None

class TestcaseModel(BaseModel):
    id: str
    title: str
    steps: List[StepModel]

class RunSeleniumRequest(BaseModel):
    testcase: TestcaseModel
    headless: Optional[bool] = True
