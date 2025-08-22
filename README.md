# 제품 분석 일보 (AgGrid 엑셀 스타일 Streamlit App)

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

## 기능
- CSV(`제품명, 분석항목.csv`)에 정의된 제품/항목을 불러옵니다.
- 엑셀 스타일 표에서 결과를 직접 입력할 수 있습니다.
- 정렬, 필터, 복사/붙여넣기 등 고급 기능 지원.
- 입력한 데이터는 `daily_product_reports.json`에 저장됩니다.
