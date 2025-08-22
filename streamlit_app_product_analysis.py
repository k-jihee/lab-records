
import streamlit as st
from datetime import date, datetime as dt
from typing import List, Dict, Optional
import uuid
import json

# --- Optional Firestore imports (handled lazily) ---
try:
    from google.oauth2 import service_account
    from google.cloud import firestore
    _FIRESTORE_AVAILABLE = True
except Exception:
    _FIRESTORE_AVAILABLE = False

st.set_page_config(page_title="제품 분석 일보", page_icon="🧪", layout="wide")

# -----------------------------
# Product Templates (Catalog)
# -----------------------------
PRODUCT_CATALOG = {
    "productA": {
        "name": "알파-아밀라아제 A-100",
        "code": "APA-100",
        "analysisItems": [
            {"itemName": "성상", "specification": "고유의 색과 향을 가진 분말", "result": ""},
            {"itemName": "수분(%)", "specification": "10 이하", "result": ""},
            {"itemName": "PH (3%)", "specification": "4 ~ 7", "result": ""},
            {"itemName": "역가(u/g)", "specification": "100,000 이상", "result": ""},
        ],
    },
    "productB": {
        "name": "베타-글루카나아제 B-200",
        "code": "BGL-200",
        "analysisItems": [
            {"itemName": "성상", "specification": "백색의 미세한 분말", "result": ""},
            {"itemName": "수분(%)", "specification": "8 이하", "result": ""},
            {"itemName": "회분(%)", "specification": "0.5 이하", "result": ""},
            {"itemName": "역가(u/g)", "specification": "200,000 이상", "result": ""},
            {"itemName": "중금속(ppm)", "specification": "10 이하", "result": ""},
        ],
    },
    "productC": {
        "name": "셀룰라아제 C-300",
        "code": "CEL-300",
        "analysisItems": [
            {"itemName": "성상", "specification": "고유의 색과 향을 가진 분말", "result": ""},
            {"itemName": "수분(%)", "specification": "10 이하", "result": ""},
            {"itemName": "PH (3%)", "specification": "4 ~ 7", "result": ""},
            {"itemName": "조단백(%)", "specification": "0.35 이하", "result": ""},
            {"itemName": "회분(%)", "specification": "0.2 이하", "result": ""},
            {"itemName": "일반세균(cfu/g)", "specification": "85 이상", "result": ""},
            {"itemName": "광학적", "specification": "26 이상", "result": ""},
            {"itemName": "입도 #40 ON", "specification": "3 이하", "result": ""},
            {"itemName": "입도 #60 ON", "specification": "10 ~ 40", "result": ""},
            {"itemName": "입도 #120# ON", "specification": "10 ~ 40", "result": ""},
            {"itemName": "입도 #120# Pass", "specification": "80 이상", "result": ""},
        ],
    },
    "productCS": {
        "name": "옥수수전분",
        "code": "GIC0032S",
        "analysisItems": [
            {"itemName": "성상", "specification": "-", "result": ""},
            {"itemName": "수분(%)", "specification": "-", "result": ""},
            {"itemName": "회분(%)", "specification": "-", "result": ""},
            {"itemName": "pH(%)", "specification": "-", "result": ""},
            {"itemName": "백도", "specification": "-", "result": ""},
            {"itemName": "입도 #60 ON", "specification": "-", "result": ""},
        ],
    },
}

# -----------------------------
# Persistence Layer
# -----------------------------
class StorageBase:
    def list_reports(self) -> List[Dict]: ...
    def add_report(self, data: Dict) -> str: ...
    def update_report(self, doc_id: str, data: Dict) -> None: ...
    def delete_report(self, doc_id: str) -> None: ...

