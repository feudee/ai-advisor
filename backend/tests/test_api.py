import pytest
from fastapi import HTTPException

from app.routers.api import (
    advisor_queue,
    chat,
    get_course,
    graph_course,
    pathway,
    recommendations,
    review,
)
from app.schemas import ApproveBody, ChatBody


def test_course_lookup_and_prerequisite_graph(db):
    session, _ = db

    assert get_course("ml", session)["code"] == "ML"
    with pytest.raises(HTTPException) as missing_course:
        get_course("unknown", session)
    assert missing_course.value.status_code == 404

    graph = graph_course("DL", session)
    assert graph["prerequisites"] == ["ML"]
    assert graph["all_prerequisites"] == ["LA", "ML", "PY"]
    assert graph["dependents"] == []


def test_live_advising_to_advisor_approval_flow(db):
    session, student = db
    recommended = recommendations(student.id, session)["recommendations"]
    ranked_codes = [row["course"]["code"] for row in recommended]
    assert "ML" in ranked_codes
    assert "DL" not in ranked_codes

    plan = pathway(student.id, session)
    assert plan["status"] == "pending"
    assert plan["semesters"]

    approved = review(
        plan["id"],
        ApproveBody(status="approved", advisor_note="Prerequisites checked."),
        session,
    )
    assert approved["status"] == "approved"
    assert approved["advisor_note"] == "Prerequisites checked."

    queued = next(item for item in advisor_queue(session) if item["id"] == plan["id"])
    assert queued["status"] == "approved"

    answer = chat(ChatBody(student_id=student.id, question="Why Machine Learning?"), session)
    assert "eligible" in answer["answer"].lower()
