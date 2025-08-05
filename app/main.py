from fastapi import FastAPI, UploadFile, File, Form, Body
from services.ocr_gpt import parse_text_with_gpt, extract_text_from_image, save_uploaded_image, run_trend_analysis_with_jot
from app.db import drop_all_purchases, insert_purchases
from sqlalchemy.orm import Session
from app.models import Purchase
from app.db import SessionLocal
from sqlalchemy import func
from sqlalchemy.orm import Session
import os
from fastapi.staticfiles import StaticFiles
import pandas as pd

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Receipt Insight API is live"}

# Absolute path to app/data/receipts
receipt_dir = os.path.join(os.path.dirname(__file__), "data", "receipts")

app.mount("/receipts", StaticFiles(directory=receipt_dir), name="receipts")

@app.post("/upload-preview")
async def upload_preview(
    file: UploadFile = File(...), 
    receipt_name: str = Form(None)
):
    upload_folder = "app/data/receipts"
    image_path = await save_uploaded_image(file, upload_folder)

    # Default title fallback
    filename_root = os.path.splitext(os.path.basename(image_path))[0]
    receipt_title = receipt_name or filename_root

    text = extract_text_from_image(image_path)
    parsed_data = parse_text_with_gpt(text)

    return {
        "status": "success",
        "receipt_title": receipt_title,
        "date": parsed_data["date"],
        "purchases": parsed_data["purchases"],
        "image_filename": os.path.basename(image_path)
    }


@app.post("/save")
def save_to_db(data: dict = Body(...)):
    if "image_filename" not in data:
        return {"status": "error", "message": "Missing image_filename in request"}

    insert_purchases(data, data["receipt_title"], data["image_filename"])
    return {"status": "success", "message": "Saved selected purchases to DB"}


@app.get("/purchases/")
def get_purchases():
    session: Session = SessionLocal()
    purchases = session.query(Purchase).order_by(Purchase.purchase_date.desc()).all()
    session.close()

    # Serialize each purchase
    return {
        "status": "success",
        "data": [
            {
                "id": p.id,
                "receipt_title": p.receipt_title,
                "purchase_date": p.purchase_date,
                "item": p.item,
                "quantity": p.quantity,
                "price": p.price,
                "image_filename": p.image_filename
            }
            for p in purchases
        ]
    }

from fastapi import HTTPException

@app.delete("/receipt/{receipt_title}")
def delete_receipt(receipt_title: str):
    session = SessionLocal()
    try:
        # Delete all purchases under this receipt
        purchases = session.query(Purchase).filter(Purchase.receipt_title == receipt_title).all()
        if not purchases:
            raise HTTPException(status_code=404, detail="Receipt not found")

        # Delete associated image file if exists
        image_path = os.path.join("app/data/receipts", purchases[0].image_filename)
        if os.path.exists(image_path):
            os.remove(image_path)

        # Delete from DB
        for p in purchases:
            session.delete(p)

        session.commit()
        return {"status": "success", "message": f"Deleted receipt: {receipt_title}"}
    finally:
        session.close()


@app.post("/admin/reset/")
def reset_purchases():
    drop_all_purchases()
    return {"status": "success", "message": "All purchases deleted"}


@app.get("/summary/")
def get_summary():
    session: Session = SessionLocal()

    # Summary by receipt
    by_receipt = session.query(
        Purchase.receipt_title,
        func.sum(Purchase.price * Purchase.quantity).label("total")
    ).group_by(Purchase.receipt_title).all()

    # Summary by date
    by_date = session.query(
        Purchase.purchase_date,
        func.sum(Purchase.price * Purchase.quantity).label("total")
    ).group_by(Purchase.purchase_date).order_by(Purchase.purchase_date.desc()).all()

    # Summary by item
    by_item = session.query(
        Purchase.item,
        func.sum(Purchase.price * Purchase.quantity).label("total")
    ).group_by(Purchase.item).order_by(func.sum(Purchase.price * Purchase.quantity).desc()).all()

    session.close()

    return {
        "status": "success",
        "summary": {
            "by_receipt": [{"receipt_title": r[0], "total": round(r[1], 2)} for r in by_receipt],
            "by_date": [{"date": d[0], "total": round(d[1], 2)} for d in by_date],
            "by_item": [{"item": i[0], "total": round(i[1], 2)} for i in by_item]
        }
    }

import time

@app.get("/summary-alerts")
def summary_alerts():
    print("📡 /summary-alerts called")
    start = time.time()
    try:
        alerts = run_trend_analysis_with_jot()
        print(f"✅ Jot completed in {time.time() - start:.2f}s")
        return {"status": "success", "alerts": alerts}
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"status": "error", "message": str(e)}

