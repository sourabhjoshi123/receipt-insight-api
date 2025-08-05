from openai import OpenAI
import os
from dotenv import load_dotenv
import pytesseract
from PIL import Image
from fastapi import UploadFile
from PIL import Image
import io
from app.db import SessionLocal, Purchase
import pandas as pd
import time
import pandas as pd

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def extract_text_from_image(image_path: str) -> str:
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)
        return text
    except Exception as e:
        raise RuntimeError(f"❌ OCR failed: {e}")

def parse_text_with_gpt(text: str):
    prompt = f"""
Extract structured data from the following receipt text. Return it as JSON with:

- date (e.g. "7/11/2025")
- purchases: a list of objects with item, qty, price
- total_amount: the overall total paid, if available.

Example output:
{{
  "date": "7/11/2025",
  "purchases": [
    {{
      "item": "endosorb tablets",
      "qty": "10.00",
      "price": "30.00"
    }},
    ...
  ],
  "total_amount": "105.00"
}}

Only return the JSON — no extra commentary.

Receipt text:
{text}
"""


    response = client.chat.completions.create(
        model="gpt-4",  # or "gpt-3.5-turbo"
        messages=[
            {"role": "system", "content": "You extract structured purchase data from receipts."},
            {"role": "user", "content": prompt}
        ]
    )

    result_text = response.choices[0].message.content.strip()
    result_text = result_text.strip("```json").strip("```")

    import json
    return json.loads(result_text)

async def save_uploaded_image(file: UploadFile, upload_folder: str) -> str:
    """Reads uploaded image, normalizes to JPEG, and saves it. Returns the saved path."""
    os.makedirs(upload_folder, exist_ok=True)

    contents = await file.read()
    try:
        # Try to open as image
        img = Image.open(io.BytesIO(contents))
        img = img.convert("RGB")  # Normalize

        # Save with .jpg extension regardless of original
        filename_root = os.path.splitext(file.filename)[0]
        safe_filename = f"{filename_root}.jpg"
        image_path = os.path.join(upload_folder, safe_filename)
        img.save(image_path, "JPEG")

        return image_path  # ✅ Return the normalized saved path

    except Exception as e:
        raise RuntimeError(f"❌ Image processing failed: {e}")

def generate_summary_alerts():
    session = SessionLocal()
    try:
        purchases = session.query(Purchase).all()

        df = pd.DataFrame([{
            "date": p.purchase_date,
            "item": p.item,
            "price": p.price,
        } for p in purchases])

        if df.empty:
            return []

        # Aggregate by date
        daily_spend = df.groupby("date")["price"].sum().to_string()

        prompt = f"""
        You're an assistant that summarizes spending trends. Here's a user's daily spend:

        {daily_spend}

        List 1–3 clear alerts or observations (e.g., spikes, unusual purchases, recurring patterns).
        """

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )

        return response.choices[0].message.content.strip()

    finally:
        session.close()


def run_trend_analysis_with_jot():
    print("📊 Starting trend analysis...")

    session = SessionLocal()
    try:
        purchases = session.query(Purchase).all()

        if not purchases:
            print("⚠️ No purchases found in DB.")
            return "No purchase data available."

        # Prepare DataFrame
        df = pd.DataFrame([{
            "date": p.purchase_date,
            "item": p.item,
            "price": p.price,
        } for p in purchases])

        # Format for markdown table
        daily_df = df.groupby("date")["price"].sum().reset_index()
        summary_table = daily_df.to_markdown(index=False)

        print("📅 Daily spending markdown table:")
        print(summary_table)

        prompt = f"""
            You are an AI insights agent analyzing daily spending trends.

            Here is a table:

            {summary_table}

            Please write 2–3 plain-English insights. Highlight any unusual spikes, dips, or steady growth. Use a friendly tone and make it easy to read.
            """

        print("🧠 Sending prompt to Jot agent...")
        thread = client.beta.threads.create()
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=prompt
        )

        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=os.getenv("JOT_AGENT_ID"),
            tool_choice="auto"
        )

        print(f"🌀 Run started (ID: {run.id})... Waiting for completion.")

        # Poll run status
        while True:
            run_status = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            print(f"⏳ Current status: {run_status.status}")
            if run_status.status == "completed":
                break
            elif run_status.status in ["failed", "cancelled"]:
                return f"❌ Jot agent failed: {run_status.status}"
            time.sleep(1)

        print("✅ Run completed. Fetching messages...")
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        for msg in reversed(messages.data):
            if msg.role == "assistant":
                response = msg.content[0].text.value
                print("📬 Response from Jot agent:")
                print(response)
                return response

        print("⚠️ No assistant message found.")
        return "No insights returned from Jot agent."

    except Exception as e:
        print(f"❌ Exception during trend analysis: {e}")
        return f"Error: {e}"

    finally:
        session.close()





