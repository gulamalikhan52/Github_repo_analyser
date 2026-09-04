
import hashlib
import time

import requests
import streamlit as st


st.set_page_config(
    page_title="AI Repository Intelligence",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_BASE_URL = "http://127.0.0.1:8000"


st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    .stApp {
        font-family: 'Inter', sans-serif;
    }

    #MainMenu, footer, header {
        visibility: hidden;
    }

    .block-container {
        max-width: 1400px;
        padding-top: 1.5rem;
        padding-bottom: 3rem;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        border-right: 1px solid rgba(128,128,128,.16);
    }

    [data-testid="stSidebar"] > div:first-child {
        padding-top: 1.5rem;
    }

    .brand {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 28px;
    }

    .brand-icon {
        width: 44px;
        height: 44px;
        border-radius: 14px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 22px;
        background: linear-gradient(135deg, #6d5dfc, #9b8cff);
        box-shadow: 0 8px 24px rgba(109,93,252,.25);
    }

    .brand-title {
        font-size: 17px;
        font-weight: 800;
        line-height: 1.1;
    }

    .brand-subtitle {
        font-size: 11px;
        opacity: .58;
        margin-top: 3px;
    }

    .hero {
        padding: 28px 30px;
        border-radius: 24px;
        background:
            radial-gradient(circle at 90% 10%, rgba(109,93,252,.22), transparent 32%),
            radial-gradient(circle at 10% 100%, rgba(77,171,247,.13), transparent 30%),
            rgba(128,128,128,.055);
        border: 1px solid rgba(128,128,128,.14);
        margin-bottom: 22px;
    }

    .eyebrow {
        display: inline-flex;
        padding: 6px 10px;
        border-radius: 999px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: .04em;
        text-transform: uppercase;
        background: rgba(109,93,252,.12);
        color: #9b8cff;
        margin-bottom: 12px;
    }

    .hero h1 {
        margin: 0;
        font-size: clamp(30px, 4vw, 48px);
        line-height: 1.05;
        letter-spacing: -0.04em;
    }

    .hero p {
        margin: 12px 0 0;
        max-width: 720px;
        opacity: .68;
        font-size: 14px;
        line-height: 1.65;
    }

    .metric {
        padding: 18px 20px;
        min-height: 112px;
        border-radius: 18px;
        border: 1px solid rgba(128,128,128,.14);
        background: rgba(128,128,128,.045);
    }

    .metric-label {
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: .07em;
        opacity: .52;
        font-weight: 700;
    }

    .metric-value {
        font-size: 26px;
        font-weight: 800;
        margin-top: 9px;
    }

    .metric-note {
        font-size: 11px;
        opacity: .48;
        margin-top: 3px;
    }

    .section-title {
        font-size: 18px;
        font-weight: 800;
        margin: 28px 0 12px;
    }

    .repo-card {
        border: 1px solid rgba(128,128,128,.14);
        border-radius: 18px;
        padding: 18px 20px;
        background: rgba(128,128,128,.045);
    }

    .repo-name {
        font-weight: 800;
        font-size: 16px;
    }

    .repo-url {
        opacity: .52;
        font-size: 12px;
        margin-top: 5px;
        overflow-wrap: anywhere;
    }

    .stage {
        padding: 14px 16px;
        border-radius: 14px;
        border: 1px solid rgba(128,128,128,.12);
        background: rgba(128,128,128,.04);
        font-size: 13px;
        margin: 10px 0;
    }

    .chat-shell {
        border: 1px solid rgba(128,128,128,.14);
        border-radius: 22px;
        padding: 18px;
        background: rgba(128,128,128,.035);
    }

    .source-card {
        border: 1px solid rgba(128,128,128,.13);
        border-radius: 14px;
        padding: 13px 15px;
        margin: 8px 0;
        background: rgba(128,128,128,.035);
    }

    .source-path {
        font-size: 12px;
        font-weight: 700;
        overflow-wrap: anywhere;
    }

    .source-meta {
        font-size: 10px;
        opacity: .5;
        margin-top: 4px;
    }

    .tip {
        padding: 13px 14px;
        border-radius: 14px;
        background: rgba(109,93,252,.08);
        border: 1px solid rgba(109,93,252,.16);
        font-size: 12px;
        line-height: 1.5;
    }

    .empty-state {
        text-align: center;
        padding: 56px 20px;
        border: 1px dashed rgba(128,128,128,.25);
        border-radius: 22px;
        opacity: .7;
    }

    div[data-testid="stButton"] > button {
        border-radius: 12px;
        min-height: 42px;
        font-weight: 700;
    }

    div[data-testid="stTextInput"] input {
        border-radius: 12px;
    }

    .small-muted {
        font-size: 11px;
        opacity: .5;
    }
</style>
""",
    unsafe_allow_html=True,
)

defaults = {
    "repository_url": "",
    "repository_key": "",
    "repo_info": None,
    "repo_ready": False,
    "messages": [],
    "last_error": None,
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


def repository_key(url: str) -> str:
    return hashlib.sha256(url.strip().lower().encode("utf-8")).hexdigest()[:16]


def api_get(path: str, timeout: int = 20):
    return requests.get(f"{API_BASE_URL}{path}", timeout=timeout)


def api_post(path: str, payload: dict, timeout: int = 30):
    return requests.post(f"{API_BASE_URL}{path}", json=payload, timeout=timeout)


def format_number(value):
    if value is None:
        return "—"
    try:
        return f"{int(value):,}"
    except (ValueError, TypeError):
        return str(value)



with st.sidebar:
    st.markdown(
        """
        <div class="brand">
            <div class="brand-icon">🤖</div>
            <div>
                <div class="brand-title">Repository AI</div>
                <div class="brand-subtitle">Code intelligence workspace</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Workspace")

    if st.session_state.repo_ready:
        st.success("Repository ready")
    else:
        st.info("No repository loaded")

    if st.button("＋ New repository", use_container_width=True):
        st.session_state.repository_url = ""
        st.session_state.repository_key = ""
        st.session_state.repo_info = None
        st.session_state.repo_ready = False
        st.session_state.messages = []
        st.session_state.last_error = None
        st.rerun()

    st.markdown("---")

    st.markdown(
        """
        <div class="tip">
            <b>💡 Try asking</b><br>
            • Where is the main application defined?<br>
            • Explain the project architecture<br>
            • Where is authentication handled?<br>
            • Which files implement the API?
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.markdown('<div class="small-muted">FastAPI + FAISS + SentenceTransformers + Groq</div>', unsafe_allow_html=True)


st.markdown(
    """
    <div class="hero">
        <div class="eyebrow">AI-powered codebase exploration</div>
        <h1>Understand any GitHub repository.</h1>
        <p>
            Connect a repository, build a semantic index, and chat with your codebase.
            Get grounded answers with the exact files used to generate each response.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


left, right = st.columns([5, 1.15])

with left:
    url = st.text_input(
        "GitHub repository URL",
        value=st.session_state.repository_url,
        placeholder="https://github.com/owner/repository",
        label_visibility="visible",
    )

with right:
    analyze = st.button("🚀 Analyze", type="primary", use_container_width=True)

if analyze:
    clean_url = url.strip()

    if not clean_url:
        st.error("Please enter a GitHub repository URL.")
    elif not clean_url.startswith(("https://github.com/", "http://github.com/")):
        st.error("Please enter a valid GitHub repository URL.")
    else:
        st.session_state.repository_url = clean_url
        st.session_state.repository_key = repository_key(clean_url)
        st.session_state.repo_ready = False
        st.session_state.repo_info = None
        st.session_state.messages = []

        try:
            response = api_post(
                "/prepare",
                {"repository_url": clean_url},
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

            status = data.get("status", "processing")

            if status in ("created", "ready", "loaded"):
                st.session_state.repo_info = data
                st.session_state.repo_ready = True
                st.success("Repository is ready.")
                st.rerun()

            elif status == "processing":
                status_box = st.empty()
                stage_box = st.empty()
                progress = st.progress(0)
                start = time.time()

                for attempt in range(600):
                    try:
                        status_response = api_get(
                            f"/prepare/status/{st.session_state.repository_key}",
                            timeout=20,
                        )
                        status_response.raise_for_status()
                        current = status_response.json()
                    except requests.RequestException as exc:
                        status_box.warning(f"Waiting for backend… {exc}")
                        time.sleep(2)
                        continue

                    current_status = current.get("status")
                    stage = current.get("stage", "")

                    elapsed = int(time.time() - start)
                    progress_value = min((attempt + 1) / 600, 0.99)
                    progress.progress(progress_value)

                    stage_label = stage.replace("_", " ").title() if stage else "Preparing repository"
                    stage_box.markdown(
                        f'<div class="stage">⚙️ <b>{stage_label}</b> · {elapsed // 60}m {elapsed % 60:02d}s elapsed</div>',
                        unsafe_allow_html=True,
                    )

                    if current_status in ("created", "ready", "loaded") or stage == "completed":
                        progress.progress(1.0)
                        st.session_state.repo_info = current
                        st.session_state.repo_ready = True
                        status_box.success("Repository indexed successfully.")
                        time.sleep(0.5)
                        st.rerun()

                    if current_status == "failed":
                        error = current.get("error", "Repository preparation failed.")
                        st.session_state.last_error = error
                        status_box.error(error)
                        break

                    status_box.info("🔄 Building your repository intelligence index…")
                    time.sleep(2)

                else:
                    st.error("Preparation is taking longer than expected. Check the backend logs.")

        except requests.RequestException as exc:
            st.error(
                "Could not connect to the backend. Start FastAPI first with "
                "`python -m uvicorn backend.main:app`."
            )
        except Exception as exc:
            st.error(f"Unexpected error: {exc}")



if st.session_state.repo_ready and st.session_state.repo_info:
    info = st.session_state.repo_info

    st.markdown('<div class="section-title">Repository overview</div>', unsafe_allow_html=True)

    repo_name = info.get("repository", st.session_state.repository_url)
    st.markdown(
        f"""
        <div class="repo-card">
            <div class="repo-name">📦 {repo_name}</div>
            <div class="repo-url">{st.session_state.repository_url}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(
            f"""
            <div class="metric">
                <div class="metric-label">Files</div>
                <div class="metric-value">{format_number(info.get("total_files"))}</div>
                <div class="metric-note">Analyzable files</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            f"""
            <div class="metric">
                <div class="metric-label">Chunks</div>
                <div class="metric-value">{format_number(info.get("total_chunks"))}</div>
                <div class="metric-note">Semantic chunks</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c3:
        st.markdown(
            f"""
            <div class="metric">
                <div class="metric-label">Embedding</div>
                <div class="metric-value">{format_number(info.get("embedding_dimension"))}</div>
                <div class="metric-note">Vector dimensions</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c4:
        skipped = info.get("total_skipped")
        st.markdown(
            f"""
            <div class="metric">
                <div class="metric-label">Skipped</div>
                <div class="metric-value">{format_number(skipped)}</div>
                <div class="metric-note">Ignored files</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    
    st.markdown('<div class="section-title">💬 Ask your repository</div>', unsafe_allow_html=True)

    if not st.session_state.messages:
        st.markdown(
            """
            <div class="empty-state">
                <div style="font-size:36px">🧠</div>
                <h3>Start exploring your codebase</h3>
                <div>Ask about architecture, functions, files, APIs, configuration, or implementation details.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            if message.get("sources"):
                with st.expander(f"📚 {len(message['sources'])} sources used"):
                    for index, source in enumerate(message["sources"], start=1):
                        path = source.get("file_path") or source.get("path") or "Unknown file"
                        score = source.get("score")
                        score_text = f" · score {score:.3f}" if isinstance(score, (int, float)) else ""

                        st.markdown(
                            f"""
                            <div class="source-card">
                                <div class="source-path">{index}. 📄 {path}</div>
                                <div class="source-meta">Retrieved context{score_text}</div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

    question = st.chat_input("Ask something about this repository…")

    if question:
        question = question.strip()

        if question:
            st.session_state.messages.append(
                {"role": "user", "content": question}
            )

            with st.chat_message("user"):
                st.markdown(question)

            with st.chat_message("assistant"):
                with st.spinner("Searching the codebase…"):
                    try:
                        response = api_post(
                            "/ask",
                            {
                                "repository_url": st.session_state.repository_url,
                                "question": question,
                                "top_k": 5,
                            },
                            timeout=180,
                        )
                        response.raise_for_status()
                        result = response.json()

                        answer = result.get("answer", "No answer returned.")
                        sources = result.get("sources", [])

                        st.markdown(answer)

                        if sources:
                            with st.expander(f"📚 {len(sources)} sources used", expanded=True):
                                for index, source in enumerate(sources, start=1):
                                    path = source.get("file_path") or source.get("path") or "Unknown file"
                                    score = source.get("score")
                                    score_text = f" · score {score:.3f}" if isinstance(score, (int, float)) else ""

                                    st.markdown(
                                        f"""
                                        <div class="source-card">
                                            <div class="source-path">{index}. 📄 {path}</div>
                                            <div class="source-meta">Retrieved context{score_text}</div>
                                        </div>
                                        """,
                                        unsafe_allow_html=True,
                                    )

                        st.session_state.messages.append(
                            {
                                "role": "assistant",
                                "content": answer,
                                "sources": sources,
                            }
                        )

                    except requests.HTTPError as exc:
                        try:
                            detail = response.json().get("detail", str(exc))
                        except Exception:
                            detail = str(exc)
                        st.error(f"Backend error: {detail}")
                    except requests.RequestException:
                        st.error("Could not connect to the FastAPI backend.")
                    except Exception as exc:
                        st.error(f"Unexpected error: {exc}")

else:
    st.markdown(
        """
        <div class="section-title">How it works</div>
        """,
        unsafe_allow_html=True,
    )

    a, b, c = st.columns(3)

    with a:
        st.markdown(
            """
            <div class="metric">
                <div style="font-size:22px">1️⃣</div>
                <div style="font-weight:800;margin-top:10px">Connect</div>
                <div class="metric-note">Paste any accessible GitHub repository URL.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with b:
        st.markdown(
            """
            <div class="metric">
                <div style="font-size:22px">2️⃣</div>
                <div style="font-weight:800;margin-top:10px">Index</div>
                <div class="metric-note">Files are chunked, embedded and stored in FAISS.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c:
        st.markdown(
            """
            <div class="metric">
                <div style="font-size:22px">3️⃣</div>
                <div style="font-weight:800;margin-top:10px">Ask</div>
                <div class="metric-note">Chat with the repository using grounded retrieval.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
