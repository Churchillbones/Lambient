from __future__ import annotations

import asyncio
import logging
from typing import List, Callable

from core.container import global_container
from core.factories.llm_factory import LLMProviderFactory
from core.exceptions import ConfigurationError

from ..utils.token import count as _count_tokens, chunk as _chunk_transcript

logger = logging.getLogger("ambient_scribe")


class TokenManager:  # noqa: D401
    """High-level helpers for token counting, chunking and long-note generation."""

    # ------------------------------------------------------------------
    @staticmethod
    def count(text: str, model: str = "gpt-4o") -> int:  # noqa: D401
        return _count_tokens(text, model)

    # ------------------------------------------------------------------
    @staticmethod
    def chunk(text: str, max_chunk_tokens: int = 2048, model: str = "gpt-4o") -> List[str]:  # noqa: D401
        return _chunk_transcript(text, max_chunk_tokens, model)

    # ------------------------------------------------------------------
    @staticmethod
    def build_note_chunked(
        transcript: str,
        prompt_template: str,
        *,
        azure_endpoint: str,
        azure_api_key: str,
        deployment_name: str,
        api_version: str,
        model: str = "gpt-4o",
    ) -> str:  # noqa: D401
        """Generate note from *transcript* using chunk-based strategy."""

        provider = global_container.resolve(LLMProviderFactory).create(
            "azure_openai",
            api_key=azure_api_key,
            endpoint=azure_endpoint,
            model_name=deployment_name,
            api_version=api_version,
        )

        def _complete(p: str) -> str:
            try:
                return asyncio.run(provider.generate_completion(p))
            except Exception as exc:  # noqa: BLE001
                raise ConfigurationError(f"Provider completion failed: {exc}") from exc

        # Reserve space for answer and prompt
        reserve_tokens = 1000
        tmpl_tokens = TokenManager.count(prompt_template, model)
        max_in_tokens = 4096 - reserve_tokens - tmpl_tokens

        chunks = TokenManager.chunk(transcript, max_in_tokens, model)
        if not chunks:
            return "Error: No transcript content to process."

        if len(chunks) == 1:
            return _complete(prompt_template.replace("{transcript}", chunks[0]))

        chunk_notes: list[str] = []
        chunk_prompt = (
            prompt_template
            + "\nNote: This is part {part_num} of {total_parts} of the transcript. Focus on extracting key information from this section only."
        )

        for idx, chunk in enumerate(chunks):
            try:
                note_prompt = (
                    chunk_prompt.replace("{transcript}", chunk)
                    .replace("{part_num}", str(idx + 1))
                    .replace("{total_parts}", str(len(chunks)))
                )
                chunk_notes.append(_complete(note_prompt))
            except Exception as exc:
                logger.error("Error processing chunk %s: %s", idx + 1, exc)
                chunk_notes.append(f"[Error processing chunk {idx + 1}: {exc}]")

        combined = "\n\n".join(chunk_notes)
        integrate_prompt = (
            "You have been given multiple sections of clinical notes derived from a longer transcript.\n"
            "Please integrate these sections into one cohesive clinical note, removing any redundancy:\n\n"
            f"{combined}\n\nPlease provide a single, integrated clinical note from all these sections."
        )

        try:
            return _complete(integrate_prompt)
        except Exception as exc:
            logger.error("Error integrating chunks: %s", exc)
            return "\n\n--- SECTION BREAK ---\n\n".join(chunk_notes)

    # ------------------------------------------------------------------
    @staticmethod
    def build_note_two_stage(
        transcript: str,
        prompt_template: str,
        *,
        azure_endpoint: str,
        azure_api_key: str,
        deployment_name: str,
        api_version: str,
        model: str = "gpt-4o",
    ) -> str:  # noqa: D401
        """Generate note via two-stage summarize-then-compose approach."""

        provider = global_container.resolve(LLMProviderFactory).create(
            "azure_openai",
            api_key=azure_api_key,
            endpoint=azure_endpoint,
            model_name=deployment_name,
            api_version=api_version,
        )

        _complete: Callable[[str], str] = lambda p: asyncio.run(provider.generate_completion(p))  # type: ignore

        if TokenManager.count(transcript, model) < 2500:
            return _complete(prompt_template.replace("{transcript}", transcript))

        # Stage-1 summarise in smaller chunks
        chunks = TokenManager.chunk(transcript, 2000, model)
        summary_prompt = (
            "Extract the key medical information from this transcript section, including:\n"
            "- Chief complaints\n- Symptoms discussed\n- Relevant patient history mentioned\n- Assessment points\n"
            "- Treatment plans or recommendations\n- Follow-up instructions\n\nTRANSCRIPT SECTION:\n{section}\n\n"
            "Provide a concise summary with the most important clinical details only."
        )

        summaries: list[str] = []
        for idx, chunk in enumerate(chunks):
            try:
                summaries.append(_complete(summary_prompt.replace("{section}", chunk)))
            except Exception as exc:
                logger.error("Error summarizing section %s: %s", idx + 1, exc)
                summaries.append(f"[Error summarizing section {idx + 1}: {exc}]")

        combined_summaries = "\n\n--- SECTION SUMMARY ---\n\n".join(summaries)
        final_prompt = (
            "You are generating a clinical note based on summaries extracted from a patient encounter.\n"
            "These summaries contain the key information from the full transcript.\n\n"
            f"{prompt_template.replace('{transcript}', 'the summarized encounter information')}\n\n"
            "SUMMARIZED ENCOUNTER INFORMATION:\n"
            f"{combined_summaries}\n\nCreate a complete, well-structured clinical note based on these summaries."
        )

        return _complete(final_prompt) 