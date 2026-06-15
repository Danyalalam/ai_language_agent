import io
import json

import pandas as pd
import requests
import streamlit as st

DEFAULT_API = "http://127.0.0.1:8000"

st.set_page_config(page_title="Pronunciation Analysis", layout="wide")
st.title("Pronunciation Analysis Dashboard")

api_base = st.sidebar.text_input("API base URL", DEFAULT_API)
mode = st.sidebar.selectbox("Pronunciation Mode", ["Reading", "Gaming"])
st.sidebar.markdown("API endpoints:\n- Reading: /analyze\n- Gaming: /analyze-gaming")

uploaded = st.file_uploader("Upload audio file", type=["wav", "mp3", "m4a", "flac", "ogg"])
language = st.sidebar.selectbox("Language", ["en-US"], index=0)
enable_prosody = st.sidebar.checkbox("Enable prosody", value=True)

reference_text = ""
game_prompt = ""
enable_miscue = True

if mode == "Reading":
    st.subheader("Reading Mode")
    reference_text = st.text_area("Reference text (script to score against)", height=140)
    enable_miscue = st.checkbox("Enable miscue detection (insertions/omissions)", value=True)
    analyze_label = "Analyze Reading"
else:
    st.subheader("Gaming Mode")
    game_prompt = st.text_input("Short gaming prompt (tongue twister / syllable prompt)")
    analyze_label = "Analyze Gaming"


def call_api(endpoint: str, file_bytes: bytes, filename: str, data: dict):
    file_obj = io.BytesIO(file_bytes)
    files = {"file": (filename, file_obj, "audio/wav")}
    resp = requests.post(endpoint, files=files, data=data, timeout=120)
    return resp


def render_result(result: dict):
    azure = result.get("azure_result", {})
    ai = result.get("ai_report", {})

    st.subheader("Azure Metrics")
    cols = st.columns(5)
    cols[0].metric("Overall", f"{azure.get('overall_score', 0):.1f}")
    cols[1].metric("Accuracy", f"{azure.get('accuracy_score', 0):.1f}")
    cols[2].metric("Fluency", f"{azure.get('fluency_score', 0):.1f}")
    cols[3].metric("Completeness", f"{azure.get('completeness_score', 0):.1f}")
    prosody = azure.get("prosody_score")
    cols[4].metric("Prosody", f"{float(prosody):.1f}" if prosody is not None else "N/A")

    st.subheader("Word-level Details")
    word_details = azure.get("word_details", [])
    if word_details:
        df = pd.DataFrame(word_details)
        st.dataframe(df, use_container_width=True)
    else:
        st.write("No word-level details available.")

    st.subheader("AI-generated Report")
    st.markdown("**Summary**")
    st.write(ai.get("summary", ""))

    st.markdown("**Strengths**")
    for s in ai.get("strengths", []):
        st.write(f"- {s}")

    st.markdown("**Weaknesses**")
    for w in ai.get("weaknesses", []):
        st.write(f"- {w}")

    st.markdown("**Recommendations**")
    for r in ai.get("recommendations", []):
        st.write(f"- {r}")

    st.subheader("Full Report")
    st.text(ai.get("full_report", ""))

    st.download_button(
        "Download JSON",
        data=json.dumps(result, ensure_ascii=False, indent=2),
        file_name="pronunciation_report.json",
        mime="application/json",
    )


def build_endpoint_and_data(base, mode):
    base = base.rstrip("/")
    if mode == "Reading":
        endpoint = f"{base}/analyze"
        return endpoint, {
            "reference_text": reference_text,
            "language": language,
            "enable_miscue": "true" if enable_miscue else "false",
            "enable_prosody": "true" if enable_prosody else "false",
        }

    endpoint = f"{base}/analyze-gaming"
    return endpoint, {
        "game_prompt": game_prompt,
        "language": language,
        "enable_prosody": "true" if enable_prosody else "false",
    }


analyze_btn = st.button(analyze_label)

if analyze_btn:
    if not uploaded:
        st.warning("Please upload an audio file.")
    else:
        endpoint, data = build_endpoint_and_data(api_base, mode)

        if mode == "Reading" and not reference_text.strip():
            st.warning("Reference text required for Reading mode.")
            st.stop()
        if mode == "Gaming" and not game_prompt.strip():
            st.warning("Game prompt required for Gaming mode.")
            st.stop()

        with st.spinner("Analyzing..."):
            try:
                resp = call_api(endpoint, uploaded.getvalue(), uploaded.name or "audio.wav", data)
            except requests.RequestException as exc:
                st.error(f"Network error: {exc}")
            else:
                if resp.status_code != 200:
                    st.error(f"API request failed: {resp.status_code}")
                    try:
                        st.code(resp.text, language="json")
                    except Exception:
                        st.write(resp.text)
                else:
                    try:
                        result = resp.json()
                    except ValueError:
                        st.error("API returned invalid JSON.")
                        st.code(resp.text)
                    else:
                        render_result(result)