class LocalJSONStorage(StorageBase):
    def __init__(self, path: str = "product_analysis_reports.json"):
        self.path = path
        if not st.session_state.get("_local_loaded"):
            if not os.path.exists(self.path):
                with open(self.path, "w", encoding="utf-8") as f:
                    json.dump([], f, ensure_ascii=False, indent=2)
            st.session_state["_local_loaded"] = True

    def _read(self) -> List[Dict]:
        with open(self.path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write(self, rows: List[Dict]):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)

    def list_reports(self) -> List[Dict]:
        rows = self._read()
        # newest first by analysisDate
        def _key(x):
            try:
                return dt.fromisoformat(x.get("analysisDate", "1970-01-01"))
            except Exception:
                return dt(1970,1,1)
        return sorted(rows, key=_key, reverse=True)

    def add_report(self, data: Dict) -> str:
        rows = self._read()
        _id = str(uuid.uuid4())
        now = dt.utcnow().isoformat()
        data = {**data, "id": _id, "createdAt": now, "updatedAt": now}
        rows.append(data)
        self._write(rows)
        return _id

    def update_report(self, doc_id: str, data: Dict) -> None:
        rows = self._read()
        updated = False
        for i, r in enumerate(rows):
            if r.get("id") == doc_id:
                rows[i] = {**r, **data, "id": doc_id, "updatedAt": dt.utcnow().isoformat()}
                updated = True
                break
        if not updated:
            raise ValueError("Report not found")
        self._write(rows)

    def delete_report(self, doc_id: str) -> None:
        rows = self._read()
        rows = [r for r in rows if r.get("id") != doc_id]
        self._write(rows)

class FirestoreStorage(StorageBase):
    def __init__(self, app_id: str, user_id: str):
        if not _FIRESTORE_AVAILABLE:
            raise RuntimeError("google-cloud-firestore가 설치되어 있지 않습니다.")
        # Secrets: st.secrets["gcp_service_account"] must be present
        if "gcp_service_account" not in st.secrets:
            raise RuntimeError("st.secrets['gcp_service_account'] 설정이 필요합니다.")
        credentials = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"]
        )
        project_id = st.secrets["gcp_service_account"].get("project_id")
        self.client = firestore.Client(project=project_id, credentials=credentials)
        self.base_path = f"artifacts/{app_id}/users/{user_id}/product_analysis_reports_v3"
        self.col_ref = self.client.collection(self.base_path)

    def list_reports(self) -> List[Dict]:
        docs = self.col_ref.stream()
        rows = []
        for d in docs:
            data = d.to_dict() or {}
            data["id"] = d.id
            rows.append(data)
        def _key(x):
            try:
                return dt.fromisoformat(x.get("analysisDate", "1970-01-01"))
            except Exception:
                return dt(1970,1,1)
        rows.sort(key=_key, reverse=True)
        return rows

    def add_report(self, data: Dict) -> str:
        # Use server timestamps where possible
        doc_ref = self.col_ref.document()
        data = {
            **data,
            "createdAt": firestore.SERVER_TIMESTAMP,
            "updatedAt": firestore.SERVER_TIMESTAMP,
        }
        doc_ref.set(data)
        return doc_ref.id

    def update_report(self, doc_id: str, data: Dict) -> None:
        doc_ref = self.col_ref.document(doc_id)
        doc_ref.update({**data, "updatedAt": firestore.SERVER_TIMESTAMP})

    def delete_report(self, doc_id: str) -> None:
        self.col_ref.document(doc_id).delete()

# -----------------------------
# Helper functions
# -----------------------------
def merge_items_from_template(product_key: str, existing_items: Optional[List[Dict]]) -> List[Dict]:
    """Merge saved results onto the template list by itemName."""
    template_items = PRODUCT_CATALOG.get(product_key, {}).get("analysisItems", [])
    existing_items = existing_items or []
    merged = []
    for t in template_items:
        found = next((e for e in existing_items if e.get("itemName") == t.get("itemName")), None)
        merged.append({
            **t,
            "result": (found.get("result") if found else t.get("result", ""))
        })
    return merged

def get_storage() -> StorageBase:
    """Return Firestore storage if configured, else local JSON storage."""
    use_firestore = st.session_state.get("use_firestore", False)
    app_id = st.session_state.get("app_id", "default-app-id").strip() or "default-app-id"
    user_id = st.session_state.get("user_id", "").strip()

    if use_firestore:
        try:
            return FirestoreStorage(app_id, user_id)
        except Exception as e:
            st.error(f"Firestore 연결에 실패했습니다: {e}")
            st.session_state["use_firestore"] = False

    return LocalJSONStorage()

