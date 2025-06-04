# src/ui_components.py
"""
ui_components.py
Streamlit UI helpers with improved recording flow, real-time ASR, and ASR model comparison
"""

from __future__ import annotations
import asyncio, io, json, time, wave, queue
from pathlib import Path
from typing import Tuple, Optional, List, Dict, Any

import numpy as np
import streamlit as st
# import librosa # Not currently used, can be removed if not planned

from .config import config, logger 
from .utils import sanitize_input
from .transcription import transcribe_audio
from .diarization import generate_gpt_speaker_tags, apply_speaker_diarization
from .llm_integration import generate_note, clean_transcription
from .encryption import secure_audio_processing
from .prompts import load_prompt_templates, save_custom_template
from .audio_processing import (
    live_vosk_callback,
    live_whisper_callback,
    format_transcript_with_confidence,
    format_elapsed_time,
    live_azure_callback
)
from .token_management import generate_coding_and_review

# Helper function to safely get values from config, then default
def get_config_value(config_key: str, default_value: str = "") -> str:
    return str(config.get(config_key, default_value))


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar configuration
# ─────────────────────────────────────────────────────────────────────────────
def render_sidebar() -> Tuple[
    Optional[str], Optional[str], Optional[str], Optional[str],
    str, bool, str, bool, Optional[str]
]:
    with st.sidebar:
        st.header("⚙️ Configuration")

        st.subheader("Azure OpenAI (LLM)")
        azure_openai_api_key_llm = st.text_input(
            "Azure OpenAI API Key (for LLM)",
            value=get_config_value("AZURE_API_KEY"), 
            type="password",
            key="sidebar_azure_openai_api_key_llm"
        )
        azure_openai_endpoint_llm = st.text_input(
            "Azure OpenAI Endpoint (for LLM)",
            value=get_config_value("AZURE_ENDPOINT"), 
            key="sidebar_azure_openai_endpoint_llm"
        )
        azure_openai_api_version_llm = get_config_value("API_VERSION", "2024-02-15-preview")
        azure_openai_model_name_llm = get_config_value("MODEL_NAME", "gpt-4o")


        st.subheader("Speech Recognition (ASR)")
        asr_engine_choice = st.selectbox(
            "ASR Engine",
            ["Vosk", "Whisper", "Azure Speech", "Azure Whisper (OpenAI SDK)"]
        )
        
        primary_service_key_to_return = azure_openai_api_key_llm
        primary_service_endpoint_to_return = azure_openai_endpoint_llm
        asr_model_info_to_return = ""
        language_to_return = "en-US" 

        if asr_engine_choice == "Vosk":
            mdir = Path(get_config_value("MODEL_DIR")) 
            opts = [d.name for d in mdir.iterdir() if d.is_dir()] if mdir.exists() else []
            default_vosk_model_name = "vosk-model-small-en-us-0.15"
            if not opts or default_vosk_model_name not in opts:
                if not (mdir / default_vosk_model_name).exists():
                     st.info(f"Default Vosk model '{default_vosk_model_name}' can be auto-downloaded if selected.")
                if default_vosk_model_name not in opts:
                    opts.insert(0, default_vosk_model_name)

            selected_vosk_model_name = st.selectbox("Vosk Model", opts, index=opts.index(default_vosk_model_name) if default_vosk_model_name in opts else 0)
            if selected_vosk_model_name == default_vosk_model_name:
                asr_model_info_to_return = "vosk_small" 
            else:
                asr_model_info_to_return = str(mdir / selected_vosk_model_name)
        
        elif asr_engine_choice == "Whisper":
            size = st.selectbox("Whisper Size", ["tiny", "base", "small", "medium", "large"])
            asr_model_info_to_return = f"whisper:{size}"
        
        elif asr_engine_choice == "Azure Speech":
            asr_model_info_to_return = "azure_speech"
            st.subheader("Azure Speech Service (ASR)")
            azure_speech_api_key_asr = st.text_input(
                "Azure Speech API Key (for ASR)",
                value=get_config_value("AZURE_SPEECH_API_KEY"), 
                type="password",
                key="sidebar_azure_speech_api_key_asr"
            )
            azure_speech_endpoint_asr = st.text_input(
                "Azure Speech Endpoint (for ASR)",
                value=get_config_value("AZURE_SPEECH_ENDPOINT"), 
                key="sidebar_azure_speech_endpoint_asr"
            )
            primary_service_key_to_return = azure_speech_api_key_asr
            primary_service_endpoint_to_return = azure_speech_endpoint_asr
            if not primary_service_key_to_return or not primary_service_endpoint_to_return:
                 st.warning("⚠️ Azure Speech (ASR) requires its own API Key and Endpoint.")
            language_to_return = st.selectbox(
                "Language (for Azure Speech ASR)",
                ["en-US", "es-ES", "fr-FR", "de-DE", "zh-CN"], index=0, key="azure_speech_language"
            )

        elif asr_engine_choice == "Azure Whisper (OpenAI SDK)":
            asr_model_info_to_return = "azure_whisper"
            if not azure_openai_api_key_llm or not azure_openai_endpoint_llm:
                st.warning("⚠️ Azure Whisper (OpenAI SDK) uses the Azure OpenAI LLM credentials. Please provide them above.")
            language_to_return = st.selectbox(
                "Language (for Azure Whisper ASR)",
                ["en", "es", "fr", "de", "zh", "auto"], index=0, key="azure_whisper_language" 
            )


        st.subheader("Note Generation LLM Source")
        note_model_source = st.selectbox(
            "LLM for Notes", 
            ["Azure OpenAI", "Local LLM Model"] 
        )
        use_local_llm_for_notes = note_model_source.startswith("Local")
        local_llm_model_name_for_notes = ""
        if use_local_llm_for_notes:
            models_dir = Path(get_config_value("LOCAL_MODELS_DIR")) 
            opts = [d.name for d in models_dir.iterdir() if d.is_dir()] if models_dir.exists() else []
            if opts:
                local_llm_model_name_for_notes = st.selectbox("Local LLM Model (for Notes)", opts, key="local_llm_note_choice")
            else:
                st.warning("No local LLM models found. Place models in 'local_llm_models' directory.")
        
        if not use_local_llm_for_notes and (not azure_openai_api_key_llm or not azure_openai_endpoint_llm) :
            st.warning("⚠️ Azure OpenAI selected for notes, but API Key/Endpoint for LLM is missing above.")


        st.subheader("Security")
        use_encryption = st.checkbox("Encrypt recordings on save", value=True)

        # Token Management Approach for handling large transcripts        st.subheader("Advanced Settings")
        with st.expander("Token Management Settings", expanded=True):
            st.markdown("##### 🔄 Token Management Strategy")
            st.markdown("For handling long transcripts that exceed OpenAI's token limits")
            
            token_management_approach = st.radio(
                "Select Strategy",
                ["Chunking", "Two-Stage Summarization"],
                index=0 if config.get("TOKEN_MANAGEMENT_APPROACH") == "chunking" else 1,
                help="Choose how to handle long transcripts that exceed token limits:\n\n"
                     "• **Chunking**: Divides transcript into parts, processes each, then combines results\n\n"
                     "• **Two-Stage Summarization**: Extracts key information first, then generates final note from summaries"
            )
            
            # Update the config directly for immediate effect
            if token_management_approach == "Chunking":
                config["TOKEN_MANAGEMENT_APPROACH"] = "chunking"
                st.success("✅ Using **Chunking** approach")
            else:
                config["TOKEN_MANAGEMENT_APPROACH"] = "two_stage"
                st.success("✅ Using **Two-Stage Summarization** approach")

        return (
            primary_service_key_to_return,
            primary_service_endpoint_to_return,
            azure_openai_api_version_llm,
            azure_openai_model_name_llm,
            asr_model_info_to_return,
            use_local_llm_for_notes,
            local_llm_model_name_for_notes,
            use_encryption,
            language_to_return
        )

