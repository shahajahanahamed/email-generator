"""
services/llm.py — Groq LLM client and email generation logic.

THIS IS THE CORE AI LAYER. It handles:
  1. Initializing the Groq client (once, at startup)
  2. Building the prompt from user input
  3. Calling the LLM
  4. Parsing the response into subject + body

WHY IS THIS A SERVICE (not inside the router)?
  - Router = thin layer (HTTP in → HTTP out)
  - Service = business logic (the actual work)
  - If you later add CLI, cron jobs, or tests →
    they all reuse the service without touching HTTP code
"""

import logging
import re
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.language_models.chat_models import BaseChatModel

from app.core.config import settings
from app.schemas.email import EmailGenerateRequest

logger = logging.getLogger(__name__)


# ── LLM Client (Singleton) ─────────────────────────────────────────────────────

# Module-level variable — initialized once when the module loads
# All requests share this single client instance
_llm_client: BaseChatModel | None = None


def get_llm_client() -> BaseChatModel:
    """
    Returns the initialized Groq LLM client.

    SINGLETON PATTERN:
    - Client is created once on first call
    - Reused for every subsequent request
    - Avoids reconnecting to Groq on every API call
    - Thread-safe for read-only client objects

    Raises:
        ValueError: If GROQ_API_KEY is not configured
        RuntimeError: If client initialization fails
    """
    global _llm_client

    if _llm_client is not None:
        return _llm_client  # Already initialized → return immediately

    if not settings.GROQ_API_KEY
        raise ValueError(
            "GROQ_API_KEY is not set in your .env file. "
            "Get your key at: https://console.groq.com"
        )

    logger.info(f"Initializing Groq LLM client with model: {settings.GROQ_MODEL}")

    try:
        _llm_client = ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model=settings.GROQ_MODEL,

            # temperature: controls randomness
            # 0.0 = deterministic (same input → same output)
            # 1.0 = very creative/random
            # 0.7 = good balance for emails (professional but not robotic)
            temperature=0.7,

            # max_tokens: maximum length of generated response
            # ~750 tokens ≈ 500-600 words (enough for a full email)
            max_tokens=750,
        )
        logger.info("✅ Groq LLM client initialized successfully")
        return _llm_client

    except Exception as e:
        logger.error(f"❌ Failed to initialize Groq client: {e}")
        raise RuntimeError(f"LLM initialization failed: {e}") from e


# ── Prompt Builder ─────────────────────────────────────────────────────────────

def build_email_prompt(request: EmailGenerateRequest) -> tuple[str, str]:
    """
    Constructs the system + user prompt for email generation.

    Returns:
        tuple[str, str]: (system_prompt, user_prompt)

    WHY TWO PROMPTS?
    - system_prompt: Sets the AI's persona and rules (like a job description)
    - user_prompt:   The actual task with specific data

    This is the standard pattern for chat LLMs (GPT-4, Claude, Llama).
    Separating them gives better, more consistent results.
    """

    # ── System Prompt ──────────────────────────────────────
    # Tells the LLM WHO it is and WHAT RULES to follow
    system_prompt = f"""You are an expert professional email writer with 15 years of experience.
Your task is to write high-quality, {request.tone} tone emails.

STRICT OUTPUT FORMAT — you MUST follow this exactly:
SUBJECT: <subject line here>
BODY:
<email body here>

RULES:
- Start BODY with proper greeting (e.g., "Dear {request.recipient_name},")
- End BODY with professional sign-off and sender name ({request.sender_name})
- Write in {request.tone} tone throughout
- Include ALL bullet points provided — do not skip any
- Do NOT add any explanation before SUBJECT or after the email body
- Do NOT use markdown formatting (no **, no ##, no bullet symbols)
- Write in plain text only"""

    # ── User Prompt ────────────────────────────────────────
    # The specific task with the user's actual data
    formatted_bullets = "\n".join(
        f"  - {point}" for point in request.bullet_points
    )

    user_prompt = f"""Write a {request.tone} email with the following details:

From: {request.sender_name}
To: {request.recipient_name}
Topic: {request.subject_hint}

Key Points to Cover:
{formatted_bullets}

Generate the email now:"""

    logger.debug(f"System prompt length: {len(system_prompt)} chars")
    logger.debug(f"User prompt length: {len(user_prompt)} chars")

    return system_prompt, user_prompt


# ── Response Parser ────────────────────────────────────────────────────────────

def parse_llm_response(raw_text: str) -> tuple[str, str]:
    """
    Parses the raw LLM output into separate subject and body.

    Expected LLM output format:
        SUBJECT: Meeting postponement request
        BODY:
        Dear John,
        I hope this email finds you well...

    Args:
        raw_text: The raw string returned by the LLM

    Returns:
        tuple[str, str]: (subject, body)

    Raises:
        ValueError: If response format is unexpected
    """
    raw_text = raw_text.strip()
    logger.debug(f"Parsing LLM response ({len(raw_text)} chars)")

    # Strategy 1: Look for SUBJECT: and BODY: markers
    subject_match = re.search(
        r"SUBJECT:\s*(.+?)(?:\n|$)",
        raw_text,
        re.IGNORECASE,
    )
    body_match = re.search(
        r"BODY:\s*\n?([\s\S]+)",
        raw_text,
        re.IGNORECASE,
    )

    if subject_match and body_match:
        subject = subject_match.group(1).strip()
        body = body_match.group(1).strip()
        logger.debug(f"✅ Parsed successfully — Subject: '{subject[:50]}...'")
        return subject, body

    # Strategy 2: Fallback — first line is subject, rest is body
    # (LLM sometimes ignores format instructions)
    logger.warning("LLM didn't follow format — using fallback parser")
    lines = raw_text.split("\n", 1)

    if len(lines) >= 2:
        subject = lines[0].strip().lstrip("Subject:").strip()
        body = lines[1].strip()
        return subject, body

    # Strategy 3: Last resort — use hint as subject
    logger.warning("Using last-resort parsing strategy")
    return "Generated Email", raw_text


# ── Main Service Function ──────────────────────────────────────────────────────

async def generate_email(request: EmailGenerateRequest) -> dict:
    """
    Main function: generates an email from the request data.

    Flow:
        1. Get LLM client
        2. Build prompts
        3. Call Groq API
        4. Parse response
        5. Return structured result

    Args:
        request: Validated EmailGenerateRequest from the router

    Returns:
        dict with keys: subject, body, model_used

    Raises:
        RuntimeError: If LLM call fails
        ValueError: If Groq API key is missing
    """

    # Step 1: Get client
    llm = get_llm_client()

    # Step 2: Build prompts
    system_prompt, user_prompt = build_email_prompt(request)

    # Step 3: Call Groq
    logger.info(
        f"Calling Groq ({settings.GROQ_MODEL}) | "
        f"Recipient: {request.recipient_name} | "
        f"Tone: {request.tone} | "
        f"Bullets: {len(request.bullet_points)}"
    )

    try:
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        # This is the actual API call to Groq
        # ainvoke() = async invoke (non-blocking, handles concurrent requests)
        response = await llm.ainvoke(messages)

        raw_text: str = response.content
        logger.info(f"✅ Groq responded ({len(raw_text)} chars)")

    except Exception as e:
        logger.error(f"❌ Groq API call failed: {e}")
        raise RuntimeError(f"LLM generation failed: {e}") from e

    # Step 4: Parse response
    subject, body = parse_llm_response(raw_text)

    # Step 5: Return result
    return {
        "subject": subject,
        "body": body,
        "model_used": settings.GROQ_MODEL,
    }