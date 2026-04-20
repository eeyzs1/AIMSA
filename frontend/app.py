import os
import time

import httpx
import streamlit as st

API_BASE = os.environ.get("API_BASE", st.secrets.get("API_BASE", "http://localhost:8000/api/v1"))

st.set_page_config(page_title="AIMSA", page_icon="📄", layout="wide")
st.title("📄 AIMSA - 智能文档问答")


def api_get(path: str):
    resp = httpx.get(f"{API_BASE}{path}", timeout=30.0)
    resp.raise_for_status()
    return resp.json()


def api_post(path: str, **kwargs):
    resp = httpx.post(f"{API_BASE}{path}", timeout=30.0, **kwargs)
    resp.raise_for_status()
    return resp.json()


tab_docs, tab_qa, tab_monitor = st.tabs(["📚 文档管理", "💬 智能问答", "📊 监控面板"])

with tab_docs:
    st.header("上传文档")
    uploaded = st.file_uploader("选择文件", type=["txt", "md", "pdf"], key="uploader")
    if uploaded and st.button("上传"):
        with st.spinner("上传中..."):
            try:
                files = {"file": (uploaded.name, uploaded.getvalue(), uploaded.type)}
                result = api_post("/documents/", files=files)
                st.success(f"上传成功! 文档ID: {result['id'][:8]}..., 状态: {result['status']}")
                st.rerun()
            except Exception as e:
                st.error(f"上传失败: {e}")

    st.divider()
    st.header("文档列表")
    if st.button("刷新列表"):
        st.rerun()
    try:
        docs = api_get("/documents/")
        if docs:
            for doc in docs:
                status_emoji = {"uploaded": "⏳", "processing": "⚙️", "ready": "✅", "failed": "❌"}.get(
                    doc["status"], "❓"
                )
                with st.expander(f"{status_emoji} {doc['filename']}"):
                    st.write(f"ID: `{doc['id']}`")
                    st.write(f"状态: {doc['status']}")
                    st.write(f"分块数: {doc['chunk_count']}")
                    st.write(f"上传时间: {doc['created_at']}")
        else:
            st.info("暂无文档，请先上传")
    except Exception as e:
        st.warning(f"无法获取文档列表: {e}")

with tab_qa:
    st.header("选择文档并提问")
    try:
        docs = api_get("/documents/")
        ready_docs = [d for d in docs if d["status"] == "ready"]
        if not ready_docs:
            st.info("暂无可用的文档，请先上传并等待处理完成")
        else:
            doc_options = {f"{d['filename']} ({d['id'][:8]})": d["id"] for d in ready_docs}
            selected = st.selectbox("选择文档", list(doc_options.keys()))
            doc_id = doc_options[selected]

            question = st.text_input("输入你的问题")
            if st.button("提问") and question:
                with st.spinner("思考中... (异步处理，可能需要几秒)"):
                    try:
                        result = api_post("/questions/", json={"document_id": doc_id, "question": question})
                        q_id = result["id"]

                        q = None
                        for _ in range(60):
                            time.sleep(2)
                            q = api_get(f"/questions/{q_id}")
                            if q["status"] in ("completed", "failed"):
                                break

                        if q and q["status"] == "completed":
                            st.success("回答完成!")
                            st.markdown(f"**回答:** {q['answer']}")
                        elif q and q["status"] == "failed":
                            st.error(f"处理失败: {q.get('answer', '未知错误')}")
                        else:
                            st.warning("处理超时，请稍后在历史问答中查看结果")
                    except Exception as e:
                        st.error(f"提问失败: {e}")

            st.divider()
            st.subheader("历史问答")
            if st.button("刷新历史"):
                st.rerun()
            try:
                questions = api_get(f"/questions/by-document/{doc_id}")
                for q in questions[:10]:
                    icon = "✅" if q["status"] == "completed" else "⏳" if q["status"] == "pending" else "❌"
                    with st.expander(f"{icon} {q['question'][:50]}"):
                        st.write(f"问题: {q['question']}")
                        st.write(f"回答: {q.get('answer', '处理中...')}")
                        st.write(f"状态: {q['status']}")
            except Exception:
                pass
    except Exception as e:
        st.warning(f"无法连接后端服务: {e}")

with tab_monitor:
    st.header("系统监控")
    col1, col2, col3 = st.columns(3)
    try:
        stats = api_get("/monitoring/stats")
        col1.metric("总推理次数", stats["total_inferences"])
        col2.metric("平均延迟", f"{stats['avg_latency']:.2f}s")
        col3.metric("失败次数", stats["failure_count"])

        col4, col5 = st.columns(2)
        col4.metric("最近1小时推理", stats["recent_inferences_1h"])
        col5.metric("最大延迟", f"{stats['max_latency']:.2f}s")
    except Exception as e:
        st.warning(f"无法获取监控数据: {e}")

    try:
        health = api_get("/monitoring/health")
        st.json(health)
    except Exception:
        st.error("后端服务不可达")

    st.divider()
    if st.button("刷新监控数据"):
        st.rerun()
