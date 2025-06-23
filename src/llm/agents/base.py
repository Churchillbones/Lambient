from __future__ import annotations

"""Abstract base class for pipeline agents."""

from abc import ABC, abstractmethod
from typing import Any

from core.interfaces.llm_service import ILLMProvider

__all__ = ["Agent"]


class Agent(ABC):
    """Common interface for all specialized LLM agents."""

    def __init__(self, provider: ILLMProvider) -> None:
        self._provider = provider

    # ------------------------------------------------------------------
    @property
    @abstractmethod
    def name(self) -> str:  # noqa: D401
        """Human-readable agent name."""

    # ------------------------------------------------------------------
    @property
    @abstractmethod
    def system_prompt(self) -> str:  # noqa: D401
        """Prompt describing the agent role (passed as *system*)."""

    # ------------------------------------------------------------------
    async def __call__(self, input_text: str, *, context: str | None = None, expect_json: bool = False) -> str:  # noqa: D401
        """Invoke the agent and return raw response text."""

        user_prompt = input_text if context is None else f"Context:\n{context}\n\n{input_text}"
        return await self._provider.generate_completion(
            user_prompt,
            system_prompt=self.system_prompt,
            is_json_output_expected=expect_json,
        ) 