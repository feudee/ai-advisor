import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import Course, Prerequisite, Student


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    courses = [
        Course(code="PY", name="Python", credits=3, semester=1, category="Core", interest_tags=["ai"], difficulty=2, availability=True),
        Course(code="LA", name="Linear Algebra", credits=3, semester=1, category="Math", interest_tags=["ai"], difficulty=3, availability=True),
        Course(code="ML", name="Machine Learning", credits=4, semester=3, category="AI", interest_tags=["ai", "machine learning"], difficulty=4, availability=True),
        Course(code="DL", name="Deep Learning", credits=4, semester=4, category="AI", interest_tags=["ai"], difficulty=5, availability=True),
        Course(code="BIG", name="Large Seminar", credits=20, semester=3, category="Elective", interest_tags=[], difficulty=2, availability=True),
    ]
    session.add_all(courses)
    session.flush()
    session.add_all(
        [
            Prerequisite(course_code="ML", prerequisite_code="PY"),
            Prerequisite(course_code="ML", prerequisite_code="LA"),
            Prerequisite(course_code="DL", prerequisite_code="ML"),
        ]
    )
    student = Student(
        student_id="T1",
        name="Test Student",
        current_semester=3,
        completed_credits=30,
        interests=["AI"],
        career_goal="AI/ML Engineer",
        gpa=3.6,
        max_credits=18,
        completed_courses=["PY", "LA"],
    )
    session.add(student)
    session.commit()
    yield session, student
    session.close()
    Base.metadata.drop_all(engine)