# -----------------------------
# UI - Sidebar
# -----------------------------
with st.sidebar:
    st.markdown("## 설정")
    st.write("저장소 선택: Firestore(권장) 또는 로컬 JSON")

    colA, colB = st.columns(2)
    app_id = colA.text_input("APP ID", value=st.session_state.get("app_id", "default-app-id"))
    user_id = colB.text_input("User ID", value=st.session_state.get("user_id", ""))

    st.session_state["app_id"] = app_id
    st.session_state["user_id"] = user_id

    # Firestore toggle
    fs_on = st.checkbox("Firestore 사용 (st.secrets 필요)", value=st.session_state.get("use_firestore", False))
    st.session_state["use_firestore"] = fs_on

    st.caption("※ Firestore 사용 시, Streamlit Secrets에 서비스 계정 JSON을 `gcp_service_account` 키로 넣어주세요.")
    st.caption("※ User ID는 경로 구분을 위해 사용됩니다. (예: artifacts/APP_ID/users/USER_ID/… )")

# -----------------------------
# UI - Header
# -----------------------------
st.title("제품 분석 일보")
st.write(f"**저장소**: {'Firestore' if st.session_state.get('use_firestore') else '로컬 JSON'}")
if st.session_state.get("use_firestore"):
    st.write(f"**경로**: artifacts/{st.session_state.get('app_id','default-app-id')}/users/{st.session_state.get('user_id','')}/product_analysis_reports_v3")

# Initialize session form state
if "form_state" not in st.session_state:
    st.session_state["form_state"] = {
        "editing_id": None,
        "product_key": "",
        "analysisDate": date.today(),
        "analystName": "",
        "analysisItems": [],
    }

form_state = st.session_state["form_state"]

# -----------------------------
# Input Form
# -----------------------------
st.header("새 보고서 작성 / 수정")

with st.form("report_form", clear_on_submit=False):
    # Product selection
    product_keys = [""] + list(PRODUCT_CATALOG.keys())
    product_labels = ["-- 제품을 선택하세요 --"] + [f"{PRODUCT_CATALOG[k]['name']} ({PRODUCT_CATALOG[k]['code']})" for k in PRODUCT_CATALOG]
    # map index to key
    try:
        current_index = product_keys.index(form_state["product_key"])
    except ValueError:
        current_index = 0
    idx = st.selectbox("제품 선택", options=range(len(product_keys)), format_func=lambda i: product_labels[i], index=current_index)
    selected_key = product_keys[idx]

    # When product changes, set items
    if selected_key != form_state["product_key"]:
        form_state["product_key"] = selected_key
        if selected_key:
            tmpl = PRODUCT_CATALOG[selected_key]
            form_state["analysisItems"] = merge_items_from_template(selected_key, form_state.get("analysisItems") or [])
        else:
            form_state["analysisItems"] = []

    # Show product code
    prod_code = PRODUCT_CATALOG.get(selected_key, {}).get("code", "—")
    st.caption(f"제품코드: {prod_code}")

    # Date & Analyst
    col1, col2 = st.columns(2)
    with col1:
        form_state["analysisDate"] = st.date_input("분석 일자", value=form_state.get("analysisDate") or date.today())
    with col2:
        form_state["analystName"] = st.text_input("분석자(작업자)", value=form_state.get("analystName",""))

    # Analysis items table
    if selected_key and form_state["analysisItems"]:
        st.markdown("#### 분석 항목")
        items = form_state["analysisItems"]
        for i, item in enumerate(items):
            c1, c2, c3 = st.columns([2, 2, 2.5])
            with c1:
                st.text_input("항목명", value=item["itemName"], disabled=True, key=f"itemName_{i}")
            with c2:
                st.text_input("규격", value=item["specification"], disabled=True, key=f"spec_{i}")
            with c3:
                items[i]["result"] = st.text_input("분석 결과", value=item.get("result",""), key=f"result_{i}")
        form_state["analysisItems"] = items

    # Buttons
    bcol1, bcol2, bcol3 = st.columns([1,1,6])
    submitted = bcol1.form_submit_button("저장" if not form_state["editing_id"] else "수정 완료")
    cancel_edit = bcol2.form_submit_button("취소", disabled=(form_state["editing_id"] is None))

