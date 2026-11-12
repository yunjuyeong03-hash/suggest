import os
import streamlit as st
from supabase import create_client, Client

# 페이지 제목 설정
st.title("💡 한 줄 건의함")
st.caption("자유롭게 한 줄로 건의사항을 남겨주세요. (익명 보장 · 실시간 DB 저장)")

# Supabase 클라이언트 초기화 (캐싱하여 재실행 시 연결 재사용)
@st.cache_resource
def init_supabase() -> Client:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        st.error("환경 변수 'SUPABASE_URL' 또는 'SUPABASE_KEY'가 설정되지 않았습니다.")
        st.stop()
    return create_client(url, key)

supabase = init_supabase()

# 입력 폼 생성
with st.form(key="suggestion_form", clear_on_submit=True):
    col1, col2 = st.columns([1, 3])
    
    with col1:
        # 테이블의 category 컬럼에 맞춘 선택창
        category = st.selectbox(
            "분류",
            ["일반", "시설/환경", "프로그램", "기타"],
            label_visibility="collapsed"
        )
    with col2:
        user_input = st.text_input(
            "건의사항을 입력하세요",
            placeholder="여기에 한 줄로 작성해 주세요...",
            label_visibility="collapsed"
        )
        
    submit_button = st.form_submit_button(label="제출하기")

# 제출 버튼 클릭 처리
if submit_button:
    cleaned_input = user_input.strip()
    if cleaned_input:
        try:
            # suggestions 테이블에 데이터 삽입 (id, created_at은 DB 자동 생성 기준)
            supabase.table("suggestions").insert({
                "content": cleaned_input,
                "category": category,
                "likes": 0
            }).execute()
            st.success("건의사항이 데이터베이스에 등록되었습니다!")
        except Exception as e:
            st.error(f"저장 중 오류가 발생했습니다: {e}")
    else:
        st.warning("내용을 입력한 후 제출해 주세요.")

st.divider()

# 건의 목록 출력 (created_at 기준 최신순)
st.subheader("📋 제출된 건의 목록")

try:
    # 최신순(desc=True)으로 데이터 조회
    response = (
        supabase.table("suggestions")
        .select("id, content, category, likes, created_at")
        .order("created_at", desc=True)
        .execute()
    )
    suggestions = response.data

    if suggestions:
        for item in suggestions:
            col_text, col_like = st.columns([5, 1])
            
            with col_text:
                cat_badge = f"`[{item.get('category') or '일반'}]`"
                st.markdown(f"{cat_badge} {item['content']}")
                
            with col_like:
                # 좋아요 버튼 클릭 시 likes 컬럼 +1 업데이트
                like_count = item.get("likes", 0) or 0
                if st.button(f"👍 {like_count}", key=f"like_{item['id']}"):
                    supabase.table("suggestions").update(
                        {"likes": like_count + 1}
                    ).eq("id", item["id"]).execute()
                    st.rerun()
    else:
        st.info("아직 등록된 건의사항이 없습니다.")

except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")