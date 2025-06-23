"""Sample transcription data for testing."""

from typing import Dict, List, Any


# Sample medical transcripts
SAMPLE_TRANSCRIPTS = {
    "primary_care_visit": """
    Doctor: Good morning, Mrs. Johnson. What brings you in today?
    Patient: Hi Dr. Smith. I've been having these headaches for about two weeks now.
    Doctor: Can you describe the headaches for me? Where do you feel them?
    Patient: They're mostly on the right side of my head, kind of throbbing.
    Doctor: How often are you getting them?
    Patient: Pretty much every day, sometimes twice a day.
    Doctor: Are there any triggers you've noticed?
    Patient: They seem worse when I'm stressed at work or haven't slept well.
    Doctor: Any nausea or sensitivity to light?
    Patient: Yes, the light bothers me a lot when I have one.
    Doctor: Have you tried any medications?
    Patient: Just ibuprofen, but it doesn't seem to help much.
    Doctor: Based on what you're telling me, this sounds like it could be migraines. Let me examine you and we'll discuss treatment options.
    """,
    
    "cardiology_consultation": """
    Doctor: Mr. Rodriguez, thank you for coming in. I've reviewed your EKG and the results from your primary care doctor.
    Patient: Thank you, Doctor. I'm a bit worried about my heart.
    Doctor: I understand your concern. Tell me about the chest pain you've been experiencing.
    Patient: It usually happens when I'm walking upstairs or doing yard work. It feels like pressure.
    Doctor: How long does it typically last?
    Patient: Maybe five to ten minutes, then it goes away when I rest.
    Doctor: Any shortness of breath with it?
    Patient: Yes, I get winded pretty easily now.
    Doctor: Are you taking your blood pressure medication regularly?
    Patient: Most of the time, yes. Sometimes I forget.
    Doctor: We need to do a stress test to get a better picture of what's happening with your heart.
    """,
    
    "pediatric_visit": """
    Doctor: Hi there, Tommy! How are you feeling today?
    Mother: He's been running a fever for three days and has a sore throat.
    Doctor: What's his temperature been?
    Mother: Around 101 to 102 degrees.
    Doctor: Tommy, can you open your mouth wide for me? Does it hurt to swallow?
    Tommy: Yes, it hurts a lot.
    Doctor: I can see his throat is quite red and swollen. Any other symptoms?
    Mother: He's been tired and not eating much.
    Doctor: Has he been around anyone else who's been sick?
    Mother: His sister had strep throat last week.
    Doctor: I'm going to do a quick strep test. This might feel a little uncomfortable, Tommy, but it will be over quickly.
    """,
    
    "mental_health_session": """
    Therapist: How have you been feeling since our last session?
    Patient: It's been a difficult week. The anxiety has been pretty constant.
    Therapist: Can you tell me more about what the anxiety feels like?
    Patient: It's like this tight feeling in my chest, and my mind just races with worry.
    Therapist: What kinds of things are you worrying about?
    Patient: Work mostly, and relationships. I keep thinking I'm going to mess everything up.
    Therapist: Have you been using the breathing techniques we practiced?
    Patient: I try to, but sometimes I forget when I'm really anxious.
    Therapist: That's completely normal. Let's review those techniques again and talk about some additional coping strategies.
    """,
    
    "emergency_room_triage": """
    Nurse: What brought you to the emergency room today?
    Patient: I fell off my bike and hurt my wrist really bad.
    Nurse: When did this happen?
    Patient: About two hours ago.
    Nurse: Can you move your fingers?
    Patient: A little bit, but it really hurts.
    Nurse: On a scale of one to ten, how would you rate your pain?
    Patient: About an eight or nine.
    Nurse: Any numbness or tingling?
    Patient: My pinky finger feels kind of numb.
    Nurse: We'll need to get an X-ray to check for fractures. Let me get you some ice for now.
    """,
    
    "surgical_consultation": """
    Surgeon: I've reviewed your imaging studies, and we need to discuss surgery for your gallbladder.
    Patient: Is it serious?
    Surgeon: You have gallstones that are causing inflammation. The recommended treatment is laparoscopic cholecystectomy.
    Patient: What does that involve?
    Surgeon: It's minimally invasive surgery using small incisions. We remove the gallbladder through tiny ports.
    Patient: How long is the recovery?
    Surgeon: Most patients go home the same day or after an overnight stay. Full recovery is typically two to three weeks.
    Patient: Are there any risks?
    Surgeon: All surgery has risks, but this is a very common procedure with a high success rate.
    """
}

