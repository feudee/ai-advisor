from sqlalchemy import String, Integer, Float, Boolean, ForeignKey, Text, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

class Student(Base):
    __tablename__ = "students"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    name: Mapped[str] = mapped_column(String)
    current_semester: Mapped[int] = mapped_column(Integer, default=5)
    completed_credits: Mapped[int] = mapped_column(Integer, default=0)
    career_goal: Mapped[str] = mapped_column(String, default="AI/ML Engineer")
    gpa: Mapped[float] = mapped_column(Float, default=3.5)
    max_credits: Mapped[int] = mapped_column(Integer, default=18)
    interest_rows: Mapped[list["StudentInterest"]] = relationship(back_populates="student", cascade="all, delete-orphan", lazy="selectin")
    completed_course_rows: Mapped[list["StudentCompletedCourse"]] = relationship(back_populates="student", cascade="all, delete-orphan", lazy="selectin")

    @property
    def interests(self):
        return [row.interest for row in self.interest_rows]

    @interests.setter
    def interests(self, values):
        self.interest_rows = [StudentInterest(interest=value.strip()) for value in (values or []) if value.strip()]

    @property
    def completed_courses(self):
        return [row.course_code for row in self.completed_course_rows]

    @completed_courses.setter
    def completed_courses(self, values):
        self.completed_course_rows = [StudentCompletedCourse(course_code=value) for value in (values or [])]

class StudentInterest(Base):
    __tablename__ = "student_interests"
    __table_args__ = (UniqueConstraint("student_pk", "interest", name="uq_student_interest"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_pk: Mapped[int] = mapped_column(ForeignKey("students.id"))
    interest: Mapped[str] = mapped_column(String)
    student: Mapped[Student] = relationship(back_populates="interest_rows")

class StudentCompletedCourse(Base):
    __tablename__ = "student_completed_courses"
    __table_args__ = (UniqueConstraint("student_pk", "course_code", name="uq_student_completed_course"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_pk: Mapped[int] = mapped_column(ForeignKey("students.id"))
    course_code: Mapped[str] = mapped_column(ForeignKey("courses.code"))
    student: Mapped[Student] = relationship(back_populates="completed_course_rows")

class Course(Base):
    __tablename__ = "courses"
    code: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    credits: Mapped[int] = mapped_column(Integer)
    semester: Mapped[int] = mapped_column(Integer)
    category: Mapped[str] = mapped_column(String)
    interest_tags: Mapped[list] = mapped_column(JSON, default=list)
    difficulty: Mapped[int] = mapped_column(Integer, default=3)
    availability: Mapped[bool] = mapped_column(Boolean, default=True)

class Prerequisite(Base):
    __tablename__ = "prerequisites"
    __table_args__ = (UniqueConstraint("course_code", "prerequisite_code", name="uq_course_prerequisite"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    course_code: Mapped[str] = mapped_column(ForeignKey("courses.code"))
    prerequisite_code: Mapped[str] = mapped_column(ForeignKey("courses.code"))

class PathwayPlan(Base):
    __tablename__ = "pathway_plans"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"))
    semesters: Mapped[list] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String, default="pending")
    advisor_note: Mapped[str] = mapped_column(Text, default="")
