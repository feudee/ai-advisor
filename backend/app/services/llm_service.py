import os

def explain(question: str, student: dict, results: dict) -> dict:
    """Use Claude only to verbalize deterministic results; retain a usable offline fallback."""
    key = os.getenv("ANTHROPIC_API_KEY")
    if key:
        try:
            from anthropic import Anthropic
            response = Anthropic(api_key=key).messages.create(
                model=os.getenv("CLAUDE_MODEL", "claude-haiku-4-5-20251001"), max_tokens=350,
                system="Explain only the structured advising facts supplied. Never change eligibility or invent courses. If a fact is absent, say so.",
                messages=[{"role":"user","content":f"Student: {student}\nComputed results: {results}\nQuestion: {question}"}],
            )
            return {"answer": response.content[0].text, "source": "claude"}
        except Exception:
            pass
    query = question.lower()
    aliases = {"ml": "machine learning", "nlp": "natural language processing", "cv": "computer vision", "dl": "deep learning"}
    query_terms = query + " " + " ".join(name for short, name in aliases.items() if short in query)
    recs = results.get("recommendations", [])
    blocked = results.get("ineligible", [])
    for item in recs:
        course = item["course"]
        if course["code"].lower() in query or course["name"].lower() in query_terms:
            return {"answer": f"{course['name']} ({course['code']}) is eligible and ranked #{item['rank']} with a score of {item['score']}/100. All recorded prerequisites are complete. The ranking reflects your stated interests, career goal, academic fit, and curriculum progression.", "source": "deterministic fallback"}
    for item in blocked:
        course = item["course"]
        if course["code"].lower() in query or course["name"].lower() in query_terms:
            return {"answer": f"{course['name']} ({course['code']}) is currently ineligible: {'; '.join(item['reasons'])}.", "source": "deterministic fallback"}
    if recs:
        top = recs[0]
        course = top["course"]
        return {"answer": f"Your highest-ranked eligible course is {course['name']} ({course['code']}) at #{top['rank']} with a score of {top['score']}/100. The ranking combines your interests, career goal, academic fit, prerequisite progression, and semester suitability. Ask about a course by name or code for its specific status.", "source": "deterministic fallback"}
    return {"answer": "The deterministic advising service found no eligible recommendations for the current profile and curriculum constraints.", "source": "deterministic fallback"}
