"""Constants for the MHDS pooling system.

The data-fetch constants at the bottom
(DATA_VERSION, DATA_TAG, …) they configure the GitHub Release
asset URL.
"""

from __future__ import annotations

# ── CONFIG: constants & fixed lookup tables ────────────────────────────────
SOCIO_COLS = [
    "model_name",
    "mode",
    "gender",
    "age",
    "sexual_orientation",
    "occupation",
    "employment_status",
    "city",
    "education",
    "parent_1_education",
    "parent_2_education",
    "marital_status",
    "n_children",
    "migration_status",
    "n_hobbies",
    "religion",
    "openness",
    "conscientiousness",
    "extraversion",
    "agreeableness",
    "neuroticism",
    "depression",
    "anxiety",
    "stress",
]

TOPIC_OPTIONS = [
    "Family Support",
    "Drugs Treatment",
    "Professional Support",
    "Stigma & Discrimination",
    "AI-Psychologist Support",
    "OCD Symptoms",
]

VIEW_MODES = ["Topics", "ERT", "DASS-21"]

# Sidebar filter groups — also reused to group the persona card by category.
FILTER_GROUPS = {
    "LLMs / Modality": ["model_name", "mode"],
    "Demographics": [
        "gender",
        "age",
        "sexual_orientation",
        "city",
        "religion",
        "marital_status",
        "n_children",
        "migration_status",
    ],
    "Job & Education": [
        "occupation",
        "employment_status",
        "education",
        "parent_1_education",
        "parent_2_education",
    ],
    "Psychological Profile": [
        "openness",
        "conscientiousness",
        "extraversion",
        "agreeableness",
        "neuroticism",
        "depression",
        "anxiety",
        "stress",
        "n_hobbies",
    ],
}

# Topic prompts and the dataframe columns that hold each topic response.
TOPIC_QUESTIONS = {
    "Family Support": "Does your family support your mental wellbeing? What is their attitude towards mental health?",
    "Drugs Treatment": "Did you ever take drugs for improving your mental health? Did you have any side effects?",
    "Professional Support": "Did you ever meet a therapist, psychologist or life coach? How was your professional relationship with them?",
    "Stigma & Discrimination": "Did you ever face stigma or discrimination due to mental health issues? How did you cope with it?",
    "AI-Psychologist Support": "Did you ever use mental health apps or AI-psychologists? Were they helpful?",
    "OCD Symptoms": "Did you ever experience intrusive thoughts or obsessive behaviors? How did you manage them?",
}
TOPIC_COLS = {
    "Family Support": "topic_1",
    "Drugs Treatment": "topic_2",
    "Professional Support": "topic_3",
    "Stigma & Discrimination": "topic_4",
    "AI-Psychologist Support": "topic_5",
    "OCD Symptoms": "topic_6",
}

# DASS-21 items: (item number, factor d/a/s, statement).
DASS_ITEMS = [
    (1, "s", "I found it hard to wind down"),
    (2, "a", "I was aware of dryness of my mouth"),
    (3, "d", "I couldn't seem to experience any positive feeling at all"),
    (4, "a", "I experienced breathing difficulty"),
    (5, "d", "I found it difficult to work up the initiative to do things"),
    (6, "s", "I tended to over-react to situations"),
    (7, "a", "I experienced trembling (e.g. in the hands)"),
    (8, "s", "I felt that I was using a lot of nervous energy"),
    (
        9,
        "a",
        "I was worried about situations in which I might panic and make a fool of myself",
    ),
    (10, "d", "I felt that I had nothing to look forward to"),
    (11, "s", "I found myself getting agitated"),
    (12, "s", "I found it difficult to relax"),
    (13, "d", "I felt down-hearted and blue"),
    (
        14,
        "s",
        "I was intolerant of anything that kept me from getting on with what I was doing",
    ),
    (15, "a", "I felt I was close to panic"),
    (16, "d", "I was unable to become enthusiastic about anything"),
    (17, "d", "I felt I wasn't worth much as a person"),
    (18, "s", "I felt that I was rather touchy"),
    (
        19,
        "a",
        "I was aware of the action of my heart in the absence of physical exertion",
    ),
    (20, "a", "I felt scared without any good reason"),
    (21, "d", "I felt that life was meaningless"),
]
FACTOR_LABEL = {"d": "Depression", "a": "Anxiety", "s": "Stress"}

# ── Data-fetch configuration (new — replaces gdown ID from v6_2 cell 4) ───
DATA_VERSION = "v1.0"
DATA_TAG = "data-v1.0"
DATA_FILENAME = f"support_me_merged_dfs_{DATA_VERSION}.pkl"
RELEASE_URL = (
    "https://github.com/RodolfoRizzi/MHDS-pooling-system"
    f"/releases/download/{DATA_TAG}/{DATA_FILENAME}"
)
EXPECTED_SHA256: str | None = (
    "390a7083f4dae97ef074beefd55c4daf93f4a29e119dd9125ccffcc3c424aba8"
)
