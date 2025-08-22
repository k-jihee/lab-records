import streamlit as st
import pandas as pd
from datetime import date
import json, os, uuid

CSV_FILE = "제품명, 분석항목.csv"

# CSV 읽기
try:
    df_csv = pd.read_csv(CSV_FILE)
except Exception as e:
    st.error(f"CSV 파일 불러오기 오류: {e}")
    st.stop()

# 컬럼 이름 정리
df_csv.columns = [c.strip() for c in df_csv.columns]

# 필수 컬럼 확인
if not ("제품명" in df_csv.columns and "분석항목" in df_csv.columns):
    st.error("CSV에 '제품명' 또는 '분석항목' 컬럼이 없습니다. 실제 컬럼명을 확인하세요.")
    st.write("현재 CSV 컬럼:", list(df_csv.columns))
    st.stop()

# 결과 컬럼 추가
df = df_csv.copy()
df["결과"] = ""

st.title("📊 일자별 제품 분석 (st.data_editor 버전)")
analysis_date = st.date_input("분석 일자", value=date.today())

# Excel 스타일 데이터 에디터
edited_df = st.data_editor(
    df,
    num_rows="dynamic",
    use_container_width=True,
    hide_index=True
)

# 저장 파일
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

# 저장 버튼
if st.button("저장"):
    reports = []
    for product in edited_df["제품명"].unique():
        items = edited_df[edited_df["제품명"] == product][["분석항목", "결과"]]
        reports.append({
            "productName": product,
            "analysisItems": [
                {"itemName": row["분석항목"], "result": row["결과"]}
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

# 저장된 보고서 보기
st.header("📂 저장된 보고서")
for rep in load_reports():
    with st.expander(f"📅 {rep['analysisDate']} (총 {len(rep['reports'])}개 제품)"):
        for product_report in rep["reports"]:
            st.write(f"### {product_report['productName']}")
            for item in product_report["analysisItems"]:
                st.write(f"- {item['itemName']}: {item['result']}")
