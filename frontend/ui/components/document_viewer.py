import time
import streamlit as st
from aiproviders import OllamaService
import requests

class DocumentViewer:
    def __init__(self, ollama_service: OllamaService):
        self.ollama_service = ollama_service

    def display_text_and_summary(self, col1, col2):
        """
        Display the document text and generate/display its summary.
        Shows the original text in one column and its summary in another,
        handling token estimation and summary generation.
        """
        with col1:
            if st.session_state.processor.token_count is None and st.session_state.processor.document_text:
                estimated_tokens = self.ollama_service._estimate_tokens(
                    st.session_state.processor.document_text
                )
                st.session_state.processor.token_count = estimated_tokens

            with st.expander("Extracted Text" + (
                f" (Estimated tokens: {st.session_state.processor.token_count:,})"
                if st.session_state.processor.token_count is not None else ""
            ), expanded=True):
                if st.session_state.extracting_text:
                    st.info("Azure Document Intelligence is extracting content...")
                else:
                    st.text_area(
                        "",
                        st.session_state.processor.document_text,
                        height=300,
                        key="extracted_text"
                    )

        with col2:
            with st.expander("Summary", expanded=True):
                if not st.session_state.processor.summary and not st.session_state.summary_in_progress:
                    text_area_placeholder = st.empty()
                    with st.spinner("Azure Text Analytics Summary is running..."):
                        st.session_state.summary_in_progress = True
                        full_response = ""

                        try:
                            text_content = st.session_state.processor.document_text
                            text_summary = requests.post("http://localhost:8000/summarize/", json={"content": text_content})
                            response = str(text_summary.json()["summary"])

                            for response in response.split():
                                full_response += response + " "
                                text_area_placeholder.text_area(
                                    "",
                                    value=full_response,
                                    height=300,
                                    key=f"summary_stream_{st.session_state.update_counter}"
                                )
                                st.session_state.update_counter += 1
                                time.sleep(0.05)

                            st.session_state.processor.summary = full_response
                        finally:
                            st.session_state.summary_in_progress = False
                else:
                    st.text_area(
                        "",
                        value=st.session_state.processor.summary or "",
                        height=300,
                        key="summary_display"
                    )

                if st.session_state.processor.summary:
                    if st.button("Regenerate Summary"):
                        st.session_state.processor.summary = None
                        st.session_state.summary_in_progress = False
                        st.rerun()
                    st.download_button(
                        label="Download Summary",
                        data=st.session_state.processor.summary,
                        file_name="summary.txt",
                        mime="text/plain"
                    )