"""
Pydantic schema for the AI Resume Parser.

This is the "contract" from Episode 6: the exact same class does double duty —
it's the schema we hand to the API to constrain generation, and it's the
validated object we get back to work with in code.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class Skills(BaseModel):
    """Skills, categorized so downstream code can filter/search by type."""

    languages: List[str] = Field(
        default_factory=list,
        description="Programming languages only, e.g. Python, TypeScript, Go.",
    )
    frameworks: List[str] = Field(
        default_factory=list,
        description="Frameworks and libraries, e.g. React, FastAPI, PyTorch.",
    )
    tools: List[str] = Field(
        default_factory=list,
        description="Everything else technical: platforms, software, methodologies, "
        "e.g. Docker, AWS, Jira, Scrum.",
    )


class Experience(BaseModel):
    """A single work experience entry."""

    company: str
    title: str
    duration: str = Field(
        description="As written in the resume, e.g. 'Jan 2022 - Present' or '2019-2021'."
    )
    bullet_points: List[str] = Field(
        default_factory=list,
        description="The responsibility/achievement bullets under this role, verbatim "
        "or lightly cleaned up — never invented.",
    )


class Education(BaseModel):
    """A single education entry."""

    institution: str
    degree: str
    field_of_study: Optional[str] = None
    graduation_year: Optional[str] = None


class ParsedResume(BaseModel):
    """
    The full structured output for one parsed resume.

    Every field here is either directly extractable from resume text, or
    (candidate_summary) a short, strictly factual synthesis of it. Nothing in
    this schema asks the model to judge, score, or rank the candidate —
    that's a deliberate design choice, see the system prompt in parser.py.
    """

    name: str
    email: Optional[str] = None
    linkedin: Optional[str] = None
    work_experience: List[Experience] = Field(default_factory=list)
    skills: Skills = Field(default_factory=Skills)
    education: List[Education] = Field(default_factory=list)
    candidate_summary: str = Field(
        description="Exactly 3 sentences. Strictly factual: experience level, "
        "domain, and notable skills. Never an opinion, score, or recommendation."
    )