# ─────────────────────────────────────────────────────────────────────────────
# Patient Data Section
# ─────────────────────────────────────────────────────────────────────────────

def render_patient_data_section(prefix: str) -> dict:
    with st.expander("📋 Patient Information", expanded=False):
        st.session_state.setdefault(
            f"patient_{prefix}", {"name": "", "ehr": "", "consent": False}
        )
        pd = st.session_state[f"patient_{prefix}"]
        pd["name"] = st.text_input(
            "Patient Name",
            pd["name"],
            key=f"{prefix}_p_name"
        )
        pd["ehr"] = st.text_area(
            "Patient EHR Data",
            pd["ehr"],
            key=f"{prefix}_p_ehr"
        )
        
        consent_text = "The patient was informed of the presence of a listening and transcribing tool during the visit and given the option to opt out and agreed to proceed."
        pd["consent"] = st.checkbox(
            consent_text,
            value=pd.get("consent", False),
            key=f"{prefix}_consent"
        )
        
        if pd["consent"]:
            st.success("✅ Patient consent recorded")
        else:
            st.warning("⚠️ Patient consent required before recording/processing")
    
    return pd

# ─────────────────────────────────────────────────────────────────────────────
# Template Section
# ─────────────────────────────────────────────────────────────────────────────

def render_template_section(prefix: str) -> str:
    st.subheader("📝 Note Template")
    tmpl_store = load_prompt_templates()
    options = ["✨ Create New Template"] + list(tmpl_store.keys())
    current_selection = st.session_state.get(f"{prefix}_tmpl_choice", "✨ Create New Template")
    if current_selection not in options:
        current_selection = "✨ Create New Template"

    choice = st.selectbox(
        "Template",
        options,
        index=options.index(current_selection),
        key=f"{prefix}_tmpl_choice"
    )
    template_text_key = f"{prefix}_tmpl_text"

    if choice == "✨ Create New Template":
        txt = st.text_area(
            "Template Instructions",
            st.session_state.get(template_text_key, ""),
            key=template_text_key,
            height=180
        )
        name = st.text_input(
            "Save as",
            key=f"{prefix}_tmpl_name"
        )
        if st.button(
            "Save Template",
            key=f"{prefix}_tmpl_save"
        ) and name and txt:
            save_custom_template(name, txt)
            st.success(f"Template '{name}' saved.")
            st.session_state[f"{prefix}_tmpl_choice"] = name
            st.rerun()
        final_template_text = txt
    else:
        selected_template_content = tmpl_store.get(choice, "")
        txt = st.text_area(
            "Template Instructions",
            selected_template_content,
            key=template_text_key,
            height=180
        )
        final_template_text = txt

    return final_template_text

# ─────────────────────────────────────────────────────────────────────────────
# Real-time ASR with enhanced visualization
# ─────────────────────────────────────────────────────────────────────────────

