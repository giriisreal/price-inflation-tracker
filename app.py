import os
import re
import pandas as pd
import requests
import pytesseract
import streamlit as st
from PIL import Image

# Windows only: remove the # and check the path
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

CSV = "receipts.csv"
st.title("My Personal Inflation Tracker")

# ---------- 1. Upload receipts ----------
receipt_date = st.date_input("Receipt date")
files = st.file_uploader("Upload receipt photos",
                         type=["png", "jpg", "jpeg"],
                         accept_multiple_files=True)

if files and st.button("Process receipts"):
    rows = []
    for f in files:
        img = Image.open(f).convert("L")
        text = pytesseract.image_to_string(img)
        for line in text.splitlines():
            m = re.match(r"(.+?)\s+(\d+\.\d{2})$", line.strip())
            if m:
                rows.append({"date": receipt_date,
                             "item": m.group(1).strip().lower(),
                             "price": float(m.group(2))})
    new = pd.DataFrame(rows)
    st.dataframe(new)
    if not new.empty:
        new.to_csv(CSV, mode="a", header=not os.path.exists(CSV), index=False)
        st.success(f"Saved {len(new)} items")
    else:
        st.warning("No items found. Try a clearer photo.")

# ---------- 2. Your inflation ----------
st.header("Results")
if os.path.exists(CSV):
    df = pd.read_csv(CSV, parse_dates=["date"])
    df["month"] = df["date"].dt.to_period("M")
    monthly = df.groupby(["item", "month"])["price"].mean().unstack()

    if monthly.shape[1] < 2:
        st.info("Add receipts from at least 2 different months to see inflation.")
    else:
        base, latest = monthly.columns[0], monthly.columns[-1]
        both = monthly[[base, latest]].dropna()
        both["change_pct"] = (both[latest] / both[base] - 1) * 100

        weights = spend / spend.sum()
        my_inflation = (both["change_pct"] * weights).sum()