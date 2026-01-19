"""
AI prompt templates for code analysis.
"""

SYSTEM_PROMPT_CODE_ANALYSIS = """You are a building code analyst assistant. Your task is to analyze inspection photos and find the EXACT code reference in the provided document text.

CRITICAL RULES:
1. You MUST ONLY cite references that ACTUALLY APPEAR in the document text provided below
2. DO NOT use your general knowledge of building codes
3. DO NOT make up or hallucinate code references
4. If you cannot find a relevant reference in the provided text, say REFERENCE: NOT_FOUND
5. Search the document text carefully for section numbers, table numbers, or figure numbers

You will be given:
- An inspection photo
- A description of the issue
- The ACTUAL TEXT from the relevant code document(s)

Your job is to SEARCH the provided document text and find the matching code reference."""


USER_PROMPT_TEMPLATE = """Analyze this inspection photo and find the relevant building code reference.

**Issue Description:** {description}
**Location:** {location}

**IMPORTANT: Below is the ACTUAL TEXT from the code document(s). You MUST find your answer in this text. Do NOT use external knowledge.**

=== BEGIN CODE DOCUMENT TEXT ===
{pdf_content}
=== END CODE DOCUMENT TEXT ===

Instructions:
1. Read through the document text above carefully
2. Find the section, table, or figure that applies to the issue shown in the photo
3. The reference MUST exist in the text above - do not make one up

Respond in this EXACT format:
MATCH_TYPE: [Section|Table|Figure]
REFERENCE: [The exact reference number found in the text, e.g., R703.8 or Table R602.3(1)] or NOT_FOUND
CONFIDENCE: [High|Medium|Low]
REASONING: [Quote the relevant text from the document that supports your answer]"""


USER_PROMPT_NO_PDF = """Analyze this inspection photo.

**Issue Description:** {description}
**Location:** {location}

**WARNING: No code document was provided. Please describe what you observe and what type of code section would likely apply, but note that you cannot provide a specific reference without the document.**

Respond in this format:
MATCH_TYPE: Section
REFERENCE: NOT_FOUND
CONFIDENCE: Low
REASONING: [Describe what you see and what type of violation it might be]"""


REANALYSIS_PROMPT_TEMPLATE = """The previous code reference was not found in the document.

**Original Description:** {description}
**Location:** {location}
**Previous Suggestion (NOT FOUND):** {previous_reference}

Please search the document text again more carefully:

=== BEGIN CODE DOCUMENT TEXT ===
{pdf_content}
=== END CODE DOCUMENT TEXT ===

Find a DIFFERENT reference that ACTUALLY EXISTS in the text above.

Respond in this EXACT format:
MATCH_TYPE: [Section|Table|Figure]
REFERENCE: [A reference that EXISTS in the text above] or NOT_FOUND
CONFIDENCE: [High|Medium|Low]
REASONING: [Quote the relevant text]"""


def build_analysis_prompt(description: str, location: str, pdf_content: str = "") -> str:
    """Build the analysis prompt with user inputs and PDF content."""
    if pdf_content and pdf_content.strip():
        return USER_PROMPT_TEMPLATE.format(
            description=description or "No description provided",
            location=location or "No location provided",
            pdf_content=pdf_content
        )
    else:
        return USER_PROMPT_NO_PDF.format(
            description=description or "No description provided",
            location=location or "No location provided"
        )


def build_reanalysis_prompt(
    description: str,
    location: str,
    previous_reference: str,
    pdf_content: str
) -> str:
    """Build prompt for re-analysis after failed verification."""
    return REANALYSIS_PROMPT_TEMPLATE.format(
        description=description,
        location=location,
        previous_reference=previous_reference,
        pdf_content=pdf_content
    )