def render_realtime_asr(
    asr_service_key: Optional[str], asr_service_endpoint: Optional[str], 
    openai_api_version_llm: Optional[str], openai_model_name_llm: Optional[str], 
    asr_info: str, 
    use_local_llm_for_notes: bool, local_llm_model_name_for_notes: str, 
    patient: dict, template: str, use_encryption: bool,
    language: Optional[str],
    consent_given: bool = False
):
    from .recorder import StreamRecorder
    from .audio_processing import live_vosk_callback, live_whisper_callback, live_azure_callback # live_azure_callback needs Azure Speech credentials
    import time

    st.write("### Real-time Transcription")
    if asr_info == "azure_speech":
        st.caption("Note: Live Azure Speech processes audio in segments. For highest accuracy with Azure Speech, use the 'Traditional Recording' option for full file processing.")


    status_placeholder = st.empty()
    transcript_placeholder = st.empty()
    control_container = st.container()
    processing_results_container = st.container()

    if "realtime_recording" not in st.session_state:
        st.session_state.realtime_recording = False; st.session_state.realtime_recorder = None
        st.session_state.transcript_history = ""; st.session_state.recording_start_time = 0
        st.session_state.update_queue = None; st.session_state.last_partial = ""
        st.session_state.last_words_info = []; st.session_state.current_transcript = ""
        st.session_state.last_recorded_path = None

    is_local_whisper = asr_info.startswith("whisper:")
    is_azure_speech = asr_info == "azure_speech"
    is_azure_whisper_sdk = asr_info == "azure_whisper"
    is_vosk = not (is_local_whisper or is_azure_speech or is_azure_whisper_sdk)


    if is_local_whisper: st.info(f"Using Local Whisper model: {asr_info.split(':', 1)[1]}")
    elif is_azure_speech:
        st.info(f"Using Azure Speech Service (Language: {language or 'Not set'})")
        if not asr_service_key or not asr_service_endpoint:
            st.error("Azure Speech (ASR) requires API key and endpoint."); return
    elif is_azure_whisper_sdk:
        st.info(f"Using Azure Whisper via OpenAI SDK (Language: {language or 'Not set'})")
        if not asr_service_key or not asr_service_endpoint: 
            st.error("Azure Whisper (OpenAI SDK) requires Azure OpenAI LLM credentials."); return
    elif is_vosk:
        vosk_display_name = Path(asr_info).name if Path(asr_info).is_dir() and asr_info != "vosk_small" else "Default Small (vosk_small)"
        st.info(f"Using Vosk model: {vosk_display_name}")


    if not consent_given: st.error("⚠️ Recording is disabled until patient consent is documented.")

    with control_container:
        col1, col2, col3 = st.columns(3)
        if col1.button("▶ Start Transcription", disabled=st.session_state.realtime_recording or not consent_given, key="start_asr_btn_rt"): # Added suffix
            st.session_state.realtime_recording = True; st.session_state.recording_start_time = time.time()
            st.session_state.transcript_history = ""; st.session_state.last_partial = ""; st.session_state.last_words_info = []
            st.session_state.current_transcript = ""; st.session_state.last_recorded_path = None
            q = queue.Queue(); st.session_state.update_queue = q
            try:
                callback_fn = None
                if is_local_whisper: callback_fn = live_whisper_callback(asr_info.split(":", 1)[1], q)
                elif is_azure_speech:
                    # live_azure_callback is passed asr_service_key and asr_service_endpoint, which are Speech credentials
                    callback_fn = live_azure_callback(asr_service_key, asr_service_endpoint, q) 
                elif is_azure_whisper_sdk:
                    st.error("Live transcription for Azure Whisper (OpenAI SDK) is not supported by available callbacks. Use Traditional Recording.")
                    st.session_state.realtime_recording = False; st.stop()
                elif is_vosk:
                    vosk_path_to_use = str(config["MODEL_DIR"] / "vosk-model-small-en-us-0.15") if asr_info == "vosk_small" else asr_info
                    if not Path(vosk_path_to_use).exists() and asr_info != "vosk_small":
                        st.error(f"Vosk model not found at {vosk_path_to_use}. Real-time will fail."); st.stop()
                    callback_fn = live_vosk_callback(vosk_path_to_use, q)
                
                if callback_fn:
                    recorder = StreamRecorder(on_chunk=callback_fn)
                    recorder.start(); st.session_state.realtime_recorder = recorder; st.rerun()
            except Exception as e:
                logger.error(f"Failed to start StreamRecorder: {e}", exc_info=True)
                st.error(f"Error starting audio recording: {e}. Check mic permissions."); st.session_state.realtime_recording = False

        is_paused = st.session_state.realtime_recorder._paused if st.session_state.realtime_recording and st.session_state.realtime_recorder else False
        if col2.button("⏸ Pause" if not is_paused else "▶ Resume", disabled=not st.session_state.realtime_recording, key="pause_asr_btn_rt"): # Added suffix
            if st.session_state.realtime_recorder:
                if is_paused: st.session_state.realtime_recorder.resume()
                else: st.session_state.realtime_recorder.pause()
                st.rerun()
        
        if col3.button("■ Stop Transcription", disabled=not st.session_state.realtime_recording, key="stop_asr_btn_rt"): # Added suffix
            if st.session_state.realtime_recorder:
                try:
                    wav_path_obj = st.session_state.realtime_recorder.stop()
                    st.session_state.last_recorded_path = str(wav_path_obj)
                    st.session_state.current_transcript = st.session_state.get("transcript_history", "") 
                    while st.session_state.update_queue and not st.session_state.update_queue.empty(): 
                        try: update_data = st.session_state.update_queue.get_nowait(); st.session_state.current_transcript = update_data.get("text", st.session_state.current_transcript)
                        except queue.Empty: break
                    logger.info(f"Real-time stopped. Final transcript len: {len(st.session_state.current_transcript)}")
                    st.session_state.realtime_recording = False; st.session_state.realtime_recorder = None; st.session_state.update_queue = None
                    st.success(f"Recording saved: {wav_path_obj.name}"); st.session_state.just_stopped_realtime = True; st.rerun()
                except Exception as e:
                    logger.error(f"Error stopping recorder: {e}", exc_info=True); st.error(f"Stop error: {e}")
                    st.session_state.realtime_recording = False; st.session_state.realtime_recorder = None; st.session_state.update_queue = None

    current_elapsed_time = "00:00"; status_message = "⚪ **IDLE**"
    if st.session_state.realtime_recording:
        current_elapsed_time = format_elapsed_time(st.session_state.recording_start_time)
        status_message = "🔴 **RECORDING**" if not is_paused else "⏸️ **PAUSED**"
        if st.session_state.update_queue: 
            while not st.session_state.update_queue.empty():
                try:
                    update = st.session_state.update_queue.get_nowait()
                    st.session_state.transcript_history = update["text"]; st.session_state.last_partial = update["partial"]
                    st.session_state.last_words_info = update.get("words_info", []); current_elapsed_time = update["elapsed"]
                except queue.Empty: break
                except Exception as e: logger.debug(f"Queue processing error: {e}") 
    
    with status_placeholder.container():
        st.markdown(f"{status_message}: {current_elapsed_time}")
        if st.session_state.realtime_recording and not is_paused:
            st.markdown(f"""<div style="padding:10px;border-radius:5px;background-color:rgba(255,0,0,0.1);border-left:5px solid red;animation:pulse 1.5s infinite;"><span style="color:red;font-weight:bold;">●</span> RECORDING IN PROGRESS - {current_elapsed_time}</div><style>@keyframes pulse{{0%{{opacity:1;}}50%{{opacity:0.5;}}100%{{opacity:1;}}}}</style>""", unsafe_allow_html=True)

    with transcript_placeholder.container():
        # Add a border and padding to the transcript display for better visual separation
        transcript_display_style = "min-height:100px; padding: 10px; border-radius: 5px;"
        formatted_html = format_transcript_with_confidence(st.session_state.transcript_history, st.session_state.last_partial, st.session_state.last_words_info)
        st.markdown("#### Live Transcript:")
        st.markdown(f'<div style="{transcript_display_style}">{formatted_html if formatted_html else "_(Waiting for speech...)_"}</div>', unsafe_allow_html=True)


    if st.session_state.realtime_recording:
        # Throttle the rerun frequency to reduce flickering.
        # A value around 0.1s to 0.25s (4-10 FPS) is usually a good balance.
        time.sleep(0.2)  # Sleep for 200 milliseconds (previously 0.15)
        try:
            st.experimental_rerun()
        except AttributeError:
            # The time.sleep() is now handled before the try-except block
            st.rerun()


    if st.session_state.pop("just_stopped_realtime", False):
        transcript = st.session_state.get("current_transcript", "")
        wav_file_path = st.session_state.get("last_recorded_path")

        if not transcript and wav_file_path and Path(wav_file_path).exists(): 
            with st.spinner("No live transcript. Transcribing saved audio..."):
                openai_llm_key_config = get_config_value("AZURE_API_KEY")
                openai_llm_endpoint_config = get_config_value("AZURE_ENDPOINT")

                if is_azure_speech:
                    transcript = transcribe_audio(wav_file_path, "azure_speech", azure_key=asr_service_key, azure_endpoint=asr_service_endpoint, openai_key=openai_llm_key_config, openai_endpoint=openai_llm_endpoint_config, language=language, return_raw=True) # Request raw for fallback
                elif is_local_whisper: transcript = transcribe_audio(wav_file_path, asr_info)
                elif is_azure_whisper_sdk:
                    transcript = transcribe_audio(wav_file_path, "azure_whisper", openai_key=asr_service_key, openai_endpoint=asr_service_endpoint, language=language)
                elif is_vosk:
                    vosk_model_path = str(config["MODEL_DIR"] / "vosk-model-small-en-us-0.15") if asr_info == "vosk_small" else asr_info
                    transcript = transcribe_audio(wav_file_path, "vosk_model", model_path=vosk_model_path)
                if transcript and not transcript.startswith("ERROR:"): st.success("Fallback transcription complete.")
                else: st.warning(f"Fallback transcription failed or empty: {transcript}")
        
        if transcript and not transcript.startswith("ERROR:"):
            with processing_results_container:
                st.subheader("Processing Final Transcript..."); st.text_area("Final Transcript", transcript, height=180, key="asr_final_display_rt_key") # Suffix key
                llm_key_for_llm_tasks = get_config_value("AZURE_API_KEY")
                llm_endpoint_for_llm_tasks = get_config_value("AZURE_ENDPOINT")

                if (llm_key_for_llm_tasks and llm_endpoint_for_llm_tasks and not use_local_llm_for_notes) or use_local_llm_for_notes:
                    with st.spinner("Cleaning..."):
                        cleaned = asyncio.run(clean_transcription(transcript, llm_key_for_llm_tasks, llm_endpoint_for_llm_tasks, openai_api_version_llm, openai_model_name_llm, use_local=use_local_llm_for_notes, local_model=local_llm_model_name_for_notes))
                    st.subheader("Cleaned"); st.text_area("", cleaned, height=180, key="rt_cleaned_text_key") # Suffix key
                    with st.spinner("Diarizing..."):
                        diarized = asyncio.run(generate_gpt_speaker_tags(cleaned, llm_key_for_llm_tasks, llm_endpoint_for_llm_tasks, openai_api_version_llm, openai_model_name_llm))
                    st.subheader("Diarized"); st.text_area("", diarized, height=180, key="rt_diarized_text_key") # Suffix key
                    if template:
                        with st.spinner("Generating note..."):
                            note = asyncio.run(generate_note(diarized, llm_key_for_llm_tasks, llm_endpoint_for_llm_tasks, openai_api_version_llm, openai_model_name_llm, template, use_local_llm_for_notes, local_llm_model_name_for_notes, patient))
                        st.subheader("Generated Note"); st.text_area("", note, height=240, key="rt_note_text_key") # Suffix key
                        
                        # --- Coding and Payer Review Section ---
                        with st.spinner("Generating coding and payer review..."):
                            coding_review = generate_coding_and_review(
                                note,
                                azure_endpoint=llm_endpoint_for_llm_tasks,
                                azure_api_key=llm_key_for_llm_tasks,
                                deployment_name=openai_model_name_llm,
                                api_version=openai_api_version_llm
                            )
                        st.subheader("Coding & Payer Review")
                        st.text_area("E/M, ICD-10, SNOMED, CPT, Risk, SDOH, Alternate Dx, Payer Review", coding_review, height=350, key="rt_coding_review_text_key")
                else: 
                    st.warning("LLM credentials (Azure OpenAI or Local) not configured for advanced processing. Basic diarization only.")
                    st.text_area("Basic Diarized", apply_speaker_diarization(transcript), height=180, key="rt_basic_diar_text_key") # Suffix key
                if use_encryption and wav_file_path and Path(wav_file_path).exists():
                    with st.spinner("Encrypting audio file..."): 
                        with secure_audio_processing(wav_file_path, True): 
                            st.success(f"Audio file {Path(wav_file_path).name} encrypted.")
        else: st.warning(f"No valid transcript captured or generated. Processing skipped. Content: '{transcript}'")


