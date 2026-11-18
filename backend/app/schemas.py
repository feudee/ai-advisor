from pydantic import BaseModel, Field


class StudentEdit(BaseModel):
    name: str
    current_semester: int = Field(ge=1, le=12)
    completed_credits: int = Field(ge=0)
    interests: list[str]
    career_goal: str
    gpa: float = Field(ge=0, le=4)
    max_credits: int = Field(ge=1, le=30)
    completed_courses: list[str]


class ApproveBody(BaseModel):
    status: str = "approved"
    advisor_note: str = ""


class ChatBody(BaseModel):
    student_id: int
    question: str
