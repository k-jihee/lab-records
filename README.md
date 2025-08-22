# 제품 분석 일보 (Streamlit App, JSON 저장)

## 실행 방법

1. 가상환경 생성 후 필요한 패키지 설치:
   ```bash
   pip install -r requirements.txt
   ```

2. 앱 실행:
   ```bash
   streamlit run app.py
   ```

3. 브라우저에서 `http://localhost:8501` 접속

## 데이터 파일

- 제품/항목 정의: `제품명, 분석항목.csv`
- 저장 데이터: `daily_product_reports.json`

앱에서 입력한 데이터는 `daily_product_reports.json` 파일에 누적 저장됩니다.
