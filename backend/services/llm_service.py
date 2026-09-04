from groq import Groq

from backend.config import GROQ_API_KEY


DEFAULT_MODEL = "openai/gpt-oss-120b"


class LLMService:
    """
    Generate grounded answers using repository context.
    """

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
    ):
        if not GROQ_API_KEY:
            raise ValueError(
                "GROQ_API_KEY is not configured."
            )

        self.client = Groq(
            api_key=GROQ_API_KEY
        )

        self.model = model

    def generate_answer(
        self,
        question: str,
        context: str,
    ) -> str:

        if not question or not question.strip():
            raise ValueError(
                "Question cannot be empty."
            )

        if not context or not context.strip():
            raise ValueError(
                "Repository context cannot be empty."
            )

        system_prompt = """
You are an AI repository analyst.

Your job is to answer questions about a software
repository using ONLY the repository context provided
by the user.

Rules:

1. Do not invent files, functions, classes, or behavior.
2. Base the answer primarily on the provided context.
3. If the context is insufficient, clearly say that
   the available repository context is insufficient.
4. Mention relevant file paths when useful.
5. Explain technical concepts clearly.
6. Prefer concise but useful answers.
"""

        user_prompt = f"""
Repository Context:

{context}

User Question:

{question}

Analyze the repository context and answer the question.
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            temperature=0.1,
            max_tokens=1200,
        )

        return response.choices[0].message.content.strip()