import networkx as nx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Course, PathwayPlan, Student
from ..schemas import ApproveBody, ChatBody, StudentEdit
from ..services.advising import WEIGHTS, evaluate, plan_pathway, public_course
from ..services.graph_service import build_graph
from ..services.llm_service import explain

router = APIRouter()


def student_or_404(db: Session, student_id: int) -> Student:
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(404, "Student not found")
    return student


def public_student(student: Student) -> dict:
    return {
        "id": student.id,
        "student_id": student.student_id,
        "name": student.name,
        "current_semester": student.current_semester,
        "completed_credits": student.completed_credits,
        "interests": student.interests,
        "career_goal": student.career_goal,
        "gpa": student.gpa,
        "max_credits": student.max_credits,
        "completed_courses": student.completed_courses,
    }


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/students")
def students(db: Session = Depends(get_db)):
    return [public_student(student) for student in db.query(Student).all()]


@router.get("/students/{student_id}")
def get_student(student_id: int, db: Session = Depends(get_db)):
    return public_student(student_or_404(db, student_id))


@router.put("/students/{student_id}")
def edit_student(student_id: int, body: StudentEdit, db: Session = Depends(get_db)):
    student = student_or_404(db, student_id)
    data = body.model_dump()
    known_codes = {row[0] for row in db.query(Course.code).all()}
    unknown = set(data["completed_courses"]) - known_codes
    if unknown:
        raise HTTPException(422, f"Unknown completed course codes: {', '.join(sorted(unknown))}")

    # Flush orphan removals before re-inserting normalized rows to avoid unique-key collisions.
    student.interest_rows.clear()
    student.completed_course_rows.clear()
    db.flush()
    for key, value in data.items():
        setattr(student, key, value)
    db.commit()
    return public_student(student)


@router.get("/courses")
def courses(db: Session = Depends(get_db)):
    return [public_course(course) for course in db.query(Course).order_by(Course.semester, Course.code)]


@router.get("/courses/{course_code}")
def get_course(course_code: str, db: Session = Depends(get_db)):
    course = db.get(Course, course_code.upper())
    if not course:
        raise HTTPException(404, "Course not found")
    return public_course(course)


@router.get("/eligibility/{student_id}")
def eligibility(student_id: int, db: Session = Depends(get_db)):
    student = student_or_404(db, student_id)
    eligible, ineligible, _ = evaluate(db, student)
    return {
        "eligible": [
            {**public_course(item["course"]), "score": item["score"], "rank": item["rank"], "prerequisites": item["prerequisites"]}
            for item in eligible
        ],
        "ineligible": [
            {"course": public_course(item["course"]), "reasons": item["reasons"]}
            for item in ineligible
        ],
    }


@router.get("/recommendations/{student_id}")
def recommendations(student_id: int, db: Session = Depends(get_db)):
    student = student_or_404(db, student_id)
    eligible, _, _ = evaluate(db, student)
    return {
        "weights": WEIGHTS,
        "recommendations": [
            {
                "course": public_course(item["course"]),
                "score": item["score"],
                "rank": item["rank"],
                "factors": item["factors"],
                "explanation": f"Interest and career fit; prerequisites satisfied. Weighted score {item['score']}/100.",
            }
            for item in eligible
        ],
    }


@router.get("/graph")
def graph(db: Session = Depends(get_db)):
    curriculum_graph = build_graph(db)
    return {
        "nodes": [{"code": course.code, "name": course.name} for course in db.query(Course).all()],
        "edges": [{"from": source, "to": target} for source, target in curriculum_graph.edges],
        "topological_order": list(nx.topological_sort(curriculum_graph)),
    }


@router.get("/graph/{course_code}")
def graph_course(course_code: str, db: Session = Depends(get_db)):
    curriculum_graph = build_graph(db)
    code = course_code.upper()
    if code not in curriculum_graph:
        raise HTTPException(404, "Course not found")
    return {
        "course_code": code,
        "prerequisites": sorted(curriculum_graph.predecessors(code)),
        "all_prerequisites": sorted(nx.ancestors(curriculum_graph, code)),
        "dependents": sorted(nx.descendants(curriculum_graph, code)),
    }


@router.post("/pathway/{student_id}")
def pathway(student_id: int, db: Session = Depends(get_db)):
    student = student_or_404(db, student_id)
    eligible, _, curriculum_graph = evaluate(db, student)
    semesters = plan_pathway(db, student, eligible, curriculum_graph)
    plan = PathwayPlan(student_id=student.id, semesters=semesters)
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return {"id": plan.id, "status": plan.status, "semesters": plan.semesters}


@router.get("/advisor")
def advisor_queue(db: Session = Depends(get_db)):
    plans = db.query(PathwayPlan).order_by(PathwayPlan.id.desc()).all()
    return [
        {
            "id": plan.id,
            "student_id": plan.student_id,
            "student_name": db.get(Student, plan.student_id).name,
            "status": plan.status,
            "advisor_note": plan.advisor_note,
            "semesters": plan.semesters,
        }
        for plan in plans
    ]


@router.post("/advisor/{plan_id}/review")
def review(plan_id: int, body: ApproveBody, db: Session = Depends(get_db)):
    plan = db.get(PathwayPlan, plan_id)
    if not plan:
        raise HTTPException(404, "Pathway not found")
    if body.status not in {"approved", "rejected", "pending"}:
        raise HTTPException(422, "status must be approved, rejected, or pending")
    plan.status = body.status
    plan.advisor_note = body.advisor_note
    db.commit()
    return {"id": plan.id, "status": plan.status, "advisor_note": plan.advisor_note, "semesters": plan.semesters}


@router.post("/chat")
def chat(body: ChatBody, db: Session = Depends(get_db)):
    student = student_or_404(db, body.student_id)
    eligible, blocked, _ = evaluate(db, student)
    results = {
        "recommendations": [
            {
                "course": public_course(item["course"]),
                "score": item["score"],
                "rank": item["rank"],
                "prerequisites": item["prerequisites"],
            }
            for item in eligible[:5]
        ],
        "ineligible": [
            {"course": public_course(item["course"]), "reasons": item["reasons"]}
            for item in blocked
        ],
    }
    student_context = {
        "name": student.name,
        "interests": student.interests,
        "career_goal": student.career_goal,
        "gpa": student.gpa,
    }
    return explain(body.question, student_context, results)