# ─────────────────────────────────────────────────────────────────────────────
# Recording Flow: Start, Pause, Stop → Pipeline Results (Traditional)
# ─────────────────────────────────────────────────────────────────────────────
def render_recording_section(
    asr_service_key: Optional[str], asr_service_endpoint: Optional[str], 
    openai_api_version_llm: Optional[str], openai_model_name_llm: Optional[str], 
    asr_info: str, 
    use_local_llm_for_notes: bool, local_llm_model_name_for_notes: str, 
    use_encryption: bool,
    language: Optional[str]
):
    st.subheader("🎙️ Record & Generate Note")
    
    consent_container = st.container(border=True)
    with consent_container:
        st.markdown("### 📝 Patient Consent Documentation"); patient = render_patient_data_section("rec")
        has_consent = patient.get("consent", False)
        if has_consent: st.success("✅ **CONSENT RECORDED**")
        else:
            st.warning("⚠️ **CONSENT REQUIRED**")
            if st.button("📝 DOCUMENT PATIENT CONSENT", use_container_width=True, type="primary", key="trad_rec_consent_btn_key_main"): # Unique key
                patient["consent"] = True; st.session_state[f"patient_rec"]["consent"] = True; st.rerun()
    
    template = render_template_section("rec")
    if not has_consent: st.error("⚠️ Patient consent is required to proceed."); return 

    asr_mode = st.radio("Transcription Mode", ["Traditional Recording", "Real-time ASR"], index=0, key="asr_mode_sel_trad_key_main") # Unique key
    
    llm_key_for_llm_tasks = get_config_value("AZURE_API_KEY")
    llm_endpoint_for_llm_tasks = get_config_value("AZURE_ENDPOINT")
    if not llm_key_for_llm_tasks and not use_local_llm_for_notes:
        st.info("ℹ️ **Note**: Advanced processing (cleaning, notes) requires Azure OpenAI API key or local LLM configuration.")

    if asr_mode == "Real-time ASR" and asr_info:
        render_realtime_asr(
            asr_service_key, asr_service_endpoint, 
            openai_api_version_llm, openai_model_name_llm, 
            asr_info, use_local_llm_for_notes, local_llm_model_name_for_notes,
            patient, template, use_encryption, language, consent_given=has_consent
        )
    else:
        from .recorder import StreamRecorder
        rec_instance = st.session_state.get("traditional_recorder")
        
        # --- Visual Feedback for Traditional Recording ---
        traditional_status_placeholder = st.empty()

        if rec_instance and "traditional_recording_start_time" in st.session_state:
            is_trad_paused = rec_instance._paused
            current_trad_elapsed_time = format_elapsed_time(st.session_state.traditional_recording_start_time)
            trad_status_message = "🔴 **RECORDING**" if not is_trad_paused else "⏸️ **PAUSED**"
            
            with traditional_status_placeholder.container():
                st.markdown(f"{trad_status_message}: {current_trad_elapsed_time}")
                if not is_trad_paused: # Show pulse animation only when actively recording
                    st.markdown(f"""<div style="padding:10px;border-radius:5px;background-color:rgba(255,0,0,0.1);border-left:5px solid red;animation:pulse 1.5s infinite;"><span style="color:red;font-weight:bold;">●</span> RECORDING IN PROGRESS - {current_trad_elapsed_time}</div><style>@keyframes pulse{{0%{{opacity:1;}}50%{{opacity:0.5;}}100%{{opacity:1;}}}}</style>""", unsafe_allow_html=True)
        else:
            with traditional_status_placeholder.container():
                st.markdown("⚪ **IDLE**: Press Start Recording to begin.")
        # --- End Visual Feedback ---

        col1, col2, col3 = st.columns(3)
        if col1.button("▶ Start Recording", disabled=(rec_instance is not None) or not has_consent, key="start_trad_btn_key_main"): # Unique key
            if "last_wav_traditional" in st.session_state: del st.session_state["last_wav_traditional"]
            st.session_state.traditional_recording_start_time = time.time() # Set start time
            st.session_state.traditional_results_placeholder = st.empty()
            recorder = StreamRecorder(); recorder.start(); st.session_state["traditional_recorder"] = recorder; st.rerun()

        is_rec = rec_instance is not None and not rec_instance._paused
        if col2.button("⏸ Pause" if is_rec else "▶ Resume", disabled=(rec_instance is None), key="pause_trad_btn_key_main"): # Unique key
            if rec_instance: 
                if is_rec: rec_instance.pause()
                else: rec_instance.resume()
                st.rerun()

        if col3.button("■ Stop Recording", disabled=(rec_instance is None), key="stop_trad_btn_key_main"): # Unique key
            recorder = st.session_state.pop("traditional_recorder", None)
            st.session_state.pop("traditional_recording_start_time", None) # Clean up start time
            if recorder:
                try: wav_obj = recorder.stop(); st.session_state["last_wav_traditional"] = str(wav_obj); st.success(f"Saved: {wav_obj.name}"); st.rerun()
                except Exception as e: logger.error(f"Trad stop error: {e}", exc_info=True); st.error(f"Stop error: {e}")
        
        # Add a rerun loop for the timer if traditional recording is active and not paused
        if rec_instance and not rec_instance._paused:
            time.sleep(0.8)  # Update about once per second, less frequent than ASR updates
            try:
                st.experimental_rerun()
            except AttributeError:
                st.rerun()
        
        if "traditional_results_placeholder" not in st.session_state: st.session_state.traditional_results_placeholder = st.empty()
        if "last_wav_traditional" in st.session_state:
            wav_path = st.session_state.pop("last_wav_traditional")
            with st.session_state.traditional_results_placeholder.container():
                raw = ""
                try:
                    with st.spinner("Transcribing..."):
                        if asr_info == "azure_speech":
                            raw = transcribe_audio(wav_path, "azure_speech", azure_key=asr_service_key, azure_endpoint=asr_service_endpoint, openai_key=llm_key_for_llm_tasks, openai_endpoint=llm_endpoint_for_llm_tasks, language=language, return_raw=True)
                        elif asr_info == "azure_whisper":
                            raw = transcribe_audio(wav_path, "azure_whisper", openai_key=asr_service_key, openai_endpoint=asr_service_endpoint, language=language)
                        elif asr_info.startswith("whisper:"): raw = transcribe_audio(wav_path, asr_info)
                        else:
                            vosk_model_path = str(config["MODEL_DIR"] / "vosk-model-small-en-us-0.15") if asr_info == "vosk_small" else asr_info
                            raw = transcribe_audio(wav_path, "vosk_model", model_path=vosk_model_path)
                    if raw.startswith("ERROR:"): st.error(f"Transcription failed: {raw}")
                    else:
                        st.subheader("Raw Transcript"); st.text_area("", raw, height=180, key="trad_raw_txt_key_main")
                        if (llm_key_for_llm_tasks and llm_endpoint_for_llm_tasks and not use_local_llm_for_notes) or use_local_llm_for_notes:
                            with st.spinner("Cleaning..."): cleaned = asyncio.run(clean_transcription(raw, llm_key_for_llm_tasks, llm_endpoint_for_llm_tasks, openai_api_version_llm, openai_model_name_llm, use_local_llm_for_notes, local_llm_model_name_for_notes))
                            st.subheader("Cleaned"); st.text_area("", cleaned, height=180, key="trad_cleaned_txt_key_main")
                            with st.spinner("Diarizing..."): diarized = asyncio.run(generate_gpt_speaker_tags(cleaned, llm_key_for_llm_tasks, llm_endpoint_for_llm_tasks, openai_api_version_llm, openai_model_name_llm))
                            st.subheader("Diarized"); st.text_area("", diarized, height=180, key="trad_diarized_txt_key_main")
                            if template:
                                with st.spinner("Generating note..."): note = asyncio.run(generate_note(diarized, llm_key_for_llm_tasks, llm_endpoint_for_llm_tasks, openai_api_version_llm, openai_model_name_llm, template, use_local_llm_for_notes, local_llm_model_name_for_notes, patient))
                                st.subheader("Generated Note"); st.text_area("", note, height=240, key="trad_note_txt_key_main")
                                # --- Coding and Payer Review Section ---
                                with st.spinner("Generating coding and payer review..."):
                                    coding_review = generate_coding_and_review(
                                        note,
                                        azure_endpoint=llm_endpoint_for_llm_tasks,
                                        azure_api_key=llm_key_for_llm_tasks,
                                        deployment_name=openai_model_name_llm,
                                        api_version=openai_api_version_llm
                                    )
                                st.subheader("Coding & Payer Review")
                                st.text_area("E/M, ICD-10, SNOMED, CPT, Risk, SDOH, Alternate Dx, Payer Review", coding_review, height=350, key="trad_coding_review_txt_key_main")
                        else:
                            st.warning("LLM credentials (Azure OpenAI or Local) not configured. Basic diarization only.")
                            st.text_area("Basic Diarized", apply_speaker_diarization(raw), height=180, key="trad_basic_diarized_key_main")
                except Exception as e: logger.error(f"Trad processing error: {e}", exc_info=True); st.error(f"Processing error: {e}")
                if use_encryption and Path(wav_path).exists():
                    with st.spinner("Encrypting audio file..."):
                        with secure_audio_processing(wav_path, True):
                            st.success(f"Audio file {Path(wav_path).name} encrypted.")


