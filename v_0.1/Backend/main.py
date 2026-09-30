import os
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
        allow_origins=[
        "https://ai-interviewassistant-z3kl.onrender.com",
    ],
   allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


class GenerateRequest(BaseModel):
    focus: str = Field(default="", max_length=200)
    difficulty: Literal["easy", "medium", "hard"] = "medium"
    role: Literal[
        "data_analyst",
        "data_engineer",
        "data_scientist",
        "machine_learning_engineer",
        "mlops",
        "ai_engineering",
    ] = "data_scientist"


class GenerateResponse(BaseModel):
    prompt: str


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


@app.get("/")
async def root():
    return {"message": "Interview question API is running"}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/generate", response_model=GenerateResponse)
async def generate_prompt(request: GenerateRequest):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="OPENAI_API_KEY is not configured.")

    client = AsyncOpenAI(api_key=api_key)
    try:
        response = await client.responses.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            input=build_messages(request.focus.strip(), request.difficulty, request.role),
            max_output_tokens=120,
            temperature=0.8,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail="The language model request failed.") from exc

    prompt = response.output_text.strip()
    if not prompt:
        raise HTTPException(status_code=502, detail="The language model returned no prompt.")
    return GenerateResponse(prompt=prompt)
