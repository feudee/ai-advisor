import networkx as nx
from sqlalchemy.orm import Session
from ..models import Course, Prerequisite

def build_graph(db: Session):
    graph = nx.DiGraph()
    graph.add_nodes_from(c.code for c in db.query(Course).all())
    # Edge direction is prerequisite -> dependent course.
    graph.add_edges_from((p.prerequisite_code, p.course_code) for p in db.query(Prerequisite).all())
    if not nx.is_directed_acyclic_graph(graph):
        raise ValueError("Curriculum prerequisites contain a cycle")
    return graph

def prerequisite_status(graph, code: str, completed: set[str]):
    # Treat every upstream dependency as required. This also protects against
    # inconsistent imported histories where an intermediate course is recorded
    # complete but its own prerequisite history is missing.
    required = nx.ancestors(graph, code)
    return {"required": sorted(required), "missing": sorted(required - completed), "satisfied": required <= completed}

def dependents(graph, code: str):
    return sorted(nx.descendants(graph, code))
