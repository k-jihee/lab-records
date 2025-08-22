# 제품 분석 일보 – Streamlit 앱

React 버전 기능을 Streamlit으로 이식한 앱입니다. Firestore 또는 로컬 JSON으로 보고서를 저장합니다.

## 빠른 실행 (로컬)

```bash
pip install -r requirements.txt
streamlit run app.py
```

- Firestore를 쓰지 않으면 현재 작업 폴더에 `product_analysis_reports.json` 파일로 저장됩니다.
- Firestore를 쓰려면 `.streamlit/secrets.toml` 파일을 만들고 아래 템플릿을 채우세요.
  - 템플릿은 `.streamlit/secrets.toml.example` 참고

## 배포 1) Streamlit Community Cloud (권장, 무료)

1. 이 폴더 구조를 통째로 GitHub 저장소에 올립니다.
2. https://share.streamlit.io 에서 **New app** → 해당 저장소와 브랜치, **app.py** 선택
3. (선택) **Advanced settings** → **Secrets**에 서비스 계정 JSON을 다음과 같이 입력
   ```toml
   [gcp_service_account]
   type = "service_account"
   project_id = "YOUR_PROJECT_ID"
   private_key_id = "…"
   private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
   client_email = "firebase-adminsdk@YOUR_PROJECT_ID.iam.gserviceaccount.com"
   client_id = "…"
   auth_uri = "https://accounts.google.com/o/oauth2/auth"
   token_uri = "https://oauth2.googleapis.com/token"
   auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
   client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk%40YOUR_PROJECT_ID.iam.gserviceaccount.com"
   ```
4. 앱이 뜨면 사이드바에서 **APP ID / User ID** 입력 → 저장소 선택 → 사용 시작

## 배포 2) Hugging Face Spaces (무료)

1. https://huggingface.co/spaces 에서 **New Space** → SDK: *Streamlit*
2. 방금 만든 GitHub repo를 연결하거나 파일을 직접 업로드
3. **Settings → Variables and secrets**에 위의 Streamlit Secrets 내용을 동일하게 추가
4. 기본 엔트리포인트는 `app.py`이므로 그대로 동작합니다.

## Firestore 경로 규칙

```
artifacts/{APP_ID}/users/{USER_ID}/product_analysis_reports_v3
```

- 사이드바에서 APP ID / User ID를 설정하면 해당 경로에 저장/조회합니다.

## 기능 요약

- 제품 템플릿 선택 → 항목 결과 입력 → 저장
- 목록 조회 / 펼침 상세 / 수정 / 삭제
- 템플릿-저장값 **항목명 기준 병합**(누락 방지)
- Firestore 미사용 시 로컬 JSON 저장

---

문의: 앱에 CSV/PDF 내보내기, 검색/필터, 파일첨부 기능 추가가 필요하면 알려주세요.