# Handle form submission
if submitted:
    if not form_state["product_key"]:
        st.error("제품을 선택하세요.")
    else:
        storage = get_storage()
        product = PRODUCT_CATALOG[form_state["product_key"]]
        payload = {
            "productName": product["name"],
            "productCode": product["code"],
            "analysisDate": form_state["analysisDate"].isoformat() if isinstance(form_state["analysisDate"], date) else str(form_state["analysisDate"]),
            "analysisItems": form_state["analysisItems"],
            "analystName": form_state.get("analystName","").strip(),
        }
        try:
            if form_state["editing_id"]:
                storage.update_report(form_state["editing_id"], payload)
                st.success("보고서를 수정했습니다.")
            else:
                storage.add_report(payload)
                st.success("보고서를 저장했습니다.")
            # Reset form
            st.session_state["form_state"] = {
                "editing_id": None,
                "product_key": "",
                "analysisDate": date.today(),
                "analystName": "",
                "analysisItems": [],
            }
            st.experimental_rerun()
        except Exception as e:
            st.error(f"저장 중 오류가 발생했습니다: {e}")

if cancel_edit:
    st.session_state["form_state"] = {
        "editing_id": None,
        "product_key": "",
        "analysisDate": date.today(),
        "analystName": "",
        "analysisItems": [],
    }
    st.experimental_rerun()

# -----------------------------
# Reports List
# -----------------------------
st.header("누적 보고서 목록")
storage = get_storage()
try:
    reports = storage.list_reports()
except Exception as e:
    reports = []
    st.error(f"목록을 불러오지 못했습니다: {e}")

if not reports:
    st.info("저장된 보고서가 없습니다.")
else:
    for r in reports:
        with st.expander(f"{r.get('productName','?')} ({r.get('productCode','?')}) • {r.get('analysisDate','?')} • 분석자: {r.get('analystName') or '미기재'}", expanded=False):
            # Table-like display
            st.markdown("**분석 항목**")
            for item in r.get("analysisItems", []):
                c1, c2, c3 = st.columns([2,2,2.5])
                c1.write(f"**{item.get('itemName','')}**")
                c2.write(item.get("specification",""))
                c3.write(item.get("result",""))

            cA, cB, cC = st.columns([1,1,6])
            if cA.button("수정", key=f"edit_{r['id']}"):
                # Load into form_state and rerun
                # Map back to product key by code
                product_key = None
                for k, v in PRODUCT_CATALOG.items():
                    if v["code"] == r.get("productCode"):
                        product_key = k
                        break
                st.session_state["form_state"] = {
                    "editing_id": r["id"],
                    "product_key": product_key or "",
                    "analysisDate": date.fromisoformat(r.get("analysisDate","1970-01-01")) if r.get("analysisDate") else date.today(),
                    "analystName": r.get("analystName",""),
                    "analysisItems": merge_items_from_template(product_key or "", r.get("analysisItems", [])) if product_key else (r.get("analysisItems", [])),
                }
                st.experimental_rerun()

            if cB.button("삭제", key=f"del_{r['id']}"):
                st.session_state["confirm_delete_id"] = r["id"]
                st.experimental_rerun()

# Delete confirmation
del_id = st.session_state.get("confirm_delete_id")
if del_id:
    st.warning("정말 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.")
    cc1, cc2, cc3 = st.columns([1,1,6])
    if cc1.button("삭제 확인"):
        try:
            storage.delete_report(del_id)
            st.success("삭제했습니다.")
        except Exception as e:
            st.error(f"삭제 중 오류: {e}")
        finally:
            st.session_state["confirm_delete_id"] = None
            st.experimental_rerun()
    if cc2.button("취소"):
        st.session_state["confirm_delete_id"] = None
        st.experimental_rerun()

st.caption("ⓘ Firestore를 사용하지 않는 경우, 현재 작업 폴더의 product_analysis_reports.json 파일에 저장됩니다.")
