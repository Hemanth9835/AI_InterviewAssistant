import os

from openai import AsyncOpenAI


class InterviewServiceError(RuntimeError):
    """Base error for interview prompt generation failures."""


class MissingOpenAIKeyError(InterviewServiceError):
    """Raised when the OpenAI API key is not configured."""


class LanguageModelRequestError(InterviewServiceError):
    """Raised when the language model request fails or returns no prompt."""


SYSTEM_PROMPT = (
    "You are an expert in Statistics, Data Science, and Machine Learning. "
    "Ask application-oriented, scenario-based interview questions with practical "
    "applications. Questions should have a statistical perspective and "
    "expect the candidate to explain the reasoning. "
    "Generate only one question at a time. Return only the question, with no answer, "
    "preamble, numbering, or bullets."
)

USER_PROMPT = (
    "I have 3 years of experience as a Data Analyst/Data Engineer and I am preparing "
    "for interviews for the positions of Data Scientist, Machine Learning Engineer, "
    "and AI Engineer. Help me prepare for these interviews by asking scenario-based "
    "questions that challenge my technical ability and analytical thinking process."
)

difficulty_guidance = {
    "easy": (
        "Keep the scenario approachable and focus on core concepts, straightforward "
        "reasoning, and familiar statistical or machine learning techniques."
    ),
    "medium": (
        "Use a realistic scenario that requires comparing reasonable approaches and "
        "explaining trade-offs involving data, metrics, assumptions, or model choice."
    ),
    "hard": (
        "Make the scenario challenging and ambiguous, requiring deeper reasoning about "
        "trade-offs, edge cases, statistical assumptions, scalability, or production risks."
    ),
}

role_labels = {
    "data_analyst": "Data Analyst",
    "data_engineer": "Data Engineer",
    "data_scientist": "Data Scientist",
    "machine_learning_engineer": "Machine Learning Engineer",
    "mlops": "MLOps",
    "ai_engineering": "AI Engineering",
}


def build_messages(
    focus: str,
    difficulty: str = "medium",
    role: str = "data_scientist",
) -> list[dict[str, str]]:
    user_prompt = (
        f"{USER_PROMPT} Target role: {role_labels[role]}. "
        f"Difficulty level: {difficulty}. {difficulty_guidance[difficulty]}"
    )
    if focus:
        user_prompt += f" Focus this question on {focus}."

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]


async def generate_interview_prompt(
    focus: str,
    difficulty: str,
    role: str,
) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise MissingOpenAIKeyError("OPENAI_API_KEY is not configured.")

    client = AsyncOpenAI(api_key=api_key)
    try:
        response = await client.responses.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            input=build_messages(focus.strip(), difficulty, role),
            max_output_tokens=120,
            temperature=0.8,
        )
    except Exception as exc:
        raise LanguageModelRequestError(
            "The language model request failed."
        ) from exc

    prompt = response.output_text.strip()
    if not prompt:
        raise LanguageModelRequestError(
            "The language model returned no prompt."
        )
    return prompt
