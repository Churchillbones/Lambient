from __future__ import annotations

import asyncio
import logging
import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from pydantic import BaseModel

from src.asr.transcription import transcribe_audio
from src.asr.exceptions import TranscriptionError
from src.llm.routing import generate_note_router
from src.llm.prompts import load_prompt_templates

logger = logging.getLogger("ambient_scribe")

router = APIRouter()


class NoteRequest(BaseModel):
    transcript: str
    template: str = ""
    api_key: str | None = None
    endpoint: str | None = None
    api_version: str | None = None
    model: str | None = None
    use_local: bool = False
    local_model: str = ""
    patient_data: dict | None = None
    use_agent_pipeline: bool = False
    agent_settings: dict | None = None


@router.get("/templates")
def list_templates():
    """Return available prompt templates."""
    return load_prompt_templates()


@router.post("/transcribe")
async def transcribe_endpoint(
    file: UploadFile = File(...),
    model: str = Form("vosk"),
    language: str = Form("en-US"),
    model_path: str | None = Form(None),
):
    """Transcribe the uploaded audio file using the requested ASR engine."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    logger.info(
        "Transcribe request: model=%s, model_path=%s, file=%s",
        model,
        model_path,
        file.filename,
    )

    try:
        transcript = await transcribe_audio(tmp_path, model, model_path=model_path, language=language)

        logger.info("Transcription result length: %d", len(transcript))
        return {"transcript": transcript}
    except TranscriptionError as te:
        logger.warning("Transcription failed: %s", te)
        raise HTTPException(status_code=400, detail=str(te))
    finally:
        Path(tmp_path).unlink(missing_ok=True)


@router.post("/notes")
async def generate_note_endpoint(req: NoteRequest):
    """Generate a structured clinical note from a transcript."""
    note, _ = await generate_note_router(
        req.transcript,
        api_key=req.api_key,
        azure_endpoint=req.endpoint,
        azure_api_version=req.api_version,
        azure_model_name=req.model,
        prompt_template=req.template,
        use_local=req.use_local,
        local_model=req.local_model,
        patient_data=req.patient_data,
        use_agent_pipeline=req.use_agent_pipeline,
        agent_settings=req.agent_settings,
        progress_callback=None,
    )
    return {"note": note} 