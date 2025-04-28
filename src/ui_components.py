# src/ui_components.py
"""
ui_components.py
Streamlit UI helpers with improved recording flow, real-time ASR, and ASR model comparison
"""

from __future__ import annotations
import asyncio, io, json, time, wave, queue # Added queue
from pathlib import Path
from typing import Tuple, Optional, List, Dict, Any

import numpy as np
import streamlit as st
import librosa

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

# This function was duplicated, keeping one definition
# def format_elapsed_time(start_time, current_time=None):
#     """Format elapsed time as MM:SS."""
#     import time
#     if current_time is None:
#         current_time = time.time()
#     elapsed = current_time - start_time
#     minutes = int(elapsed // 60)
#     seconds = int(elapsed % 60)
#     return f"{minutes:02d}:{seconds:02d}"

# ─────────────────────────────────────────────────────────────────────────────
# Sidebar configuration
# ─────────────────────────────────────────────────────────────────────────────
def render_sidebar() -> Tuple[
    Optional[str], Optional[str], Optional[str], Optional[str],
    str, bool, str, bool
]:
    with st.sidebar:
        st.header("⚙️ Configuration")

        # Azure Configuration Section
        st.subheader("Azure Configuration")
        
        # These inputs are for Azure OpenAI (for note generation, etc.)
        azure_openai_api_key = st.text_input(
            "Azure OpenAI API Key",
            value=config.get("AZURE_API_KEY") or config.get("AZURE_OPENAI_API_KEY", ""),
            type="password",
            key="sidebar_azure_openai_api_key"
        )
        
        azure_openai_endpoint = st.text_input(
            "Azure OpenAI Endpoint",
            value=config.get("AZURE_ENDPOINT", ""),
            key="sidebar_azure_openai_endpoint"
        )

        # Initialize variables to be returned
        azure_key_to_return = azure_openai_api_key
        azure_endpoint_to_return = azure_openai_endpoint

        # Note generation model
        st.subheader("Note Generation")
        src = st.selectbox(
            "Note Model",
            ["Azure OpenAI (GPT-4)", "Local LLM Model"]
        )
        use_local = src.startswith("Local")
        local_model = ""
        if use_local:
            models_dir = config["LOCAL_MODELS_DIR"]
            opts = [d.name for d in models_dir.iterdir() if d.is_dir()] if models_dir.exists() else []
            if opts:
                local_model = st.selectbox("Local LLM Model", opts, key="local_choice")

        # Real-time ASR engine
        st.subheader("Speech Recognition")
        engine = st.selectbox(
            "ASR Engine",
            ["Vosk", "Whisper", "Azure Speech"]
        )
        
        # Engine-specific configuration
        if engine == "Vosk":
            mdir = config["MODEL_DIR"]
            opts = [d.name for d in mdir.iterdir() if d.is_dir()] if mdir.exists() else []
            asr_path = st.selectbox("Vosk Model", opts) if opts else ""
            asr_info = str(mdir / asr_path) if opts and asr_path else "vosk_small"
        elif engine == "Whisper":
            size = st.selectbox(
                "Whisper Size",
                ["tiny", "base", "medium"]
            )
            asr_info = f"whisper:{size}"
        elif engine == "Azure Speech":
            asr_info = "azure_speech"
            # Show Azure Speech specific inputs only when selected
            st.subheader("Azure Speech Configuration")
            azure_speech_api_key = st.text_input(
                "Azure Speech API Key",
                value=config.get("AZURE_SPEECH_API_KEY", ""),
                type="password",
                key="sidebar_azure_speech_api_key"
            )
            
            azure_speech_endpoint = st.text_input(
                "Azure Speech Endpoint",
                value=config.get("AZURE_SPEECH_ENDPOINT", ""),
                key="sidebar_azure_speech_endpoint"
            )

            # Use the speech-specific keys/endpoints if provided, otherwise fall back to OpenAI keys
            # This allows using a single set of keys for both if they are the same
            azure_key_to_return = azure_speech_api_key if azure_speech_api_key else azure_openai_api_key
            azure_endpoint_to_return = azure_speech_endpoint if azure_speech_endpoint else azure_openai_endpoint

            if not azure_key_to_return or not azure_endpoint_to_return:
                 st.warning("⚠️ Azure Speech requires both API Key and Endpoint")

        else:
            asr_info = ""

        # Security Settings
        st.subheader("Security")
        use_encryption = st.checkbox(
            "Encrypt recordings on save",
            value=True
        )

        return (
            azure_key_to_return,
            azure_endpoint_to_return,
            config.get("API_VERSION"), # This is likely for OpenAI, might need review
            config.get("MODEL_NAME"),   # This is likely for OpenAI model name
            asr_info,
            use_local,
            local_model,
            use_encryption
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
        
        # Add consent checkbox
        consent_text = "The patient was informed of the presence of a listening and transcribing tool during the visit and given the option to opt out and agreed to proceed."
        pd["consent"] = st.checkbox(
            consent_text,
            value=pd.get("consent", False),
            key=f"{prefix}_consent"
        )
        
        # Display consent status
        if pd["consent"]:
            st.success("✅ Patient consent recorded")
        else:
            st.warning("⚠️ Patient consent required before recording")
    
    return pd

# ─────────────────────────────────────────────────────────────────────────────
# Template Section
# ─────────────────────────────────────────────────────────────────────────────

def render_template_section(prefix: str) -> str:
    st.subheader("📝 Note Template")
    tmpl_store = load_prompt_templates()
    options = ["✨ Create New Template"] + list(tmpl_store.keys())
    # Ensure default selection exists or handle gracefully
    current_selection = st.session_state.get(f"{prefix}_tmpl_choice", "✨ Create New Template")
    if current_selection not in options:
        current_selection = "✨ Create New Template" # Reset if invalid

    choice = st.selectbox(
        "Template",
        options,
        index=options.index(current_selection), # Set index based on current state
        key=f"{prefix}_tmpl_choice"
    )
    template_text_key = f"{prefix}_tmpl_text"

    if choice == "✨ Create New Template":
        # Use session state to preserve text when switching templates
        st.session_state.setdefault(template_text_key, "")
        txt = st.text_area(
            "Template Instructions",
            st.session_state[template_text_key],
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
            # Update state and rerun to select the new template
            st.session_state[f"{prefix}_tmpl_choice"] = name
            st.rerun()
        final_template_text = txt # Use the text from the text area
    else:
        # Load selected template text
        selected_template_content = tmpl_store.get(choice, "")
        st.session_state[template_text_key] = selected_template_content # Update session state
        txt = st.text_area(
            "Template Instructions",
            selected_template_content,
            key=template_text_key, # Keep the same key
            height=180
        )
        final_template_text = txt # Use the text from the text area (allows edits)

    return final_template_text # Return the currently displayed/edited text

# ─────────────────────────────────────────────────────────────────────────────
# Real-time ASR with enhanced visualization
# ─────────────────────────────────────────────────────────────────────────────

def render_realtime_asr(
    asr_info: str,
    azure_key: Optional[str], endpoint: Optional[str], api_ver: Optional[str], model_name: Optional[str],
    use_local_llm: bool, local_llm: str, patient: dict, template: str, use_encryption: bool,
    consent_given: bool = False
):
    """Real-time ASR implementation using StreamRecorder with enhanced visualization and auto-processing."""
    from .recorder import StreamRecorder
    from .audio_processing import live_vosk_callback, live_whisper_callback, live_azure_callback
    import time

    st.write("### Real-time Transcription")

    # Create UI placeholders with more structure
    status_placeholder = st.empty()
    transcript_placeholder = st.empty()
    control_container = st.container()
    processing_results_container = st.container()

    # Initialize session state for recording state if not exists
    if "realtime_recording" not in st.session_state:
        st.session_state.realtime_recording = False
        st.session_state.realtime_recorder = None
        st.session_state.transcript_history = ""
        st.session_state.recording_start_time = 0
        st.session_state.update_queue = None
        st.session_state.last_partial = ""
        st.session_state.last_words_info = []
        st.session_state.current_transcript = ""
        st.session_state.last_recorded_path = None

    # --- Determine which ASR engine to use
    is_whisper = asr_info.startswith("whisper:")
    is_azure_speech = asr_info == "azure_speech"

    # Display model info based on engine type
    if is_whisper:
        model_size = asr_info.split(":", 1)[1]
        st.info(f"Using Whisper model: {model_size}")
    elif is_azure_speech:
        st.info("Using Azure Speech Service")
        if not azure_key or not endpoint:
            st.error("Azure Speech requires API key and endpoint. Please provide them in the sidebar.")
            return
    else:  # Vosk
        model_path = asr_info
        vosk_model_display_name = "Unknown Vosk Model"
        if Path(asr_info).exists() and Path(asr_info).is_dir():
            vosk_model_display_name = Path(asr_info).name
        elif asr_info == "vosk_small":
            vosk_model_display_name = "Default Small Model"
        st.info(f"Using Vosk model: {vosk_model_display_name}")

    # Display consent warning if not given
    if not consent_given:
        st.error("⚠️ Recording is disabled until patient consent is documented. Please check the consent box in the Patient Information section.")

    # Handle start/stop recording
    with control_container:
        col1, col2, col3 = st.columns(3)

        # Start button - disabled if no consent
        if col1.button("▶ Start Transcription", 
                      disabled=st.session_state.realtime_recording or not consent_given,
                      key="start_asr_btn"):
            st.session_state.realtime_recording = True
            st.session_state.recording_start_time = time.time()
            st.session_state.transcript_history = ""
            st.session_state.last_partial = ""
            st.session_state.last_words_info = []
            st.session_state.current_transcript = ""
            st.session_state.last_recorded_path = None

            # Create queue and store in session state
            q = queue.Queue()
            st.session_state.update_queue = q

            # Create the appropriate callback function based on ASR selection
            try:
                if is_whisper:
                    callback_fn = live_whisper_callback(asr_info.split(":", 1)[1], q)
                elif is_azure_speech:
                    if not azure_key or not endpoint:
                        st.error("Azure Speech requires API key and endpoint")
                        st.session_state.realtime_recording = False
                        st.stop()
                    callback_fn = live_azure_callback(azure_key, endpoint, q)
                else:  # Vosk
                    if not Path(asr_info).exists() or not Path(asr_info).is_dir():
                        st.error(f"Invalid Vosk model path selected: {asr_info}. Please select a valid model.")
                        st.session_state.realtime_recording = False
                        st.stop()
                    callback_fn = live_vosk_callback(asr_info, q)

                # Create recorder with the queue-based callback
                recorder = StreamRecorder(on_chunk=callback_fn)
                recorder.start()
                st.session_state.realtime_recorder = recorder
                st.rerun()
            except Exception as e:
                logger.error(f"Failed to start StreamRecorder: {e}", exc_info=True)
                st.error(f"Error starting audio recording: {e}. Check microphone permissions and availability.")
                st.session_state.realtime_recording = False

        # Pause/Resume button (only enabled when recording)
        is_paused = False
        if st.session_state.realtime_recording and st.session_state.realtime_recorder:
            recorder = st.session_state.realtime_recorder
            is_paused = recorder._paused

            if col2.button("⏸ Pause" if not is_paused else "▶ Resume", key="pause_asr_btn"):
                if is_paused:
                    recorder.resume()
                else:
                    recorder.pause()
                st.rerun()
        else:
            # Disabled button when not recording
            col2.button("⏸ Pause", disabled=True, key="pause_asr_btn_disabled")

        # Stop button
        if col3.button("■ Stop Transcription", disabled=not st.session_state.realtime_recording,
                      key="stop_asr_btn"):
            if st.session_state.realtime_recorder:
                # Stop the recorder and save the file
                recorder = st.session_state.realtime_recorder
                try:
                    wav_path_obj = recorder.stop()
                    st.session_state.last_recorded_path = str(wav_path_obj)
                    
                    # Explicitly set current_transcript before setting the flag and rerunning
                    final_transcript = st.session_state.get("transcript_history", "")
                    st.session_state.current_transcript = final_transcript
                    
                    # Debug: log what's being stored
                    logger.info(f"Storing transcript of length {len(final_transcript)} characters")
                    if not final_transcript:
                        logger.warning("WARNING: Empty transcript captured - check transcript_history")
                        # Try to get any transcript accumulated in the update_queue
                        while st.session_state.update_queue and not st.session_state.update_queue.empty():
                            try:
                                update_data = st.session_state.update_queue.get_nowait()
                                if update_data.get("text"):
                                    final_transcript = update_data["text"]
                                    st.session_state.current_transcript = final_transcript
                                    logger.info(f"Retrieved transcript from queue: {len(final_transcript)} chars")
                                    break
                            except:
                                break

                    # Reset recorder state
                    st.session_state.realtime_recording = False
                    st.session_state.realtime_recorder = None
                    st.session_state.update_queue = None

                    st.success(f"Recording saved to {wav_path_obj.name}")
                    st.session_state.just_stopped_realtime = True
                    st.rerun()
                except Exception as e:
                    logger.error(f"Error stopping recorder or saving file: {e}", exc_info=True)
                    st.error(f"Error stopping recording: {e}")
                    st.session_state.realtime_recording = False
                    st.session_state.realtime_recorder = None
                    st.session_state.update_queue = None

    # --- Queue Processing and UI Update Logic (Main Thread) ---
    current_elapsed_time = "00:00"
    status_message = "Idle"
    if st.session_state.realtime_recording:
        # Calculate current elapsed time for display even if queue is empty
        current_elapsed_time = format_elapsed_time(st.session_state.recording_start_time)
        status_message = "🎤 Listening..."
        if st.session_state.realtime_recorder and st.session_state.realtime_recorder._paused:
             status_message = "⏸️ Paused"

        # Process items from the queue
        if st.session_state.update_queue:
            while not st.session_state.update_queue.empty():
                try:
                    update_data = st.session_state.update_queue.get_nowait()

                    # Update accumulated transcript and last partial/words
                    st.session_state.transcript_history = update_data["text"]
                    st.session_state.last_partial = update_data["partial"]
                    st.session_state.last_words_info = update_data.get("words_info", [])
                    current_elapsed_time = update_data["elapsed"] # Use time from update

                    # Update status message based on final/partial
                    if update_data["is_final"]:
                        status_message = "💬 Processing complete sentence..."
                    # Keep "Listening..." for partial results

                except queue.Empty:
                    break # Queue is empty, stop processing for now
                except Exception as e:
                    logger.error(f"Error processing update queue: {e}", exc_info=True)
                    # Avoid stopping the app, just log and show error
                    st.toast(f"Error updating transcript display: {e}", icon="⚠️")
                    break # Stop processing on error

    # Update Status Placeholder
    with status_placeholder.container():
        if st.session_state.realtime_recording:
            cols = st.columns([1, 3])
            with cols[0]:
                st.markdown(f"🔴 **RECORDING: {current_elapsed_time}**")
            with cols[1]:
                st.markdown(status_message)

            # Display pulsing alert if actively recording and not paused
            if not (st.session_state.realtime_recorder and st.session_state.realtime_recorder._paused):
                st.markdown(f"""
                <div style="
                    padding: 10px;
                    border-radius: 5px;
                    background-color: rgba(255, 0, 0, 0.1);
                    border-left: 5px solid red;
                    animation: pulse 1.5s infinite;
                ">
                    <span style="color: red; font-weight: bold;">●</span> RECORDING IN PROGRESS - {current_elapsed_time}
                </div>
                <style>
                @keyframes pulse {{
                    0% {{ opacity: 1; }}
                    50% {{ opacity: 0.5; }}
                    100% {{ opacity: 1; }}
                }}
                </style>
                """, unsafe_allow_html=True)
        else:
             st.markdown("⚪ **IDLE**") # Show idle status when not recording


    # Update Transcript Placeholder
    with transcript_placeholder.container():
        # Always display the latest known state
        formatted_html = format_transcript_with_confidence(
            st.session_state.transcript_history,
            st.session_state.last_partial,
            st.session_state.last_words_info
        )
        st.markdown("#### Live Transcript:")
        # Use a min-height to prevent layout jumps
        st.markdown(f'<div style="min-height: 50px;">{formatted_html if formatted_html else "_(Waiting for speech...)_"}</div>', unsafe_allow_html=True)


    # --- Automatic Processing after Stop ---
    # This post-processing code runs for both Vosk and Whisper after stopping
    # Flag is set in the stop button section for both engines
    # Do not duplicate this block
    # ...
    

    # Rerun periodically while recording to check the queue
    if st.session_state.realtime_recording:
        # Use Streamlit's experimental rerun feature for smoother updates if available,
        # otherwise fall back to time.sleep
        try:
             st.experimental_rerun(ttl=0.1) # Rerun after 100ms
        except AttributeError:
             time.sleep(0.1) # Small delay to prevent excessive reruns
             st.rerun()

    # --- Post-processing code for both engines ---
    # This code runs after stopping either Vosk or Whisper recording
    # The flag is set in the stop button section of each engine
    if st.session_state.pop("just_stopped_realtime", False):
        # Directly use the current_transcript set when stopping
        transcript = st.session_state.get("current_transcript", "") 
        wav_file_path = st.session_state.get("last_recorded_path")

        # Make sure we have a transcript - if current_transcript is empty, 
        # fall back to transcript_history as a backup
        if not transcript and st.session_state.get("transcript_history"):
            transcript = st.session_state.get("transcript_history", "")
            st.info("Using accumulated transcript history.")
        
        # Final fallback: if we have a WAV file but still no transcript, try to transcribe it directly
        if not transcript and wav_file_path and Path(wav_file_path).exists():
            try:
                with st.spinner("No transcript captured. Transcribing audio file directly..."):
                    # Determine transcription method based on current ASR info
                    if asr_info.startswith("whisper:"):
                        # For whisper, use the model size specified in asr_info
                        transcript = transcribe_audio(wav_file_path, asr_info)
                    elif Path(asr_info).exists() and Path(asr_info).is_dir():
                        # For Vosk with specific model path
                        transcript = transcribe_audio(wav_file_path, "vosk_model", model_path=asr_info)
                    else:
                        # Fallback to default vosk_small
                        transcript = transcribe_audio(wav_file_path, "vosk_small")
                    
                    if transcript:
                        st.success("Successfully transcribed audio file as fallback.")
                    else:
                        st.warning("Fallback transcription produced empty result.")
            except Exception as e:
                logger.error(f"Error during fallback transcription: {e}", exc_info=True)
                st.error(f"Failed to transcribe audio: {e}")

        if transcript: # Check if the transcript is actually non-empty
            with processing_results_container: # Display results in their own container
                st.subheader("Processing Final Transcript...")
                # Display final transcript clearly before processing
                with st.expander("Final Recorded Transcript", expanded=True):
                     st.text_area("", transcript, height=180, key="asr_final_transcript_display_auto")

                if azure_key or use_local_llm:
                    try:
                        with st.spinner("Cleaning transcription..."):
                            cleaned = asyncio.run(clean_transcription(
                                transcript, azure_key, endpoint, api_ver, model_name,
                                use_local=use_local_llm, local_model=local_llm, highlight_terms=True
                            ))
                        st.subheader("Cleaned Transcription")
                        st.text_area("", cleaned, height=180, key="realtime_cleaned_transcript_auto")

                        with st.spinner("Identifying speakers..."):
                            diarized = asyncio.run(generate_gpt_speaker_tags(
                                cleaned, azure_key, endpoint, api_ver, model_name
                            ))
                        st.subheader("Diarized Transcription")
                        st.text_area("", diarized, height=180, key="realtime_diarized_transcript_auto")

                        note = ""
                        if template:
                            with st.spinner("Generating medical note..."):
                                note = asyncio.run(generate_note(
                                    diarized, azure_key, endpoint, api_ver, model_name,
                                    template, use_local_llm, local_llm, patient
                                ))
                            st.subheader("Generated Note")
                            st.text_area("", note, height=240, key="realtime_generated_note_auto")
                        else:
                             st.info("No template selected for note generation.")

                    except Exception as e:
                         logger.error(f"Error during transcript processing: {e}", exc_info=True)
                         st.error(f"An error occurred during processing: {e}")

                else:
                    # Simple processing without API key
                    st.warning("API key not provided. Showing basic transcript without advanced features.")
                    try:
                        # Apply basic diarization
                        diarized = apply_speaker_diarization(transcript) # Use the final transcript
                        st.subheader("Basic Diarized Transcription")
                        st.text_area("", diarized, height=180, key="realtime_basic_diarized_auto")
                        st.info("For advanced features like transcript cleaning and note generation, please provide an Azure API key or configure a local LLM in the sidebar.")
                    except Exception as e:
                         logger.error(f"Error during basic diarization: {e}", exc_info=True)
                         st.error(f"An error occurred during basic diarization: {e}")

                    # Handle encryption after processing
                    if use_encryption and wav_file_path and Path(wav_file_path).exists():
                         try:
                             with st.spinner("Encrypting audio file..."):
                                 with secure_audio_processing(wav_file_path, True):
                                     st.success(f"Audio file {Path(wav_file_path).name} encrypted.")
                         except Exception as e:
                             logger.error(f"Error encrypting file {wav_file_path}: {e}", exc_info=True)
                             st.warning(f"Failed to encrypt audio file: {e}")
                    elif use_encryption and not wav_file_path:
                         logger.warning("Encryption enabled but no WAV file path found.")


        else: # No transcript captured
             with processing_results_container:
                 st.warning("No transcript captured to process.")


# ─────────────────────────────────────────────────────────────────────────────
# Recording Flow: Start, Pause, Stop → Pipeline Results
# ─────────────────────────────────────────────────────────────────────────────

# Corrected function signature (removed duplicates)
def render_recording_section(
    azure_key: Optional[str], endpoint: Optional[str], api_ver: Optional[str], model_name: Optional[str],
    asr_info: str, use_local_llm: bool, local_llm: str, use_encryption: bool
):
    st.subheader("🎙️ Record & Generate Note")
    
    # Add a prominent consent button at the top
    consent_text = "The patient was informed of the presence of a listening and transcribing tool during the visit and given the option to opt out and agreed to proceed."
    
    # Add a prominent consent box before the patient info section
    consent_container = st.container(border=True)
    with consent_container:
        st.markdown("### 📝 Patient Consent Documentation")
        
        # Render patient data and template sections
        patient = render_patient_data_section("rec")
        
        # Get consent status from patient data
        has_consent = patient.get("consent", False)
        
        # Add a prominent standalone consent button
        if has_consent:
            st.success("✅ **CONSENT RECORDED**: Patient has been informed and has agreed to proceed with recording and transcription.")
        else:
            st.warning("⚠️ **CONSENT REQUIRED**: Recording is disabled until patient consent is documented.")
            st.info(consent_text)
            # Add a big button as an alternative to the checkbox in patient info
            if st.button("📝 DOCUMENT PATIENT CONSENT", 
                        use_container_width=True,
                        type="primary"):
                # Update the consent in patient data
                patient["consent"] = True
                st.session_state[f"patient_rec"]["consent"] = True
                st.rerun()  # Rerun to update UI
    
    # Template section (outside the consent container)
    template = render_template_section("rec")
    
    # Check if patient consent has been given (from patient data)
    if not has_consent:
        st.error("⚠️ Patient consent is required before recording. Check the consent box in Patient Information or use the consent button above.")

    # Option for real-time ASR vs. traditional recording
    asr_mode = st.radio(
        "Transcription Mode",
        ["Traditional Recording", "Real-time ASR"],
        index=0, # Default to Traditional
        key="asr_mode_selection" # Add key
    )

    # Display API key status
    if not azure_key and not use_local_llm:
        st.info("ℹ️ **Note**: Basic transcription works without an API key, but cleaning, diarization, and note generation require an Azure API key or local LLM.")

    if asr_mode == "Real-time ASR" and asr_info:
        # Real-time ASR mode using StreamRecorder
        # Pass necessary parameters for processing down to render_realtime_asr
        render_realtime_asr(
            asr_info,
            azure_key, endpoint, api_ver, model_name,
            use_local_llm, local_llm, patient, template, use_encryption, # Pass all needed params
            consent_given=has_consent # Pass consent status
        )
        # Processing logic is now handled *inside* render_realtime_asr after stopping

    else: # Traditional Recording Mode
        # Corrected Traditional recording UI and processing logic
        from .recorder import StreamRecorder
        # Use a different session state key for the traditional recorder instance
        rec = st.session_state.get("traditional_recorder")
        
        # Display consent warning if not given
        if not has_consent:
            st.error("⚠️ Recording is disabled until patient consent is documented. Please check the consent box in the Patient Information section.")

        col1, col2, col3 = st.columns(3)

        if col1.button("▶ Start Recording", 
                      disabled=(rec is not None) or not has_consent, 
                      key="start_traditional_rec"):
            # Clear previous results when starting new traditional recording
            if "last_wav_traditional" in st.session_state:
                 del st.session_state["last_wav_traditional"]
            # Clear potential leftover processing results display areas
            st.session_state.traditional_results_placeholder = st.empty()

            recorder = StreamRecorder() # No callback needed for traditional
            recorder.start()
            st.session_state["traditional_recorder"] = recorder
            st.rerun() # Rerun to update button states

        is_recording = rec is not None and not rec._paused
        if col2.button("⏸ Pause" if is_recording else "▶ Resume", disabled=(rec is None), key="pause_traditional_rec"):
            if rec:
                if is_recording:
                    rec.pause()
                else:
                    rec.resume()
                st.rerun() # Rerun to update button states

        if col3.button("■ Stop Recording", disabled=(rec is None), key="stop_traditional_rec"):
            recorder = st.session_state.pop("traditional_recorder", None)
            if recorder:
                try:
                    wav_path_obj = recorder.stop()
                    # Use a different key to trigger processing for traditional mode
                    st.session_state["last_wav_traditional"] = str(wav_path_obj)
                    st.success(f"Recording saved: {wav_path_obj.name}")
                    st.rerun() # Rerun to trigger processing block below
                except Exception as e:
                     logger.error(f"Error stopping traditional recorder: {e}", exc_info=True)
                     st.error(f"Error stopping recording: {e}")


        # Container for traditional processing results
        if "traditional_results_placeholder" not in st.session_state:
             st.session_state.traditional_results_placeholder = st.empty()

        # Process recorded audio if available (triggered after stop by "last_wav_traditional")
        if "last_wav_traditional" in st.session_state:
             wav_path_str = st.session_state.pop("last_wav_traditional") # Get and remove path from state

             with st.session_state.traditional_results_placeholder.container(): # Display results here
                 # Determine transcription key based on sidebar ASR selection
                 transcription_key = "vosk_small"  # Default
                 model_details = None
                 if asr_info:
                     if asr_info.startswith("whisper:"):
                         transcription_key = "local_whisper"
                         model_details = asr_info
                     elif asr_info == "azure_speech":
                         transcription_key = "azure_speech"
                         model_details = None
                     elif Path(asr_info).is_dir():
                         transcription_key = "vosk_model"
                         model_details = asr_info

                 try:
                     with st.spinner("Transcribing audio..."):
                         if transcription_key == "vosk_model" and model_details:
                             raw = transcribe_audio(wav_path_str, transcription_key, model_path=model_details)
                         elif transcription_key == "local_whisper":
                              raw = transcribe_audio(wav_path_str, model_details)
                         elif transcription_key == "azure_speech":
                             raw = transcribe_audio(wav_path_str, transcription_key, 
                                                 azure_key=azure_key, azure_endpoint=endpoint)
                         else:
                             raw = transcribe_audio(wav_path_str, transcription_key)

                     st.subheader("Raw Transcription")
                     st.text_area("Raw Transcript", raw, height=180, key="recording_raw_transcript")

                     # Clean the transcription if API key available
                     if azure_key or use_local_llm:
                         with st.spinner("Cleaning transcription..."):
                             cleaned = asyncio.run(clean_transcription(
                                 raw, azure_key, endpoint, api_ver, model_name,
                                 use_local=use_local_llm, local_model=local_llm, highlight_terms=True
                             ))
                         st.subheader("Cleaned Transcription")
                         st.text_area("Cleaned Transcript", cleaned, height=180, key="recording_cleaned_transcript")

                         with st.spinner("Identifying speakers..."):
                             diarized = asyncio.run(generate_gpt_speaker_tags(
                                 cleaned, azure_key, endpoint, api_ver, model_name
                             ))
                         st.subheader("Diarized Transcription")
                         st.text_area("Diarized Transcript", diarized, height=180, key="recording_diarized_transcript")

                         # Generate medical note if template available
                         if template:
                             with st.spinner("Generating medical note..."):
                                 note = asyncio.run(generate_note(
                                     diarized, azure_key, endpoint, api_ver, model_name,
                                     template, use_local_llm, local_llm, patient
                                 ))
                             st.subheader("Generated Note")
                             st.text_area("Generated Medical Note", note, height=240, key="recording_generated_note")
                         else:
                              st.info("No template selected for note generation.")
                     else:
                         # Basic processing without API key
                         st.warning("API key not provided. Showing basic transcript without advanced features.")
                         diarized = apply_speaker_diarization(raw) # Use raw transcript
                         st.subheader("Basic Diarized Transcription")
                         # Use unique key for traditional mode basic diarization display
                         st.text_area("", diarized, height=180, key="recording_basic_diarized")
                         st.info("For advanced features like transcript cleaning and note generation, please provide an Azure API key or configure a local LLM in the sidebar.")

                     # Handle encryption if enabled
                     if use_encryption:
                         with st.spinner("Encrypting audio file..."):
                              # Use the wav_path_str which holds the path
                              with secure_audio_processing(wav_path_str, True):
                                   st.success(f"Audio file {Path(wav_path_str).name} encrypted.")

                 except Exception as e:
                      logger.error(f"Error during traditional recording processing: {e}", exc_info=True)
                      st.error(f"An error occurred during processing: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# Upload Audio Section
# ─────────────────────────────────────────────────────────────────────────────

def render_upload_section(
    azure_key: Optional[str], endpoint: Optional[str], api_ver: Optional[str], model_name: Optional[str],
    asr_info: str, use_local_llm: bool, local_llm: str, use_encryption: bool = False
):
    st.subheader("⬆️ Upload Audio & Generate Note")
    
    # Add a prominent consent box before the patient info section
    consent_text = "The patient was informed of the presence of a listening and transcribing tool during the visit and given the option to opt out and agreed to proceed."
    
    consent_container = st.container(border=True)
    with consent_container:
        st.markdown("### 📝 Patient Consent Documentation")
        
        # Render patient data and template sections
        patient = render_patient_data_section("upload")
        
        # Get consent status from patient data
        has_consent = patient.get("consent", False)
        
        # Add a prominent standalone consent button
        if has_consent:
            st.success("✅ **CONSENT RECORDED**: Patient has been informed and has agreed to proceed with recording and transcription.")
        else:
            st.warning("⚠️ **CONSENT REQUIRED**: Processing is disabled until patient consent is documented.")
            st.info(consent_text)
            # Add a big button as an alternative to the checkbox in patient info
            if st.button("📝 DOCUMENT PATIENT CONSENT", 
                        use_container_width=True,
                        type="primary",
                        key="upload_consent_btn"):
                # Update the consent in patient data
                patient["consent"] = True
                st.session_state[f"patient_upload"]["consent"] = True
                st.rerun()  # Rerun to update UI
    
    # Template section (outside the consent container)
    template = render_template_section("upload")

    # Check if patient consent has been given
    if not has_consent:
        st.error("⚠️ Patient consent is required before processing audio. Check the consent box in Patient Information or use the consent button above.")

    # Display API key status
    if not azure_key and not use_local_llm:
        st.info("ℹ️ **Note**: Basic transcription works without an API key, but cleaning, diarization, and note generation require an Azure API key or local LLM.")

    uploaded = st.file_uploader("Choose WAV/MP3/M4A", type=["wav","mp3","m4a"])
    if not uploaded:
        return

    # Process the uploaded file
    temp_file_path = None # Keep track of the final path for encryption
    try:
        with st.spinner("Processing uploaded audio..."):
            # Save the file
            temp = Path(config["CACHE_DIR"] / uploaded.name)
            temp.write_bytes(uploaded.read())
            temp_file_path = str(temp) # Initial path

            # Convert to WAV if necessary
            if temp.suffix.lower() != ".wav":
                from .audio_processing import convert_to_wav
                temp_file_path = convert_to_wav(str(temp)) # Update path after conversion
                temp = Path(temp_file_path) # Update Path object if needed

            # Determine transcription key based on sidebar ASR selection
            transcription_key = "vosk_small" # Default
            model_details = None
            if asr_info:
                if asr_info.startswith("whisper:"):
                    transcription_key = "local_whisper"
                    model_details = asr_info # e.g., "whisper:tiny"
                elif Path(asr_info).is_dir(): # Check if it's a valid dir path for Vosk
                    transcription_key = "vosk_model"
                    model_details = asr_info
                # Add elif for specific vosk keys if needed

            # Transcribe using the final path (temp_file_path)
            if transcription_key == "vosk_model" and model_details:
                raw = transcribe_audio(temp_file_path, transcription_key, model_path=model_details)
            elif transcription_key == "local_whisper":
                 raw = transcribe_audio(temp_file_path, model_details)
            else:
                raw = transcribe_audio(temp_file_path, transcription_key) # Default vosk_small

        # Show raw transcription
        st.subheader("Raw Transcription")
        st.text_area("Raw Transcript", raw, height=180, key="upload_raw_transcript")

        # Add processing button
        if st.button("Process Transcript and Generate Note", 
                    disabled=not has_consent,
                    key="upload_process_btn"):
            # Processing with API key
            if azure_key or use_local_llm:
                with st.spinner("Processing transcript..."):
                    # Clean the transcription
                    cleaned = asyncio.run(clean_transcription(
                        raw, azure_key, endpoint, api_ver, model_name,
                        use_local=use_local_llm, local_model=local_llm, highlight_terms=True
                    ))

                    # Apply speaker diarization with API
                    diarized = asyncio.run(generate_gpt_speaker_tags(
                        cleaned, azure_key, endpoint, api_ver, model_name
                    ))

                    # Display results
                    st.subheader("Cleaned Transcription")
                    st.text_area("Cleaned Transcript", cleaned, height=180, key="upload_cleaned_transcript")
                    st.subheader("Diarized Transcription")
                    st.text_area("Diarized Transcript", diarized, height=180, key="upload_diarized_transcript")

                    # Generate medical note if template available
                    if template:
                        with st.spinner("Generating medical note..."):
                            note = asyncio.run(generate_note(
                                diarized, azure_key, endpoint, api_ver, model_name,
                                template, use_local_llm, local_llm, patient
                            ))

                        st.subheader("Generated Note")
                        st.text_area("Generated Medical Note", note, height=240, key="upload_generated_note")
                    else:
                        st.warning("Please select or create a template to generate a note.")
            else:
                # Basic processing without API key
                with st.spinner("Applying basic speaker diarization..."):
                    diarized = apply_speaker_diarization(raw)

                st.subheader("Basic Diarized Transcription")
                st.text_area("", diarized, height=180, key="upload_basic_diarized")

                st.info("For advanced features like transcript cleaning and note generation, please provide an Azure API key in the sidebar.")

        # Handle encryption if enabled and file path exists
        if use_encryption and temp_file_path and Path(temp_file_path).exists():
            with st.spinner("Encrypting audio file..."):
                with secure_audio_processing(temp_file_path, True):
                    st.success(f"Audio file {Path(temp_file_path).name} encrypted.")
        elif use_encryption and not temp_file_path:
             logger.warning("Encryption enabled for upload, but file path was not determined.")

    except Exception as e:
         logger.error(f"Error processing uploaded file: {e}", exc_info=True)
         st.error(f"Failed to process uploaded file: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# View Transcription Section
# ─────────────────────────────────────────────────────────────────────────────

def render_view_transcription_section(
    azure_key: Optional[str], endpoint: Optional[str], api_ver: Optional[str], model_name: Optional[str], asr_info: str
):
    st.subheader("🔍 View Existing Transcription")
    wav_file = st.file_uploader("Pick a WAV file", type=["wav"])
    if not wav_file:
        return

    try:
        p = Path(config["CACHE_DIR"] / wav_file.name)
        p.write_bytes(wav_file.read())

        # Determine transcription key based on sidebar ASR selection
        transcription_key = "vosk_small" # Default
        model_details = None
        if asr_info:
            if asr_info.startswith("whisper:"):
                transcription_key = "local_whisper"
                model_details = asr_info # e.g., "whisper:tiny"
            elif Path(asr_info).is_dir(): # Check if it's a valid dir path for Vosk
                transcription_key = "vosk_model"
                model_details = asr_info
            # Add elif for specific vosk keys if needed

        with st.spinner("Transcribing audio..."):
            if transcription_key == "vosk_model" and model_details:
                txt = transcribe_audio(str(p), transcription_key, model_path=model_details)
            elif transcription_key == "local_whisper":
                 txt = transcribe_audio(str(p), model_details)
            else:
                txt = transcribe_audio(str(p), transcription_key) # Default vosk_small

        st.subheader("Transcription")
        st.text_area("Audio Transcript", txt, height=200, key="view_transcription")

    except Exception as e:
         logger.error(f"Error viewing transcription for {wav_file.name}: {e}", exc_info=True)
         st.error(f"Failed to view transcription: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# ASR Model Comparison Section
# ─────────────────────────────────────────────────────────────────────────────

def render_model_comparison_section(asr_info: str): # asr_info here is the *currently selected* one, maybe not needed?
    st.subheader("⚖️ ASR Model Comparison")

    # Get available Vosk models
    mdir = config["MODEL_DIR"]
    vosk_models = []
    if mdir.exists():
        vosk_models = [d.name for d in mdir.iterdir() if d.is_dir()]

    # Define available Whisper models
    whisper_models = ["tiny", "base", "medium"] # Could add large, etc.

    # Model selection columns
    st.markdown("#### Select Models to Compare")
    col_select1, col_select2 = st.columns(2)

    model1_key = None
    model1_display_name = "Model 1"
    with col_select1:
        model1_type = st.radio("Model 1 Type", ["Vosk", "Whisper"], key="model1_type", index=0)
        if model1_type == "Vosk":
            if vosk_models:
                model1_name = st.selectbox("Select Vosk Model", vosk_models, key="model1_vosk")
                model1_key = str(mdir / model1_name) # Store full path
                model1_display_name = f"Vosk ({model1_name})"
            else:
                st.warning("No Vosk models found in the model directory.")
        else: # Whisper
            model1_size = st.selectbox("Select Whisper Size", whisper_models, key="model1_whisper")
            model1_key = f"whisper:{model1_size}"
            model1_display_name = f"Whisper ({model1_size})"

    model2_key = None
    model2_display_name = "Model 2"
    with col_select2:
        model2_type = st.radio("Model 2 Type", ["Vosk", "Whisper"], key="model2_type", index=1) # Default to Whisper
        if model2_type == "Vosk":
            if vosk_models:
                model2_name = st.selectbox("Select Vosk Model", vosk_models, key="model2_vosk", index=min(1, len(vosk_models)-1) if vosk_models else 0) # Avoid index error
                model2_key = str(mdir / model2_name) # Store full path
                model2_display_name = f"Vosk ({model2_name})"
            else:
                st.warning("No Vosk models found in the model directory.")
        else: # Whisper
            model2_size = st.selectbox("Select Whisper Size", whisper_models, key="model2_whisper", index=1) # Default to base
            model2_key = f"whisper:{model2_size}"
            model2_display_name = f"Whisper ({model2_size})"

    # File uploader for audio to compare
    wav_file = st.file_uploader("Choose a WAV file to compare", type=["wav"], key="compare_uploader")
    if not wav_file or not model1_key or not model2_key:
        st.info("Please select two models and upload a WAV file to compare.")
        return

    # Process the file and run comparison
    if st.button("Run Comparison", key="run_compare_btn"):
        try:
            with st.spinner("Processing audio for comparison..."):
                path = Path(config["CACHE_DIR"] / f"compare_{wav_file.name}")
                path.write_bytes(wav_file.read())
                path_str = str(path)

                # Transcribe with selected models
                model1_txt = ""
                if model1_key.startswith("whisper:"):
                    model1_txt = transcribe_audio(path_str, model1_key)
                elif Path(model1_key).is_dir(): # Vosk path
                    model1_txt = transcribe_audio(path_str, "vosk_model", model_path=model1_key)

                model2_txt = ""
                if model2_key.startswith("whisper:"):
                    model2_txt = transcribe_audio(path_str, model2_key)
                elif Path(model2_key).is_dir(): # Vosk path
                    model2_txt = transcribe_audio(path_str, "vosk_model", model_path=model2_key)

            # Display comparison results
            col_res1, col_res2 = st.columns(2)
            with col_res1:
                st.subheader(model1_display_name)
                st.text_area("Transcript", model1_txt, height=200, key="comparison_model1_text")
                wc1 = len(model1_txt.split())
                st.caption(f"Word count: {wc1}")

            with col_res2:
                st.subheader(model2_display_name)
                st.text_area("Transcript", model2_txt, height=200, key="comparison_model2_text")
                wc2 = len(model2_txt.split())
                st.caption(f"Word count: {wc2}")

            # Additional comparison metrics
            st.subheader("Comparison Metrics")
            wc_diff = abs(wc1 - wc2)
            wc_diff_percent = (wc_diff / max(wc1, wc2, 1)) * 100 # Avoid division by zero

            st.markdown(f"""
            | Metric     | {model1_display_name} | {model2_display_name} | Difference |
            |------------|-----------------------|-----------------------|------------|
            | Word Count | {wc1}                 | {wc2}                 | {wc_diff} ({wc_diff_percent:.1f}%) |
            """)

            # Highlight which model has longer transcript
            if wc1 > wc2:
                st.info(f"{model1_display_name} produced a longer transcript by {wc_diff} words ({wc_diff_percent:.1f}%).")
            elif wc2 > wc1:
                st.info(f"{model2_display_name} produced a longer transcript by {wc_diff} words ({wc_diff_percent:.1f}%).")
            else:
                st.success("Both models produced the same word count.")

        except Exception as e:
             logger.error(f"Error during model comparison: {e}", exc_info=True)
             st.error(f"Comparison failed: {e}")
