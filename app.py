import streamlit as st
import pandas as pd
import json

SAVE_FILE = "daily_product_reports.json"

def load_reports():
    with open(SAVE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

st.header("📈 데이터 분석 / 추이 변화")

# 데이터 로드
reports = load_reports()

# JSON → DataFrame 변환
rows = []
for rep in reports:
    date = rep["analysisDate"]
    for prod in rep["reports"]:
        pname = prod["productName"]
        for item in prod["analysisItems"]:
            try:
                val = float(item["result"])
            except:
                val = None
            rows.append({
                "analysisDate": date,
                "productName": pname,
                "itemName": item["itemName"],
                "result": val
            })
df = pd.DataFrame(rows)

if df.empty:
    st.info("저장된 데이터가 없습니다.")
else:
    st.subheader("📌 원시 데이터 테이블")
    st.dataframe(df)

    # -----------------------------
    # 1) 한 제품의 항목별 추이
    # -----------------------------
    st.subheader("📊 단일 제품 · 항목 추이")
    prod_sel = st.selectbox("제품 선택", df["productName"].unique(), key="prod_sel")
    item_sel = st.selectbox(
        "항목 선택",
        df[df["productName"]==prod_sel]["itemName"].unique(),
        key="item_sel"
    )

    filtered = df[(df["productName"]==prod_sel) & (df["itemName"]==item_sel)]
    filtered = filtered.sort_values("analysisDate")

    st.line_chart(filtered.set_index("analysisDate")["result"])

    # -----------------------------
    # 2) 여러 제품 간 비교
    # -----------------------------
    st.subheader("📊 여러 제품 간 비교 (동일 항목)")
    item_sel2 = st.selectbox("비교할 항목 선택", df["itemName"].unique(), key="item_sel2")

    compare_df = df[df["itemName"]==item_sel2].pivot(
        index="analysisDate", columns="productName", values="result"
    ).sort_index()

    st.write("🔹 제품별 추이 (Line chart)")
    st.line_chart(compare_df)

    st.write("🔹 제품별 값 비교 (Bar chart)")
    st.bar_chart(compare_df)
