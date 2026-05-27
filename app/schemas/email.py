"""
schemas/email.py - Request and Response data models for Phase 2.

WHY PYDANTIC MODELS?
    - FastAPI auto-validates incoming JSON against these models
    - If a field is wrong type or missing -> automatic 422 error
    - Auto-generates API docs (Swagger UI shows these fields)
    - Acts as living documentation for your API contract

PHASE 2: Simple models (we expand them significantly in Phase 3)
"""

# ── Request Model ─────────────────────────────────────────────────────────────
from typing import Optional

from pydantic import BaseModel, Field
from pydantic_settings import SettingsConfigDict


class EmailGenerateRequest(BaseModel):
    """
    What the client sends to generate an email.
    Example JSON body :
    {
        "recipient_name": "John Smith",
        "sender_name": "Alice",
        "subject_hint": "Project deadline extension request",
        "bullet_points": [
            "Deadline is next Friday",
            "Team needs 2 more weeks",
            "Current blocker: design assets not delivered"
        ],
        "tone": "formal"
    }
    """

    recipient_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Name of the email recipient",
        examples=["John Smith"],
    )
    sender_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Name of the email sender",
        examples=["Alice Johnson"],
    )

    subject_hint: str = Field(
        ...,
        min_length=3,
        max_length=200,
        description="Brief hint about what the email is about",
        examples=["Project deadline extension request"],
    )

    bullet_points: list[str] = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Key points to include in the email",
        examples=[["Deadline is next Friday", "Need 2 more weeks"]],
    )

    tone: Optional[str] = Field(
        default="formal",
        description="Writing tone of the email",
        examples=["formal"],
    )

    class Config:
        # Allows Swagger UI to show a working example
        json_schema_extra = {
            "example": {
                "recipient_name": "John Smith",
                "sender_name": "Alice Johnson",
                "subject_hint": "Project deadline extension request",
                "bullet_points": [
                    "Original deadline is next Friday",
                    "Team needs 2 additional weeks",
                    "Current blocker: design assets not yet delivered by vendor",
                    "Requesting new deadline: March 15th",
                ],
                "tone": "formal",
            }
        }


# ── Response Model ─────────────────────────────────────────────────────────────


class EmailGenerateResponse(BaseModel):
    """
    What the API returns after generating an email.

    WHY SEPARATE RESPONSE MODEL?
    - Controls exactly what fields the client receives
    - Hides internal fields (DB ids, raw prompts, costs)
    - Easy to version (add fields without breaking old clients)
    """

    success: bool = Field(description="Whether the generation succeeded")

    subject: str = Field(description="Generated email subject line")

    body: str = Field(description="Generated email body")

    tone_used: str = Field(description="The tone that was applied")

    bullet_points_used: list[str] = Field(
        description="The bullet points that were processed"
    )

    model_used: str = Field(description="Which LLM model generated this email")


# ── Error Response Model ───────────────────────────────────────────────────────


class ErrorResponse(BaseModel):
    """
    Consistent error shape across all endpoints.

    Instead of different error formats everywhere,
    ALL errors look the same → easier for frontend to handle.
    """

    success: bool = False
    error: str = Field(description="Human-readable error message")
    detail: Optional[str] = Field(
        default=None, description="Technical detail (only shown in debug mode)"
    )
