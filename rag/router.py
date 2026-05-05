def classify_query(question: str):
    q = question.lower()

    if any(k in q for k in ["case name", "date", "judge", "title"]):
        return "metadata"

    return "semantic"