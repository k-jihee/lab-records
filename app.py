import streamlit as st
import pandas as pd
from datetime import date
import json, os, uuid

CSV_FILE = "제품명, 분석항목.csv"

df = pd.read_csv(CSV_FILE)
df.columns = [c.strip() for c in df.columns]

if not ("제품명" in df.columns and "분석항목" in df.columns):
    st.error("CSV에 '제품명', '분석항목' 컬럼이 없습니다.")
    st.stop()

st.title("📊 일자별 제품 분석 (HTML 테이블 스타일)")
analysis_date = st.date_input("분석 일자", value=date.today())

# 제품별 그룹핑
grouped = df.groupby("제품명")["분석항목"].apply(list).to_dict()

results = {}

for product, items in grouped.items():
    st.subheader(f"📦 {product}")
    table_html = "<table style='width:100%; border-collapse: collapse;'>"
    table_html += "<tr><th style='border:1px solid #ddd;padding:8px;'>항목명</th><th style='border:1px solid #ddd;padding:8px;'>결과</th></tr>"
    st.markdown(table_html, unsafe_allow_html=True)

    prod_results = {}
    for item in items:
        col1, col2 = st.columns([2,3])
        with col1:
            st.markdown(f"<div style='padding:8px;border:1px solid #ddd'>{item}</div>", unsafe_allow_html=True)
        with col2:
            val = st.text_input(f"{product}_{item}", key=f"{product}_{item}")
            prod_results[item] = val
    results[product] = prod_results
    st.markdown("<br>", unsafe_allow_html=True)

# 저장 로직
SAVE_FILE = "daily_product_reports.json"
if not os.path.exists(SAVE_FILE):
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=2)

def load_reports():
    with open(SAVE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_report(data):
    reports = load_reports()
    reports.append(data)
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(reports, f, ensure_ascii=False, indent=2)

if st.button("저장"):
    reports = []
    for product, items in results.items():
        reports.append({
            "productName": product,
            "analysisItems": [{"itemName": k, "result": v} for k, v in items.items()]
        })
    data = {
        "id": str(uuid.uuid4()),
        "analysisDate": str(analysis_date),
        "reports": reports
    }
    save_report(data)
    st.success("저장 완료 ✅")
    st.json(data)
