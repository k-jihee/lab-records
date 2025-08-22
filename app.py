import streamlit as st
import pandas as pd
from datetime import date
import json
import uuid
import os

# CSV 불러오기 (제품명, 분석항목)
CSV_FILE = "제품명, 분석항목.csv"

if not os.path.exists(CSV_FILE):
    st.error(f"CSV 파일을 찾을 수 없습니다: {CSV_FILE}")
    st.stop()

df = pd.read_csv(CSV_FILE)
product_dict = {}
for _, row in df.iterrows():
    prod = row["제품명"]
    item = row["분석항목"]
    product_dict.setdefault(prod, []).append(item)

# 저장용 JSON 파일 경로
SAVE_FILE = "daily_product_reports.json"

# JSON 파일 초기화
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

# ---------------- UI ----------------
st.title("📊 일자별 제품 분석 입력 (로컬 JSON 저장)")

# 분석 일자 선택
analysis_date = st.date_input("분석 일자", value=date.today())

# 입력값 저장 딕셔너리
results = {}

st.subheader("제품별 분석 결과 입력")

for product, items in product_dict.items():
    with st.expander(f"📦 {product}", expanded=True):
        prod_results = {}
        for item in items:
            val = st.text_input(f"{product} - {item}", key=f"{product}_{item}")
            prod_results[item] = val
        results[product] = prod_results

# 저장 버튼
if st.button("저장"):
    data = {
        "id": str(uuid.uuid4()),
        "analysisDate": str(analysis_date),
        "reports": []
    }
    for product, items in results.items():
        data["reports"].append({
            "productName": product,
            "analysisItems": [{"itemName": k, "result": v} for k, v in items.items()]
        })
    save_report(data)
    st.success("저장 완료 ✅")
    st.json(data)

# ---------------- 목록 ----------------
st.header("📂 저장된 보고서")
all_reports = load_reports()

if not all_reports:
    st.info("저장된 보고서가 없습니다.")
else:
    for rep in all_reports:
        with st.expander(f"📅 {rep['analysisDate']} (총 {len(rep['reports'])}개 제품)", expanded=False):
            for product_report in rep["reports"]:
                st.write(f"### {product_report['productName']}")
                for item in product_report["analysisItems"]:
                    st.write(f"- {item['itemName']}: {item['result']}")
