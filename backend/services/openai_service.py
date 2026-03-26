import json
import re

from openai import APIError, AuthenticationError, OpenAI, RateLimitError

SYSTEM_PROMPT = (
    "You are a world-class research scientist and educator. Given the text of a "
    "research paper, you produce a comprehensive, research-grade tutorial as structured "
    "JSON. Your output must be a single JSON object (no markdown fences, no commentary) "
    "with these exact keys:\n"
    "\n"
    "- title (string): The paper's title\n"
    "- authors (array of strings): Author names\n"
    "- summary (string): Executive summary covering key contributions, novelty, and impact\n"
    "- math_foundations (array of objects with keys: name, latex, explanation): "
    "Core mathematical concepts with LaTeX equations\n"
    "- algorithms (array of objects with keys: name, pseudocode, implementation, synthetic_data): "
    "Each major algorithm with pseudocode, Python implementation (with type hints and docstrings), "
    "and code to generate realistic synthetic data for testing\n"
    "- visualizations (array of objects with keys: title, code): "
    "matplotlib/plotly code for publication-quality figures\n"
    "- ablation_study (object with keys: description, code): "
    "Ablation study varying key hyperparameters\n"
    "- exercises (array of objects with keys: question, hint): "
    "3-5 meaningful exercises for deeper understanding\n"
    "- references (array of strings): Key references and further reading\n"
    "\n"
    "Requirements:\n"
    "- All Python code must include type hints and be production-quality\n"
    "- Synthetic data must be realistic, not random noise\n"
    "- Visualizations must be publication-quality with proper labels and legends\n"
    "- Math must use proper LaTeX notation\n"
    "- Return ONLY the JSON object, no other text"
)

USER_PROMPT_TEMPLATE = (
    "Analyze the following research paper and produce the structured tutorial JSON.\n"
    "\n"
    "Paper text:\n"
    "{{PAPER_TEXT}}"
)

REQUIRED_KEYS = {
    "title", "authors", "summary", "math_foundations",
    "algorithms", "visualizations", "ablation_study",
    "exercises", "references",
}


def generate_tutorial(pdf_text: str, api_key: str) -> dict:
    """Call GPT-5.4 to generate a structured research tutorial from paper text.

    Args:
        pdf_text: Extracted text from the research paper.
        api_key: User's OpenAI API key.

    Returns:
        A dict with keys: title, authors, summary, math_foundations,
        algorithms, visualizations, ablation_study, exercises, references.

    Raises:
        ValueError: On authentication failure, rate limits, API errors,
                    or malformed responses.
    """
    client = OpenAI(api_key=api_key)

    user_prompt = USER_PROMPT_TEMPLATE.replace("{{PAPER_TEXT}}", pdf_text)

    try:
        response = client.chat.completions.create(
            model="gpt-5.4",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
        )
    except AuthenticationError:
        raise ValueError("Invalid OpenAI API key. Please check your key and try again.")
    except RateLimitError:
        raise ValueError("OpenAI rate limit exceeded. Please wait a moment and try again.")
    except APIError as e:
        raise ValueError(f"OpenAI API error: {e.message}")

    raw = response.choices[0].message.content.strip()

    # Strip markdown code fences if present
    fenced = re.match(r"^```(?:json)?\s*\n(.*)\n```$", raw, re.DOTALL)
    if fenced:
        raw = fenced.group(1).strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        raise ValueError(f"Failed to parse GPT response as JSON: {raw[:200]}")

    missing = REQUIRED_KEYS - set(data.keys())
    if missing:
        raise ValueError(f"GPT response missing required keys: {', '.join(sorted(missing))}")

    return data
