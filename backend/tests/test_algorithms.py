import networkx as nx
import pytest
from app.models import Prerequisite
from app.services.graph_service import build_graph, prerequisite_status
from app.services.advising import evaluate, plan_pathway, load_weights

def test_prerequisites_satisfied_and_missing(db):
    session,student=db; graph=build_graph(session)
    assert prerequisite_status(graph,"ML",set(student.completed_courses))["satisfied"]
    assert prerequisite_status(graph,"DL",set(student.completed_courses))["missing"]==["ML"]

def test_transitive_prerequisites_are_required(db):
    session,student=db; graph=build_graph(session)
    status=prerequisite_status(graph,"DL",{"PY"})
    assert status["missing"]==["LA","ML"]

def test_completed_course_filter_and_credit_limit(db):
    session,student=db; eligible,ineligible,_=evaluate(session,student)
    eligible_codes={x["course"].code for x in eligible}; blocked={x["course"].code:x["reasons"] for x in ineligible}
    assert "PY" not in eligible_codes
    assert "DL" in blocked and "Missing prerequisites: ML" in blocked["DL"]
    assert "BIG" in blocked and any("semester limit" in reason.lower() for reason in blocked["BIG"])

def test_recommendation_ranking_is_deterministic_and_weighted(db):
    session,student=db; first=evaluate(session,student)[0]; again=evaluate(session,student)[0]
    assert [x["course"].code for x in first]==[x["course"].code for x in again]
    assert first[0]["course"].code=="ML" and first[0]["score"]>0

def test_pathway_respects_prerequisites_and_credit_limit(db):
    session,student=db; eligible,_,graph=evaluate(session,student); pathway=plan_pathway(session,student,eligible,graph)
    assert pathway[0]["semester"]==3
    assert all(term["credits"]<=student.max_credits for term in pathway)
    locations={c["code"]:term["semester"] for term in pathway for c in term["courses"]}
    if "ML" in locations and "DL" in locations: assert locations["ML"]<locations["DL"]

def test_cycle_detection(db):
    session,_=db; session.add(Prerequisite(course_code="PY",prerequisite_code="ML"));session.commit()
    with pytest.raises(ValueError,match="cycle"): build_graph(session)

def test_ranking_weights_can_be_configured_and_normalized(monkeypatch):
    monkeypatch.setenv("ADVISOR_WEIGHTS", '{"interest": 7, "career": 1, "academic": 1, "progression": 1, "semester": 0}')
    weights = load_weights()
    assert sum(weights.values()) == pytest.approx(1)
    assert weights["interest"] == pytest.approx(.7)

def test_invalid_ranking_weights_are_rejected(monkeypatch):
    monkeypatch.setenv("ADVISOR_WEIGHTS", '{"interest": -1, "career": 1, "academic": 1, "progression": 1, "semester": 1}')
    with pytest.raises(ValueError, match="non-negative"):
        load_weights()
