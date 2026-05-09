import io
import json

import pandas as pd
import requests
import streamlit as st

DEFAULT_API = "http://127.0.0.1:8000/analyze"

st.set_page_config(page_title="Pronunciation Analysis", layout="wide")
st.title("Pronunciation Analysis Dashboard")

api_url = st.sidebar.text_input("API URL", DEFAULT_API)
uploaded = st.file_uploader(
    "Upload learner audio",
    type=["wav", "mp3", "m4a", "flac", "ogg"],
)
reference_text = st.text_area("Reference text", height=140)
analyze_btn = st.button("Analyze")


def call_api(api_url: str, file_bytes: bytes, filename: str, reference_text: str):
    file_obj = io.BytesIO(file_bytes)
    files = {"file": (filename, file_obj, "audio/wav")}
    data = {"reference_text": reference_text}
    response = requests.post(api_url, files=files, data=data, timeout=120)
    return response


def render_result(result: dict):
    azure = result.get("azure_result", {})
    ai = result.get("ai_report", {})

    st.subheader("Azure Metrics")
    metric_cols = st.columns(5)
    metric_cols[0].metric("Overall", f"{azure.get('overall_score', 0):.1f}")
    metric_cols[1].metric("Accuracy", f"{azure.get('accuracy_score', 0):.1f}")
    metric_cols[2].metric("Fluency", f"{azure.get('fluency_score', 0):.1f}")
    metric_cols[3].metric("Completeness", f"{azure.get('completeness_score', 0):.1f}")

    prosody = azure.get("prosody_score")
    if prosody is not None:
        metric_cols[4].metric("Prosody", f"{float(prosody):.1f}")
    else:
        metric_cols[4].metric("Prosody", "N/A")

    st.subheader("Word-level Details")
    word_details = azure.get("word_details", [])
    if word_details:
        df = pd.DataFrame(word_details)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.write("No word-level details available.")

    st.subheader("AI-generated Report")
    st.markdown("**Summary**")
    st.write(ai.get("summary", ""))

    st.markdown("**Strengths**")
    for item in ai.get("strengths", []):
        st.write(f"- {item}")

    st.markdown("**Weaknesses**")
    for item in ai.get("weaknesses", []):
        st.write(f"- {item}")

    st.markdown("**Recommendations**")
    for item in ai.get("recommendations", []):
        st.write(f"- {item}")

    st.subheader("Full Report")
    st.text(ai.get("full_report", ""))

    st.download_button(
        "Download JSON",
        data=json.dumps(result, ensure_ascii=False, indent=2),
        file_name="pronunciation_report.json",
        mime="application/json",
    )


if analyze_btn:
    if not uploaded:
        st.warning("Please upload an audio file.")
    elif not reference_text.strip():
        st.warning("Please enter the reference text.")
    else:
        with st.spinner("Analyzing..."):
            try:
                response = call_api(
                    api_url,
                    uploaded.getvalue(),
                    uploaded.name or "audio.wav",
                    reference_text,
                )
            except requests.RequestException as exc:
                st.error(f"Network error: {exc}")
            else:
                if response.status_code != 200:
                    st.error(f"API request failed: {response.status_code}")
                    st.code(response.text, language="json")
                else:
                    try:
                        result = response.json()
                    except ValueError:
                        st.error("API returned invalid JSON.")
                        st.code(response.text)
                    else:
                        render_result(result)