import json
import os

import networkx as nx
from sqlalchemy.orm import Session
from ..models import Student, Course
from .graph_service import build_graph, prerequisite_status

DEFAULT_WEIGHTS = {"interest": .35, "career": .25, "academic": .20, "progression": .10, "semester": .10}


def load_weights():
    """Load a normalized, non-negative ranking configuration from the environment."""
    raw = os.getenv("ADVISOR_WEIGHTS")
    if not raw:
        return DEFAULT_WEIGHTS.copy()
    try:
        configured = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("ADVISOR_WEIGHTS must be a JSON object") from exc
    if not isinstance(configured, dict) or set(configured) != set(DEFAULT_WEIGHTS):
        raise ValueError(f"ADVISOR_WEIGHTS must contain exactly: {', '.join(DEFAULT_WEIGHTS)}")
    if any(not isinstance(value, (int, float)) or value < 0 for value in configured.values()):
        raise ValueError("ADVISOR_WEIGHTS values must be non-negative numbers")
    total = sum(configured.values())
    if total <= 0:
        raise ValueError("ADVISOR_WEIGHTS must have a positive total")
    return {key: value / total for key, value in configured.items()}


WEIGHTS = load_weights()

def evaluate(db: Session, student: Student):
    courses = db.query(Course).all()
    by_code = {c.code: c for c in courses}
    graph = build_graph(db)
    completed = set(student.completed_courses or [])
    eligible, ineligible = [], []
    for c in courses:
        if c.code in completed: continue
        reasons = []
        prereq = prerequisite_status(graph, c.code, completed)
        if prereq["missing"]: reasons.append("Missing prerequisites: " + ", ".join(prereq["missing"]))
        if not c.availability: reasons.append("Not currently offered")
        if c.semester > student.current_semester + 1: reasons.append(f"Available in a later curriculum semester ({c.semester})")
        if c.credits > student.max_credits: reasons.append(f"Course exceeds the {student.max_credits}-credit semester limit")
        if reasons: ineligible.append({"course": c, "reasons": reasons}); continue
        interests = {x.lower() for x in (student.interests or [])}
        tags = {x.lower() for x in (c.interest_tags or [])}
        interest = len(interests & tags) / max(len(tags), 1)
        goal = (student.career_goal or "").lower()
        career = 1.0 if any(k in goal and k in " ".join(tags) for k in ["ai", "machine learning", "data", "software", "nlp"]) else .5
        academic = max(0.0, min(1.0, (student.gpa or 0) / 4 - max(0, c.difficulty - 3) * .12))
        progression = .5 if list(graph.successors(c.code)) else 1.0
        semester_fit = 1.0 if c.semester <= student.current_semester + 1 else 0.0
        score = 100 * (WEIGHTS["interest"]*interest + WEIGHTS["career"]*career + WEIGHTS["academic"]*academic + WEIGHTS["progression"]*progression + WEIGHTS["semester"]*semester_fit)
        eligible.append({"course": c, "score": round(score, 1), "factors": {"interest": round(interest,2), "career": career, "academic": round(academic,2), "progression": progression, "semester": semester_fit}, "prerequisites": prereq["required"]})
    eligible.sort(key=lambda x: (-x["score"], x["course"].semester, x["course"].code))
    for rank, item in enumerate(eligible, 1): item["rank"] = rank
    return eligible, ineligible, graph

def plan_pathway(db: Session, student: Student, eligible, graph, horizons=4):
    by_code = {c.code: c for c in db.query(Course).all()}
    done = set(student.completed_courses or [])
    remaining = {c for c in graph.nodes if c not in done}
    score = {x["course"].code: x["score"] for x in eligible}
    semesters = []
    for offset in range(horizons):
        term = student.current_semester + offset
        credits, selected = 0, []
        ready = [code for code in remaining if set(nx.ancestors(graph, code)) <= done and by_code[code].availability and by_code[code].semester <= term + 1]
        ready.sort(key=lambda code: (-score.get(code, 50), by_code[code].semester, code))
        for code in ready:
            c = by_code[code]
            if credits + c.credits <= student.max_credits:
                selected.append({"code": code, "name": c.name, "credits": c.credits, "score": score.get(code, 50)})
                credits += c.credits
        if selected:
            semesters.append({"semester": term, "courses": selected, "credits": credits})
            done.update(x["code"] for x in selected); remaining -= set(x["code"] for x in selected)
        if not remaining: break
    return semesters

def public_course(c):
    return {"code":c.code,"name":c.name,"credits":c.credits,"semester":c.semester,"category":c.category,"interest_tags":c.interest_tags,"difficulty":c.difficulty,"availability":c.availability}
