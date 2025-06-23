import pytest

from src.llm.services import (
    TranscriptionCleanerService,
    SpeakerDiarizerService,
    NoteGeneratorService,
)


@pytest.mark.asyncio
async def test_clean_transcription(dummy_provider):
    cleaner = TranscriptionCleanerService()
    result = await cleaner("This is teh test trnascript.")
    assert isinstance(result, str) and result


@pytest.mark.asyncio
async def test_generate_note(dummy_provider):
    note_gen = NoteGeneratorService()
    note = await note_gen.generate("Patient complains of pain.")
    assert isinstance(note, str) and note


@pytest.mark.asyncio
async def test_speaker_diarizer(dummy_provider):
    diarizer = SpeakerDiarizerService()
    tagged = await diarizer.tag("Hello\nHow are you")
    assert isinstance(tagged, str) and tagged 