import hashlib
import os
import time

import requests
import streamlit as st


st.set_page_config(
    page_title="AI Repository Intelligence",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "http://127.0.0.1:8000",
).rstrip("/")



st.markdown(
    """
    <style>
        @import url(
            'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap'
        );

        .stApp {
            font-family: 'Inter', sans-serif;
        }

        .main-title {
            font-size: 2.6rem;
            font-weight: 800;
            margin-bottom: 0.2rem;
        }

        .subtitle {
            font-size: 1rem;
            opacity: 0.7;
            margin-bottom: 1.5rem;
        }

        .repo-card {
            padding: 1.4rem;
            border-radius: 16px;
            border: 1px solid rgba(128,128,128,0.25);
            margin-bottom: 1rem;
        }

        .source-card {
            padding: 1rem;
            border-radius: 12px;
            border: 1px solid rgba(128,128,128,0.22);
            margin-bottom: 0.7rem;
        }

        .metric-card {
            padding: 1rem;
            border-radius: 14px;
            border: 1px solid rgba(128,128,128,0.22);
            text-align: center;
        }

        .metric-value {
            font-size: 1.7rem;
            font-weight: 800;
        }

        .metric-label {
            font-size: 0.85rem;
            opacity: 0.65;
        }

        .status-connected {
            padding: 0.55rem 0.8rem;
            border-radius: 10px;
            border: 1px solid rgba(0,180,100,0.35);
            background: rgba(0,180,100,0.08);
        }

        .status-error {
            padding: 0.55rem 0.8rem;
            border-radius: 10px;
            border: 1px solid rgba(220,60,60,0.35);
            background: rgba(220,60,60,0.08);
        }

        div[data-testid="stChatMessage"] {
            border-radius: 14px;
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
    return hashlib.sha256(
        url.strip().lower().encode("utf-8")
    ).hexdigest()[:16]


def api_get(path: str, timeout: int = 20):
    url = f"{API_BASE_URL}{path}"
    return requests.get(url, timeout=timeout)


def api_post(path: str, payload: dict, timeout: int = 30):
    url = f"{API_BASE_URL}{path}"
    return requests.post(
        url,
        json=payload,
        timeout=timeout,
    )


def format_number(value):
    if value is None:
        return "—"

    try:
        return f"{int(value):,}"
    except (ValueError, TypeError):
        return str(value)


def extract_error(response):
    try:
        data = response.json()

        if isinstance(data, dict):
            if "detail" in data:
                return str(data["detail"])

            if "error" in data:
                return str(data["error"])

        return response.text

    except Exception:
        return response.text

def check_backend():
    try:
        response = api_get("/health", timeout=5)

        if response.status_code == 200:
            try:
                data = response.json()
            except Exception:
                data = {}

            return True, data

        return False, f"HTTP {response.status_code}"

    except requests.exceptions.RequestException as exc:
        return False, str(exc)


def prepare_repository(url: str):
    response = api_post(
        "/prepare",
        {
            "repository_url": url,
        },
        timeout=30,
    )

    if response.status_code not in (200, 201, 202):
        raise RuntimeError(extract_error(response))

    return response.json()

def get_prepare_status(repository_key_value: str):
    response = api_get(
        f"/prepare/status/{repository_key_value}",
        timeout=20,
    )

    if response.status_code != 200:
        raise RuntimeError(extract_error(response))

    return response.json()



def ask_repository(question: str, top_k: int = 5):
    repository_url = st.session_state.get("repository_url", "").strip()

    if not repository_url:
        raise RuntimeError(
            "No repository is selected. Please analyze a repository first."
        )

    response = api_post(
        "/ask",
        {
            "repository_url": repository_url,
            "question": question.strip(),
            "top_k": top_k,
        },
        timeout=120,
    )

    if response.status_code != 200:
        raise RuntimeError(extract_error(response))

    return response.json()


with st.sidebar:

    st.markdown("## 🤖 Repository AI")

    st.caption(
        "AI-powered GitHub repository analysis"
    )

    st.divider()

    connected, health_data = check_backend()

    if connected:
        st.success("Backend connected")
    else:
        st.error("Backend not connected")

        with st.expander("Connection details"):
            st.code(API_BASE_URL)
            st.caption(str(health_data))

    st.divider()

    st.markdown("### Backend")

    st.code(
        API_BASE_URL,
        language="text",
    )

    st.divider()

    if st.button(
        "🔄 Check Backend",
        use_container_width=True,
    ):
        st.rerun()

    if st.session_state.repo_ready:

        st.divider()

        if st.button(
            "🆕 New Repository",
            use_container_width=True,
        ):
            st.session_state.repository_url = ""
            st.session_state.repository_key = ""
            st.session_state.repo_info = None
            st.session_state.repo_ready = False
            st.session_state.messages = []
            st.session_state.last_error = None

            st.rerun()


st.markdown(
    '<div class="main-title">AI Repository Intelligence</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">'
    "Understand any accessible GitHub repository using AI-powered "
    "semantic search and RAG."
    "</div>",
    unsafe_allow_html=True,
)


if not st.session_state.repo_ready:

    st.markdown("### 🔗 Analyze a GitHub Repository")

    st.info(
        "Enter the URL of any accessible GitHub repository."
    )

    repository_url = st.text_input(
        "GitHub Repository URL",
        value=st.session_state.repository_url,
        placeholder="https://github.com/owner/repository",
        label_visibility="collapsed",
    )

    analyze_clicked = st.button(
        "🚀 Analyze Repository",
        type="primary",
        use_container_width=True,
    )

    if analyze_clicked:

        if not repository_url.strip():
            st.warning(
                "Please enter a GitHub repository URL."
            )
            st.stop()

        repository_url = repository_url.strip()

        st.session_state.repository_url = repository_url
        st.session_state.repository_key = repository_key(
            repository_url
        )
        st.session_state.last_error = None

        try:

            with st.status(
                "Preparing repository...",
                expanded=True,
            ) as status:

                st.write("🔍 Checking repository/index...")

                prepare_data = prepare_repository(
                    repository_url
                )

                current_status = prepare_data.get(
                    "status",
                    "processing",
                )

                repository_key_value = prepare_data.get(
                    "repository_key",
                    st.session_state.repository_key,
                )

                st.session_state.repository_key = (
                    repository_key_value
                )

                if current_status in (
                    "created",
                    "loaded",
                    "ready",
                    "completed",
                ):

                    st.write(
                        "✅ Repository is ready."
                    )

                    st.session_state.repo_info = (
                        prepare_data
                    )

                    st.session_state.repo_ready = True

                    status.update(
                        label="Repository ready",
                        state="complete",
                    )

                else:

                    progress = st.progress(0)

                    max_attempts = 600

                    for attempt in range(max_attempts):

                        time.sleep(2)

                        status_data = get_prepare_status(
                            repository_key_value
                        )

                        status_value = status_data.get(
                            "status",
                            "processing",
                        )

                        stage = status_data.get(
                            "stage",
                            "",
                        )

                        if stage:
                            st.write(
                                f"⚙️ {stage}"
                            )

                        if status_value in (
                            "created",
                            "loaded",
                            "ready",
                            "completed",
                        ):

                            progress.progress(100)

                            st.session_state.repo_info = (
                                status_data
                            )

                            st.session_state.repo_ready = (
                                True
                            )

                            status.update(
                                label="Repository ready",
                                state="complete",
                            )

                            break

                        if status_value in (
                            "failed",
                            "error",
                        ):

                            error_message = (
                                status_data.get(
                                    "error",
                                    "Repository preparation failed.",
                                )
                            )

                            raise RuntimeError(
                                error_message
                            )

                        progress.progress(
                            min(
                                int(
                                    (
                                        attempt + 1
                                    )
                                    / max_attempts
                                    * 100
                                ),
                                99,
                            )
                        )

                    else:
                        raise RuntimeError(
                            "Repository preparation timed out."
                        )

        except Exception as exc:

            st.session_state.last_error = str(exc)

            st.error(
                f"❌ Failed to prepare repository: {exc}"
            )

            st.stop()

        st.rerun()


if st.session_state.repo_ready:

    repo_info = st.session_state.repo_info or {}

    repository_name = repo_info.get(
        "repository",
        st.session_state.repository_url,
    )

    st.markdown(
        f"### 📦 {repository_name}"
    )

    st.caption(
        st.session_state.repository_url
    )

    st.divider()

    total_files = repo_info.get(
        "total_files"
    )

    total_skipped = repo_info.get(
        "total_skipped"
    )

    total_chunks = repo_info.get(
        "total_chunks"
    )

    embedding_dimension = repo_info.get(
        "embedding_dimension"
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            '<div class="metric-card">'
            f'<div class="metric-value">{format_number(total_files)}</div>'
            '<div class="metric-label">Files indexed</div>'
            "</div>",
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            '<div class="metric-card">'
            f'<div class="metric-value">{format_number(total_skipped)}</div>'
            '<div class="metric-label">Files skipped</div>'
            "</div>",
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            '<div class="metric-card">'
            f'<div class="metric-value">{format_number(total_chunks)}</div>'
            '<div class="metric-label">Chunks</div>'
            "</div>",
            unsafe_allow_html=True,
        )

    with col4:
        st.markdown(
            '<div class="metric-card">'
            f'<div class="metric-value">{format_number(embedding_dimension)}</div>'
            '<div class="metric-label">Embedding dimension</div>'
            "</div>",
            unsafe_allow_html=True,
        )

    st.divider()


    st.markdown("### 🧠 Repository Overview")

    overview_col1, overview_col2 = st.columns(2)

    with overview_col1:

        st.markdown(
            '<div class="repo-card">',
            unsafe_allow_html=True,
        )

        st.markdown("**Repository**")

        st.write(
            repository_name
        )

        st.markdown("**Repository Key**")

        st.code(
            st.session_state.repository_key
        )

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )

    with overview_col2:

        st.markdown(
            '<div class="repo-card">',
            unsafe_allow_html=True,
        )

        st.markdown("**Status**")

        st.success("Ready for questions")

        st.markdown("**Architecture**")

        st.write(
            "GitHub → Chunking → Embeddings → FAISS → "
            "Semantic Retrieval → RAG → LLM"
        )

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )

    st.divider()

    st.markdown("### 💡 Suggested Questions")

    suggestions = [
        "What is this repository about?",
        "Explain the project architecture.",
        "Where is the main application entry point?",
        "How does the repository handle configuration?",
        "What are the main modules in this project?",
        "How do I run this project locally?",
    ]

    suggestion_cols = st.columns(3)

    for index, question in enumerate(suggestions):

        with suggestion_cols[index % 3]:

            if st.button(
                question,
                key=f"suggestion_{index}",
                use_container_width=True,
            ):
                st.session_state.messages.append(
                    {
                        "role": "user",
                        "content": question,
                    }
                )

                try:

                    result = ask_repository(
                        question
                    )

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": result.get(
                                "answer",
                                "No answer returned.",
                            ),
                            "sources": result.get(
                                "sources",
                                [],
                            ),
                        }
                    )

                except Exception as exc:

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": (
                                f"❌ Error: {exc}"
                            ),
                        }
                    )

                st.rerun()

    st.divider()

    st.markdown("### 💬 Ask About Your Repository")

    for message in st.session_state.messages:

        with st.chat_message(
            message["role"]
        ):

            st.markdown(
                message["content"]
            )

            sources = message.get(
                "sources",
                [],
            )

            if sources:

                with st.expander(
                    f"📚 Sources ({len(sources)})"
                ):

                    for source in sources:

                        if isinstance(
                            source,
                            dict,
                        ):

                            file_path = source.get(
                                "file_path",
                                source.get(
                                    "path",
                                    "Unknown file",
                                ),
                            )

                            chunk_index = source.get(
                                "chunk_index",
                                0,
                            )

                            st.markdown(
                                '<div class="source-card">',
                                unsafe_allow_html=True,
                            )

                            st.markdown(
                                f"**📄 {file_path}**"
                            )

                            st.caption(
                                f"Chunk: {chunk_index}"
                            )

                            st.markdown(
                                "</div>",
                                unsafe_allow_html=True,
                            )

                        else:

                            st.write(
                                str(source)
                            )

    user_question = st.chat_input(
        "Ask something about the repository..."
    )

    if user_question:

        user_question = user_question.strip()

        if user_question:

            st.session_state.messages.append(
                {
                    "role": "user",
                    "content": user_question,
                }
            )

            with st.chat_message("assistant"):

                with st.spinner(
                    "Searching repository..."
                ):

                    try:

                        result = ask_repository(
                            user_question
                        )

                        answer = result.get(
                            "answer",
                            "No answer returned.",
                        )

                        sources = result.get(
                            "sources",
                            [],
                        )

                        st.markdown(
                            answer
                        )

                        if sources:

                            with st.expander(
                                f"📚 Sources ({len(sources)})"
                            ):

                                for source in sources:

                                    if isinstance(
                                        source,
                                        dict,
                                    ):

                                        file_path = source.get(
                                            "file_path",
                                            source.get(
                                                "path",
                                                "Unknown file",
                                            ),
                                        )

                                        chunk_index = source.get(
                                            "chunk_index",
                                            0,
                                        )

                                        st.markdown(
                                            '<div class="source-card">',
                                            unsafe_allow_html=True,
                                        )

                                        st.markdown(
                                            f"**📄 {file_path}**"
                                        )

                                        st.caption(
                                            f"Chunk: {chunk_index}"
                                        )

                                        st.markdown(
                                            "</div>",
                                            unsafe_allow_html=True,
                                        )

                                    else:

                                        st.write(
                                            str(source)
                                        )

                        st.session_state.messages.append(
                            {
                                "role": "assistant",
                                "content": answer,
                                "sources": sources,
                            }
                        )

                    except Exception as exc:

                        error_message = (
                            f"❌ Failed to get answer: {exc}"
                        )

                        st.error(
                            error_message
                        )

                        st.session_state.messages.append(
                            {
                                "role": "assistant",
                                "content": error_message,
                            }
                        )

            st.rerun()
