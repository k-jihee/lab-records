import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
from datetime import date
import json, os, uuid

# CSV 파일 경로
CSV_FILE = "제품명, 분석항목.csv"

if not os.path.exists(CSV_FILE):
    st.error(f"CSV 파일을 찾을 수 없습니다: {CSV_FILE}")
    st.stop()

df_csv = pd.read_csv(CSV_FILE)
product_dict = {}
for _, row in df_csv.iterrows():
    prod = row["제품명"]
    item = row["분석항목"]
    product_dict.setdefault(prod, []).append(item)

# 초기 DataFrame 생성 (제품명+항목명, 결과는 빈칸)
rows = []
for prod, items in product_dict.items():
    for it in items:
        rows.append({"제품명": prod, "항목명": it, "결과": ""})
df = pd.DataFrame(rows)

st.title("📊 일자별 제품 분석 (AgGrid 엑셀 스타일)")

analysis_date = st.date_input("분석 일자", value=date.today())

# AgGrid 옵션 설정
gb = GridOptionsBuilder.from_dataframe(df)
gb.configure_default_column(editable=True, groupable=True, filter=True, resizable=True, sortable=True)
gb.configure_column("제품명", editable=False)
gb.configure_column("항목명", editable=False)
gb.configure_column("결과", editable=True)
grid_options = gb.build()

grid_response = AgGrid(
    df,
    gridOptions=grid_options,
    update_mode=GridUpdateMode.VALUE_CHANGED,
    fit_columns_on_grid_load=True,
    enable_enterprise_modules=False,
    height=400,
    theme="balham"
)

edited_df = pd.DataFrame(grid_response["data"])

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
    for product in edited_df["제품명"].unique():
        items = edited_df[edited_df["제품명"] == product][["항목명", "결과"]]
        reports.append({
            "productName": product,
            "analysisItems": [
                {"itemName": row["항목명"], "result": row["결과"]}
                for _, row in items.iterrows()
            ]
        })
    data = {
        "id": str(uuid.uuid4()),
        "analysisDate": str(analysis_date),
        "reports": reports
    }
    save_report(data)
    st.success("저장 완료 ✅")
    st.json(data)

# 저장된 보고서 목록
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