# Sample cleaned transcripts (what should result after cleaning)
CLEANED_TRANSCRIPTS = {
    "primary_care_visit": """
    Doctor: Good morning, Mrs. Johnson. What brings you in today?
    Patient: Hi Dr. Smith. I've been having these headaches for about two weeks now.
    Doctor: Can you describe the headaches for me? Where do you feel them?
    Patient: They're mostly on the right side of my head, kind of throbbing.
    Doctor: How often are you getting them?
    Patient: Pretty much every day, sometimes twice a day.
    Doctor: Are there any triggers you've noticed?
    Patient: They seem worse when I'm stressed at work or haven't slept well.
    Doctor: Any nausea or sensitivity to light?
    Patient: Yes, the light bothers me a lot when I have one.
    Doctor: Have you tried any medications?
    Patient: Just ibuprofen, but it doesn't seem to help much.
    Doctor: Based on what you're telling me, this sounds like it could be migraines. Let me examine you and we'll discuss treatment options.
    """,
}

# Sample medical entities that should be extracted
SAMPLE_MEDICAL_ENTITIES = {
    "primary_care_visit": {
        "symptoms": [
            "headaches",
            "throbbing pain",
            "sensitivity to light",
            "nausea"
        ],
        "conditions": [
            "migraines"
        ],
        "medications": [
            "ibuprofen"
        ],
        "triggers": [
            "stress",
            "lack of sleep"
        ],
        "location": [
            "right side of head"
        ],
        "duration": [
            "two weeks",
            "every day"
        ],
        "severity": [
            "doesn't help much"
        ]
    },
    
    "cardiology_consultation": {
        "symptoms": [
            "chest pain",
            "pressure",
            "shortness of breath",
            "winded easily"
        ],
        "conditions": [
            "cardiac concern"
        ],
        "medications": [
            "blood pressure medication"
        ],
        "triggers": [
            "walking upstairs",
            "yard work"
        ],
        "duration": [
            "five to ten minutes"
        ],
        "procedures": [
            "stress test",
            "EKG"
        ]
    }
}

# Sample SOAP notes
SAMPLE_SOAP_NOTES = {
    "primary_care_visit": """
    SOAP Note - Primary Care Visit

    Subjective:
    Patient is a female presenting with a chief complaint of headaches persisting for approximately two weeks. She describes the headaches as throbbing in nature, primarily located on the right side of her head. The headaches occur daily, sometimes twice per day. Patient reports triggers include work-related stress and poor sleep. Associated symptoms include photophobia and nausea. Patient has tried ibuprofen with minimal relief.

    Objective:
    Patient appears comfortable but concerned. Vital signs stable. Neurological examination pending.

    Assessment:
    Based on the patient's presentation, symptoms are consistent with migraine headaches. Differential diagnosis includes tension headaches and cluster headaches.

    Plan:
    1. Complete neurological examination
    2. Discuss migraine management strategies
    3. Consider prophylactic medication if episodes continue
    4. Patient education on trigger avoidance
    5. Follow-up in 2-3 weeks
    """,
    
    "cardiology_consultation": """
    SOAP Note - Cardiology Consultation

    Subjective:
    Patient is a male presenting with exertional chest pain and dyspnea. Pain is described as pressure-like, occurring with activities such as climbing stairs or yard work. Symptoms resolve with rest within 5-10 minutes. Patient has a history of hypertension and admits to occasional non-compliance with antihypertensive medications.

    Objective:
    EKG reviewed showing [findings]. Patient appears mildly anxious but hemodynamically stable.

    Assessment:
    Symptoms suggestive of stable angina. Differential includes unstable angina and myocardial ischemia.

    Plan:
    1. Stress test to evaluate for coronary artery disease
    2. Medication compliance counseling
    3. Lifestyle modifications discussion
    4. Follow-up based on stress test results
    """
}

# Sample note summaries
SAMPLE_SUMMARIES = {
    "primary_care_visit": "45-year-old female with 2-week history of right-sided throbbing headaches, daily occurrence, with photophobia and nausea. Symptoms consistent with migraines. Plan includes examination and migraine management discussion.",
    
    "cardiology_consultation": "Male patient with exertional chest pain and dyspnea, symptoms resolve with rest. History of hypertension with medication non-compliance. Plan for stress testing to evaluate for coronary artery disease."
}