# ─────────────────────────────────────────────────────────────────────────────
# Upload Audio Section
# ─────────────────────────────────────────────────────────────────────────────
def render_upload_section(
    asr_service_key: Optional[str], asr_service_endpoint: Optional[str], 
    openai_api_version_llm: Optional[str], openai_model_name_llm: Optional[str], 
    asr_info: str, 
    use_local_llm_for_notes: bool, local_llm_model_name_for_notes: str, 
    use_encryption: bool = False,
    language: Optional[str] = "en-US"
):
    st.subheader("⬆️ Upload Audio & Generate Note")
    consent_container = st.container(border=True)
    with consent_container:
        st.markdown("### 📝 Patient Consent Documentation"); patient = render_patient_data_section("upload")
        has_consent = patient.get("consent", False)
        if has_consent: st.success("✅ **CONSENT RECORDED**")
        else:
            st.warning("⚠️ **CONSENT REQUIRED**")
            if st.button("📝 DOCUMENT PATIENT CONSENT", use_container_width=True, type="primary", key="upload_consent_btn_main_key_upload"): # Unique key
                patient["consent"] = True; st.session_state[f"patient_upload"]["consent"] = True; st.rerun()
    
    template = render_template_section("upload")
    if not has_consent: st.error("⚠️ Patient consent is required to proceed."); return

    llm_key_for_llm_tasks = get_config_value("AZURE_API_KEY")
    llm_endpoint_for_llm_tasks = get_config_value("AZURE_ENDPOINT")
    if not llm_key_for_llm_tasks and not use_local_llm_for_notes:
        st.info("ℹ️ **Note**: Advanced processing requires Azure OpenAI API key or local LLM.")

    uploaded_file = st.file_uploader("Choose WAV/MP3/M4A", type=["wav","mp3","m4a"], key="main_file_uploader_key_upload") # Unique key
    if not uploaded_file: return

    final_audio_path_str = ""
    try:
        with st.spinner("Saving & converting audio..."):
            temp_audio_dir = Path(get_config_value("CACHE_DIR")); temp_audio_dir.mkdir(parents=True, exist_ok=True)
            temp_audio_file = temp_audio_dir / uploaded_file.name
            temp_audio_file.write_bytes(uploaded_file.read()); final_audio_path_str = str(temp_audio_file)
            if temp_audio_file.suffix.lower() != ".wav":
                from .audio_processing import convert_to_wav
                final_audio_path_str = convert_to_wav(final_audio_path_str)
        
        raw_transcript_upload = ""
        with st.spinner("Transcribing..."):
            if asr_info == "azure_speech":
                raw_transcript_upload = transcribe_audio(final_audio_path_str, "azure_speech", azure_key=asr_service_key, azure_endpoint=asr_service_endpoint, openai_key=llm_key_for_llm_tasks, openai_endpoint=llm_endpoint_for_llm_tasks, language=language, return_raw=True) # Ensure raw for this step
            elif asr_info == "azure_whisper":
                raw_transcript_upload = transcribe_audio(final_audio_path_str, "azure_whisper", openai_key=asr_service_key, openai_endpoint=asr_service_endpoint, language=language)
            elif asr_info.startswith("whisper:"): raw_transcript_upload = transcribe_audio(final_audio_path_str, asr_info)
            else: 
                vosk_model_path = str(config["MODEL_DIR"] / "vosk-model-small-en-us-0.15") if asr_info == "vosk_small" else asr_info
                raw_transcript_upload = transcribe_audio(final_audio_path_str, "vosk_model", model_path=vosk_model_path)
        
        st.subheader("Raw Transcript"); st.text_area("", raw_transcript_upload, height=180, key="upload_raw_disp_key_upload") # Unique key
        if st.button("Process Transcript & Generate Note", disabled=not has_consent, key="upload_proc_btn_key_upload"): # Unique key
            if raw_transcript_upload.startswith("ERROR:"): st.error(f"Cannot process, error: {raw_transcript_upload}"); return
            if (llm_key_for_llm_tasks and llm_endpoint_for_llm_tasks and not use_local_llm_for_notes) or use_local_llm_for_notes:
                with st.spinner("Processing..."):
                    cleaned_up = asyncio.run(clean_transcription(raw_transcript_upload, llm_key_for_llm_tasks, llm_endpoint_for_llm_tasks, openai_api_version_llm, openai_model_name_llm, use_local_llm_for_notes, local_llm_model_name_for_notes))
                    diarized_up = asyncio.run(generate_gpt_speaker_tags(cleaned_up, llm_key_for_llm_tasks, llm_endpoint_for_llm_tasks, openai_api_version_llm, openai_model_name_llm))
                    st.subheader("Cleaned"); st.text_area("", cleaned_up, height=180, key="upload_clean_disp_key_upload") 
                    st.subheader("Diarized"); st.text_area("", diarized_up, height=180, key="upload_diar_disp_key_upload") 
                    if template:
                        with st.spinner("Generating note..."): note_up = asyncio.run(generate_note(diarized_up, llm_key_for_llm_tasks, llm_endpoint_for_llm_tasks, openai_api_version_llm, openai_model_name_llm, template, use_local_llm_for_notes, local_llm_model_name_for_notes, patient))
                        st.subheader("Generated Note"); st.text_area("", note_up, height=240, key="upload_note_disp_key_upload")
                        
                        # --- Coding and Payer Review Section ---
                        with st.spinner("Generating coding and payer review..."):
                            coding_review = generate_coding_and_review(
                                note_up,
                                azure_endpoint=llm_endpoint_for_llm_tasks,
                                azure_api_key=llm_key_for_llm_tasks,
                                deployment_name=openai_model_name_llm,
                                api_version=openai_api_version_llm
                            )
                        st.subheader("Coding & Payer Review")
                        st.text_area("E/M, ICD-10, SNOMED, CPT, Risk, SDOH, Alternate Dx, Payer Review", coding_review, height=350, key="upload_coding_review_txt_key_upload")
            else: 
                st.warning("LLM credentials (Azure OpenAI or Local) not configured. Basic diarization only.")
                st.text_area("Basic Diarized", apply_speaker_diarization(raw_transcript_upload), height=180, key="upload_basic_diar_disp_key_upload") 
        if use_encryption and final_audio_path_str and Path(final_audio_path_str).exists():
            with st.spinner("Encrypting audio file..."): 
                with secure_audio_processing(final_audio_path_str, True): 
                    st.success(f"Audio file {Path(final_audio_path_str).name} encrypted.")
    except Exception as e: logger.error(f"Upload processing error: {e}", exc_info=True); st.error(f"Upload error: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# View Transcription Section
# ─────────────────────────────────────────────────────────────────────────────
def render_view_transcription_section(
    asr_service_key: Optional[str], asr_service_endpoint: Optional[str], 
    openai_api_version_llm: Optional[str], openai_model_name_llm: Optional[str], 
    asr_info: str, 
    language: Optional[str] = "en-US"
):
    st.subheader("🔍 View Existing Transcription")
    uploaded_wav = st.file_uploader("Pick a WAV file", type=["wav"], key="view_wav_uploader_key_view") # Unique key
    if not uploaded_wav: return
    try:
        temp_view_dir = Path(get_config_value("CACHE_DIR")); temp_view_dir.mkdir(parents=True, exist_ok=True)
        view_path_obj = temp_view_dir / uploaded_wav.name
        view_path_obj.write_bytes(uploaded_wav.read()); view_path_str = str(view_path_obj)
        
        llm_key_for_azure_speech_postproc = get_config_value("AZURE_API_KEY")
        llm_endpoint_for_azure_speech_postproc = get_config_value("AZURE_ENDPOINT")

        with st.spinner("Transcribing..."):
            if asr_info == "azure_speech":
                view_txt = transcribe_audio(view_path_str, "azure_speech", azure_key=asr_service_key, asr_service_endpoint=asr_service_endpoint, openai_key=llm_key_for_azure_speech_postproc, openai_endpoint=llm_endpoint_for_azure_speech_postproc, language=language, return_raw=True) # Ensure raw for view
            elif asr_info == "azure_whisper":
                view_txt = transcribe_audio(view_path_str, "azure_whisper", openai_key=asr_service_key, openai_endpoint=asr_service_endpoint, language=language)
            elif asr_info.startswith("whisper:"): view_txt = transcribe_audio(view_path_str, asr_info)
            else: 
                vosk_model_path = str(config["MODEL_DIR"] / "vosk-model-small-en-us-0.15") if asr_info == "vosk_small" else asr_info
                view_txt = transcribe_audio(view_path_str, "vosk_model", model_path=vosk_model_path)
        st.subheader("Transcription"); st.text_area("", view_txt, height=200, key="view_trans_text_area_key_view") # Unique key
    except Exception as e: logger.error(f"View transcription error: {e}", exc_info=True); st.error(f"View error: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# ASR Model Comparison Section
# ─────────────────────────────────────────────────────────────────────────────
def render_model_comparison_section(
    selected_asr_info_from_sidebar: str, 
    language_from_sidebar: Optional[str] = "en-US"
    ):
    st.subheader("⚖️ ASR Model Comparison")
    mdir = Path(get_config_value("MODEL_DIR")); vosk_opts = [d.name for d in mdir.iterdir() if d.is_dir()] if mdir.exists() else []
    whisper_opts = ["tiny", "base", "small", "medium", "large"]
    
    comp_models = {} 
    for vo in vosk_opts: comp_models[f"Vosk ({vo})"] = str(mdir / vo)
    if not vosk_opts or "vosk-model-small-en-us-0.15" not in vosk_opts : 
        comp_models["Vosk (default small)"] = "vosk_small" 
    for wo in whisper_opts: comp_models[f"Whisper ({wo})"] = f"whisper:{wo}"
    comp_models["Azure Speech"] = "azure_speech"
    comp_models["Azure Whisper (OpenAI SDK)"] = "azure_whisper"
    
    comp_keys_list = list(comp_models.keys())
    if not comp_keys_list: st.warning("No ASR models found for comparison."); return

    col_sel1, col_sel2 = st.columns(2)
    with col_sel1: m1_disp = st.selectbox("Model 1", comp_keys_list, key="comp_m1_sel_key_comp", index=0) # Unique key
    with col_sel2: m2_disp = st.selectbox("Model 2", comp_keys_list, key="comp_m2_sel_key_comp", index=min(1, len(comp_keys_list)-1)) # Unique key
    m1_key = comp_models[m1_disp]; m2_key = comp_models[m2_disp]

    compare_wav = st.file_uploader("Choose WAV for comparison", type=["wav"], key="compare_wav_upload_key_comp") # Unique key
    if not compare_wav or not m1_key or not m2_key: st.info("Select two models and upload WAV."); return

    if st.button("Run Comparison", key="run_comp_btn_main_key_comp"): # Unique key
        azure_speech_key_comp = get_config_value("AZURE_SPEECH_API_KEY")
        azure_speech_endpoint_comp = get_config_value("AZURE_SPEECH_ENDPOINT")
        azure_openai_key_comp = get_config_value("AZURE_API_KEY") 
        azure_openai_endpoint_comp = get_config_value("AZURE_ENDPOINT")

        def get_comp_transcript(model_id: str, audio_p: str, lang: Optional[str]) -> str:
            if model_id == "azure_speech":
                if not azure_speech_key_comp or not azure_speech_endpoint_comp: return "ERROR: Azure Speech keys missing for comparison."
                return transcribe_audio(audio_p, "azure_speech", azure_key=azure_speech_key_comp, azure_endpoint=azure_speech_endpoint_comp, openai_key=azure_openai_key_comp, openai_endpoint=azure_openai_endpoint_comp, language=lang, return_raw=True) # Ensure raw for comparison
            elif model_id == "azure_whisper":
                if not azure_openai_key_comp or not azure_openai_endpoint_comp: return "ERROR: Azure OpenAI keys missing for Azure Whisper comparison."
                return transcribe_audio(audio_p, "azure_whisper", openai_key=azure_openai_key_comp, openai_endpoint=azure_openai_endpoint_comp, language=lang)
            elif model_id.startswith("whisper:"): return transcribe_audio(audio_p, model_id)
            elif model_id == "vosk_small": 
                vosk_model_path = str(config["MODEL_DIR"] / "vosk-model-small-en-us-0.15")
                return transcribe_audio(audio_p, "vosk_model", model_path=vosk_model_path)
            elif Path(model_id).is_dir(): return transcribe_audio(audio_p, "vosk_model", model_path=model_id)
            return f"ERROR: Unknown model '{model_id}' for comparison."

        try:
            with st.spinner("Comparing..."):
                comp_dir = Path(get_config_value("CACHE_DIR")); comp_dir.mkdir(parents=True, exist_ok=True)
                comp_path = comp_dir / f"comp_{compare_wav.name}"; comp_path.write_bytes(compare_wav.read()); comp_path_str = str(comp_path)
                
                txt1 = get_comp_transcript(m1_key, comp_path_str, language_from_sidebar)
                txt2 = get_comp_transcript(m2_key, comp_path_str, language_from_sidebar)

            res_col1, res_col2 = st.columns(2)
            with res_col1: st.subheader(m1_disp); st.text_area("", txt1, height=200, key="comp_txt1_area_key_comp"); wc1 = 0 if txt1.startswith("ERROR:") else len(txt1.split()); st.caption(f"Words: {wc1}") # Unique key
            with res_col2: st.subheader(m2_disp); st.text_area("", txt2, height=200, key="comp_txt2_area_key_comp"); wc2 = 0 if txt2.startswith("ERROR:") else len(txt2.split()); st.caption(f"Words: {wc2}") # Unique key
            

            st.subheader("Metrics")
            if txt1.startswith("ERROR:") or txt2.startswith("ERROR:"): st.warning("Comparison incomplete due to error in one or both transcriptions.")
            else:
                diff = abs(wc1 - wc2); diff_pc = (diff / max(wc1, wc2, 1)) * 100
                st.markdown(f"""| Metric | {m1_disp} | {m2_disp} | Diff |
|---|---|---|---|
| Word Count | {wc1} | {wc2} | {diff} ({diff_pc:.1f}%) |""")
                if wc1 > wc2: st.info(f"{m1_disp} produced a longer transcript.")
                elif wc2 > wc1: st.info(f"{m2_disp} produced a longer transcript.")
                else: st.success("Both models produced transcripts of the same word count.")
        except Exception as e: logger.error(f"Comparison error: {e}", exc_info=True); st.error(f"Comparison failed: {e}")