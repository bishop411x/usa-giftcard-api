# main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
import random
import re
import string
from datetime import datetime
import pytz
from typing import List, Optional

US_TZ = pytz.timezone('America/New_York')
def now_us(): return datetime.now(US_TZ).strftime('%Y-%m-%d %I:%M:%S %p %Z')

app = FastAPI(title="USA Gift Card API", docs_url="/docs")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

GIFTCARDS = {
    "Amazon Gift Card": {"pattern": r"^[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$", "len": 14, "pin": None},
    "Google Play Gift Card": {"pattern": r"^[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$", "len": 19, "pin": None},
    "Steam Gift Card": {"pattern": r"^[A-Z0-9]{5}-[A-Z0-9]{5}-[A-Z0-9]{5}$", "len": 17, "pin": None},
    "Best Buy Gift Card": {"pattern": r"^[0-9]{4} [0-9]{4} [0-9]{4} [0-9]{4}$", "len": 19, "pin": 4},
}

def random_alnum(n): return ''.join(random.choices(string.ascii_uppercase + string.digits, k=n))

class GenReq(BaseModel):
    card_name: str = Field(..., example="Amazon Gift Card")
    count: int = Field(1, ge=1, le=50)

class ValReq(BaseModel):
    card_name: str
    voucher: str
    pin: Optional[str] = None

@app.get("/")
def home(): return {"message": "Live in USA", "time": now_us(), "docs": "/docs"}

@app.get("/cards")
def cards(): return list(GIFTCARDS.keys())

@app.post("/generate")
def generate(req: GenReq):
    if req.card_name not in GIFTCARDS: raise HTTPException(404, "Not supported")
    cfg = GIFTCARDS[req.card_name]
    res = []
    for _ in range(req.count):
        if "Amazon" in req.card_name:
            v = "-".join(random_alnum(4) for _ in range(3))
        elif "Google" in req.card_name:
            v = "-".join(random_alnum(4) for _ in range(4))
        elif "Steam" in req.card_name:
            v = "-".join(random_alnum(5) for _ in range(3))
        else:
            v = " ".join(f"{random.randint(0,9999):04d}" for _ in range(4))
        pin = "".join(random.choices(string.digits, k=cfg["pin"])) if cfg["pin"] else None
        res.append({"voucher": v, "pin": pin})
    return res

@app.post("/validate")
def validate(req: ValReq):
    if req.card_name not in GIFTCARDS: raise HTTPException(404, "Not supported")
    cfg = GIFTCARDS[req.card_name]
    v_ok = bool(re.match(cfg["pattern"], req.voucher))
    p_ok = cfg["pin"] is None or (req.pin and len(req.pin) == cfg["pin"] and req.pin.isdigit())
    return {"valid": v_ok and p_ok, "accuracy": 100.0 if v_ok and p_ok else 0.0}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