# Configuration data for testing
CONFIGURATION_TEST_DATA = {
    "valid_config": {
        "azure": {
            "openai": {
                "endpoint": "https://test.openai.azure.com/",
                "api_key": "test_api_key_123",
                "deployment_name": "gpt-35-turbo",
                "api_version": "2023-12-01-preview"
            },
            "speech": {
                "subscription_key": "test_speech_key_456",
                "region": "eastus",
                "language": "en-US"
            }
        },
        "vosk": {
            "model_path": "/path/to/vosk/model",
            "language": "en"
        },
        "ollama": {
            "base_url": "http://localhost:11434",
            "model": "llama2"
        }
    },
    
    "invalid_config": {
        "azure": {
            "openai": {
                "endpoint": "not_a_valid_url",
                "api_key": "",
                "deployment_name": "",
                "api_version": "invalid_version"
            }
        }
    }
}

# Test audio file specifications
AUDIO_FILE_SPECS = {
    "short_clip": {
        "duration": 5.0,  # seconds
        "sample_rate": 16000,
        "channels": 1,
        "format": "wav",
        "size_bytes": 160000  # approximate
    },
    
    "medium_clip": {
        "duration": 30.0,
        "sample_rate": 16000,
        "channels": 1,
        "format": "wav",
        "size_bytes": 960000
    },
    
    "long_clip": {
        "duration": 300.0,  # 5 minutes
        "sample_rate": 16000,
        "channels": 1,
        "format": "wav",
        "size_bytes": 9600000
    }
}

# Expected API responses for testing
MOCK_API_RESPONSES = {
    "azure_openai_chat_completion": {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "created": 1677652288,
        "model": "gpt-35-turbo",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "This is a mock response from Azure OpenAI."
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 9,
            "completion_tokens": 12,
            "total_tokens": 21
        }
    },
    
    "azure_speech_recognition": {
        "RecognitionStatus": "Success",
        "DisplayText": "This is a test transcription result.",
        "Offset": 1000000,
        "Duration": 50000000,
        "NBest": [
            {
                "Confidence": 0.9123,
                "Lexical": "this is a test transcription result",
                "ITN": "This is a test transcription result",
                "MaskedITN": "This is a test transcription result",
                "Display": "This is a test transcription result."
            }
        ]
    },
    
    "ollama_generate": {
        "model": "llama2",
        "created_at": "2023-08-04T19:22:45.499127Z",
        "response": "This is a mock response from Ollama.",
        "done": True,
        "context": [1, 2, 3, 4, 5],
        "total_duration": 5589157167,
        "load_duration": 3013701500,
        "prompt_eval_count": 46,
        "prompt_eval_duration": 1160282000,
        "eval_count": 113,
        "eval_duration": 1408557000
    }
}

# Performance benchmark expectations
PERFORMANCE_BENCHMARKS = {
    "streaming": {
        "max_latency_ms": 500,
        "max_session_creation_ms": 100,
        "max_memory_mb": 200,
        "min_throughput_chunks_per_sec": 10
    },
    
    "transcription": {
        "max_processing_time_ratio": 0.3,  # Should process faster than real-time
        "max_memory_per_minute_mb": 50,
        "min_accuracy_threshold": 0.8
    },
    
    "note_generation": {
        "max_response_time_ms": 5000,
        "min_note_length_chars": 200,
        "max_token_usage": 1000
    }
}


def get_sample_transcript(transcript_type: str) -> str:
    """Get a sample transcript by type."""
    return SAMPLE_TRANSCRIPTS.get(transcript_type, SAMPLE_TRANSCRIPTS["primary_care_visit"])


def get_sample_entities(transcript_type: str) -> Dict[str, List[str]]:
    """Get sample medical entities for a transcript type."""
    return SAMPLE_MEDICAL_ENTITIES.get(transcript_type, SAMPLE_MEDICAL_ENTITIES["primary_care_visit"])


def get_sample_soap_note(transcript_type: str) -> str:
    """Get a sample SOAP note by type."""
    return SAMPLE_SOAP_NOTES.get(transcript_type, SAMPLE_SOAP_NOTES["primary_care_visit"])


def get_mock_api_response(service: str, endpoint: str) -> Dict[str, Any]:
    """Get mock API response for testing."""
    key = f"{service}_{endpoint}"
    return MOCK_API_RESPONSES.get(key, {})


def get_performance_benchmark(category: str) -> Dict[str, Any]:
    """Get performance benchmark expectations."""
    return PERFORMANCE_BENCHMARKS.get(category, {})