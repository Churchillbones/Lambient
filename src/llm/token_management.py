"""
token_management.py
Handles token management for OpenAI API calls to stay within token limits.

This module provides two approaches for handling large transcriptions that might exceed
the token limits of the OpenAI API:

1. Chunk Processing (generate_note_from_chunked_transcript):
   - Splits the transcript into manageable chunks
   - Processes each chunk independently
   - Combines the results into a cohesive note

2. Two-Stage Summarization (generate_note_with_two_stage_summarization):
   - First extracts key information from transcript sections
   - Then combines these summaries into a cohesive note

The approach can be configured using the TOKEN_MANAGEMENT_APPROACH environment variable ('chunking' or 'two_stage').

Both approaches use the tiktoken library for accurate token counting.
"""

import asyncio
from typing import List, Dict, Any, Optional
import logging

from core.bootstrap import container
from core.factories.llm_factory import LLMProviderFactory
from core.exceptions import ConfigurationError
from core.interfaces.token_service import ITokenService

from .utils import token as token_utils

# Standardized logger
logger = logging.getLogger("ambient_scribe")

_token_service: ITokenService = container.resolve(ITokenService)

# DEPRECATED MODULE – logic moved to `src.llm.services.token_manager`.
# Importing here for backward compatibility.

from warnings import warn as _warn

from .services.token_manager import TokenManager as _TM

_warn(
    "'src.llm.token_management' is deprecated. Use 'src.llm.services.token_manager' instead.",
    DeprecationWarning,
    stacklevel=2,
)

count_tokens = _TM.count  # type: ignore
chunk_transcript = _TM.chunk  # type: ignore
generate_note_from_chunked_transcript = _TM.build_note_chunked  # type: ignore
generate_note_with_two_stage_summarization = _TM.build_note_two_stage  # type: ignore

def generate_coding_and_review(
    note: str,
    azure_endpoint: str,
    azure_api_key: str,
    deployment_name: str,
    api_version: str,
    model: str = "gpt-4o"
) -> str:
    """
    Use GPT to generate E/M, ICD-10, SNOMED, CPT, risk, SDOH, alternate dx, and payer review based on a clinical note.
    The prompt is tailored for insurance-defensible coding and payer review.
    """
    if not note:
        return "No note provided for coding analysis."
    prompt = f"""
E/M Coding: on separate lines recommend insurance-defensible e/m coding based on documented a) mdm and b) time.  Briefly summarize justification for each as specifically documented in the note.   Time coding for established patients: total 10-19 minutes = 99212, 20-29 minutes = 99213, 30-39 minutes = 99214, and 40-54 minutes = 99215.  If greater than 54 minutes, code 99417 may be added for each additional fifteen minutes.  For new patients, time coding is 15-29 minutes = 99202, 30-44 minutes = 99203, 45-59 minutes = 99204, and 60-74 minutes = 99205. If greater than 74 minutes, code 99417 may be added for each additional fifteen minutes. 3) Recommend icd-10 and snomed codes, placing both on the same line for each separate condition. Include BOTH codes AND DESCRIPTIVE TEXT FOR EACH.  Ensure in each each match of icd-10 and snomed codes that the identifying text for icd-10 matches the text for snomed.  Specifically identify and note conditions considered high-risk for coding. Include only icd-10 and snomed codes that are mentioned in the text of the note, NOT in an inserted problem list.  Include items from the problem list ONLY if they are ALSO discussed in the note.  4) Recommend CPT codes for any noted procedures.  For EKGs please specifically include codes for test performance and provider reading.  Specifically evaluate then include, only when clearly relevant, potential CPT procedure modifiers (25, 59, 76 or 77).  Specifically document why such modifiers are relevant to this encounter.  Especially ensure CPT modifier 59 is identified if procedures were performed at different sites during the encounter.  5) Identify comorbidities and risk adjustment codes.  6) Review and identify any relevant social determinants of health codes (Z55-Z65). 7) Summarize at least four alternate diagnoses considered and explain why they weren't actioned.  8) Review your responses 1-7 from a payer perspective, noting whether a payer might dispute e/m or diagnosis codes due to insufficient documentation in the note.  Also suggest what might be improved in the note to counter the payer's perspective.\n\nCLINICAL NOTE:\n{note}\n"""
    provider = container.resolve(LLMProviderFactory).create(
        "azure_openai",
        api_key=azure_api_key,
        endpoint=azure_endpoint,
        model_name=deployment_name,
        api_version=api_version,
    )
    try:
        return asyncio.run(provider.generate_completion(prompt))
    except Exception as e:
        logger.error(f"Error generating coding analysis: {str(e)}")
        return f"Error generating coding analysis: {str(e)}"
