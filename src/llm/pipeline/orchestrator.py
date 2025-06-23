from __future__ import annotations

"""Basic orchestrator that wires the new Agent classes together.

The goal is to provide a reusable, declarative way to run a sequence of
agents without depending on the old monolithic `MedicalNoteAgentPipeline`
implementation.  For now it covers the *happy-path* flow used by the UI:

1. TranscriptionCleaner → cleaned transcript
2. MedicalExtractor     → JSON data
3. ClinicalWriter       → draft note
4. QualityReviewer      → optional refinement / score
"""

from typing import Any, Dict, Tuple, Optional, List

from core.interfaces.llm_service import ILLMProvider

from ..agents import (
    Agent,
    TranscriptionCleaner,
    MedicalExtractor,
    ClinicalWriter,
    QualityReviewer,
)

__all__ = ["Orchestrator", "PipelineResult"]

PipelineResult = Tuple[str, Dict[str, Any]]  # final note, metadata


class Orchestrator:  # noqa: D101 – simple orchestrator
    def __init__(
        self,
        provider: ILLMProvider,
        *,
        include_review: bool = True,
        max_iterations: int = 1,
    ) -> None:
        self._provider = provider
        self.include_review = include_review
        self.max_iterations = max_iterations

        # Build default pipeline order
        self.steps: List[Agent] = [
            TranscriptionCleaner(provider),
            MedicalExtractor(provider),
            ClinicalWriter(provider),
        ]
        if include_review:
            self.steps.append(QualityReviewer(provider))

    # ------------------------------------------------------------------
    async def run(self, transcript: str, *, template: str = "SOAP", patient_data: Optional[dict] = None) -> PipelineResult:  # noqa: D401
        metadata: Dict[str, Any] = {
            "template": template,
            "iterations": 0,
            "stages": [],
        }

        # Stage 1: clean transcript
        cleaned = await self.steps[0](transcript)
        metadata["stages"].append({"name": "clean", "length": len(cleaned)})

        # Stage 2: extract
        extracted_json_str = await self.steps[1](cleaned, expect_json=True)

        # Quick sanity-check – if extraction looks empty or not JSON, fallback to simple transcript-based prompt.
        import json, re  # noqa: E402 – local import

        def _is_valid_json(text: str) -> bool:  # noqa: D401
            if not text:
                return False
            # Strip code fences if present
            candidate = text.strip()
            candidate = re.sub(r"^```json|```$", "", candidate.strip(), flags=re.IGNORECASE).strip()
            try:
                json.loads(candidate)
                return True
            except Exception:
                return False

        if not _is_valid_json(extracted_json_str):
            # Fallback: use cleaned transcript directly as context
            extracted_json_str = (
                "{\n  \"transcript\": " + json.dumps(cleaned[:10000]) + "\n}"  # minimal JSON
            )
            metadata["extraction_fallback"] = True
        metadata["stages"].append({"name": "extract", "json_length": len(extracted_json_str)})

        # Stage 3: write
        context_lines = []
        if patient_data:
            for key in ("name", "age", "gender"):
                if key in patient_data:
                    context_lines.append(f"Patient {key.capitalize()}: {patient_data[key]}")
        context = "\n".join(context_lines) if context_lines else None

        draft_note = await self.steps[2](
            f"Generate a complete {template} note using the clinical information below.\n"
            f"Use ALL specific details, findings, and information provided - do not use placeholder text.\n\n"
            f"CLINICAL DATA:\n{extracted_json_str}",
            context=context,
        )
        metadata["stages"].append({"name": "write", "length": len(draft_note)})

        # Stage 4: review / iterate
        final_note = draft_note
        if self.include_review:
            reviewer: QualityReviewer = self.steps[3]  # type: ignore[assignment]
            for i in range(self.max_iterations):
                review_json = await reviewer(
                    f"Review and improve this note if needed:\n\n{final_note}\n\nSOURCE DATA:{extracted_json_str}",
                    expect_json=True,
                )
                import json  # local import to keep top minimal

                review = json.loads(review_json)
                metadata["stages"].append({
                    "name": f"review_{i+1}",
                    "score": review.get("quality_score"),
                    "issues": len(review.get("issues_found", [])),
                })
                final_note = review.get("refined_note", final_note)
                if review.get("quality_score", 0) >= 90:
                    break
                metadata["iterations"] += 1

        return final_note, metadata 