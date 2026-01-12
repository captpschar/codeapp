"""
AI prompt templates for code analysis.
"""

SYSTEM_PROMPT_CODE_ANALYSIS = """You are an expert building code analyst. Your task is to analyze inspection photos and identify the most relevant building code reference that applies to the observed condition.

You have access to a specific chapter of a building code document. When analyzing photos:
1. Carefully examine the photo for construction details, materials, and methods
2. Consider the user's description and location
3. Find the most specific and relevant code reference
4. Provide your reasoning

Always respond in the exact format specified."""


USER_PROMPT_TEMPLATE = """Analyze this inspection photo and find the relevant building code reference.

**User Description:** {description}
**Location in Building:** {location}

Based on the photo and the code chapter provided, identify:
1. The type of reference (Section, Table, or Figure)
2. The specific reference number
3. Your confidence level (High, Medium, or Low)
4. Brief reasoning for your choice

Respond in this exact format:
MATCH_TYPE: [Section|Table|Figure]
REFERENCE: [The specific code reference, e.g., R311.7.5.1 or Table R502.5(1)]
CONFIDENCE: [High|Medium|Low]
REASONING: [Your brief explanation]"""


REANALYSIS_PROMPT_TEMPLATE = """The previous code reference suggestion was not found in the document.

**Original Description:** {description}
**Location:** {location}
**Previous Suggestion:** {previous_reference}
**User Feedback:** {feedback}

Please re-analyze and provide a different, valid code reference that exists in the document.

Respond in this exact format:
MATCH_TYPE: [Section|Table|Figure]
REFERENCE: [The specific code reference]
CONFIDENCE: [High|Medium|Low]
REASONING: [Your brief explanation]"""


def build_analysis_prompt(description: str, location: str) -> str:
    """Build the analysis prompt with user inputs."""
    return USER_PROMPT_TEMPLATE.format(
        description=description,
        location=location
    )


def build_reanalysis_prompt(
    description: str,
    location: str,
    previous_reference: str,
    feedback: str
) -> str:
    """Build prompt for re-analysis after hallucination."""
    return REANALYSIS_PROMPT_TEMPLATE.format(
        description=description,
        location=location,
        previous_reference=previous_reference,
        feedback=feedback
    )
