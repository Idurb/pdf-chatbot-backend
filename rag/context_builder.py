def build_context(chunks):
    cleaned = [c.replace("\n", " ").strip() for c in chunks]
    return "\n\n".join(cleaned[:5])