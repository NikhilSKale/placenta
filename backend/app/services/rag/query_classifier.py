"""Query classifier: detect intent, company, topics, and document category."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional


KNOWN_COMPANIES = {
    "ivp": "IVP",
    "indus valley": "IVP",
    "network marvels": "Network Marvels",
    "nm": "Network Marvels",
    "iss": "ISS Stoxx",
    "iss stoxx": "ISS Stoxx",
    "stoxx": "ISS Stoxx",
    "nomura": "Nomura",
    "tcs": "TCS",
    "tcs digital": "TCS Digital",
    "quantiphi": "Quantiphi",
    "deloitte": "Deloitte",
}

POLICY_KEYWORDS = [
    "policy", "rule", "regulation", "vesit", "placement policy",
    "eligibility rule", "official", "institute", "restriction",
    "violation", "internship policy", "handbook",
]

TOPIC_KEYWORDS = {
    "sql": "SQL",
    "dbms": "DBMS",
    "database": "DBMS",
    "oops": "OOP",
    "oop": "OOP",
    "object oriented": "OOP",
    "os": "OS",
    "operating system": "OS",
    "networking": "Networking",
    "network": "Networking",
    "dsa": "DSA",
    "data structure": "DSA",
    "algorithm": "DSA",
    "java": "Java",
    "python": "Python",
    "aptitude": "Aptitude",
    "assessment": "Aptitude",
    "test": "Aptitude",
    "coding": "Coding",
    "ctc": "CTC",
    "salary": "CTC",
    "package": "CTC",
    "stipend": "Stipend",
    "internship": "Internship",
    "ppo": "PPO",
    "hackathon": "Hackathon",
    "hr": "HR",
    "technical": "Technical Interview",
    "cgpa": "CGPA",
    "eligibility": "Eligibility",
    "ai": "AI/ML",
    "machine learning": "AI/ML",
}


@dataclass
class QueryAnalysis:
    original_query: str
    detected_company: Optional[str] = None
    detected_topics: List[str] = field(default_factory=list)
    doc_category: str = "all"  # "all", "placement_experience", "policy"
    intent: str = "general"  # "factual", "comparison", "policy", "preparation", "general"
    chroma_where: Optional[dict] = None
    is_comparison: bool = False


def classify_query(query: str) -> QueryAnalysis:
    """Classify a query and return retrieval metadata."""
    q = query.lower()
    analysis = QueryAnalysis(original_query=query)

    # Detect company
    for keyword, canonical in KNOWN_COMPANIES.items():
        if keyword in q:
            analysis.detected_company = canonical
            break

    # Detect topics
    found_topics = []
    for keyword, topic in TOPIC_KEYWORDS.items():
        if keyword in q and topic not in found_topics:
            found_topics.append(topic)
    analysis.detected_topics = found_topics

    # Detect intent
    if any(k in q for k in POLICY_KEYWORDS):
        analysis.doc_category = "policy"
        analysis.intent = "policy"
    elif any(k in q for k in ["compare", "comparison", "vs", "versus", "difference between", "both"]):
        analysis.is_comparison = True
        analysis.intent = "comparison"
    elif any(k in q for k in ["prepare", "preparation", "tips", "resources", "study", "recommend"]):
        analysis.intent = "preparation"
    elif any(k in q for k in ["how many", "what is", "what was", "which", "who", "when", "where", "did"]):
        analysis.intent = "factual"
    else:
        analysis.intent = "general"

    if analysis.doc_category != "policy":
        analysis.doc_category = "placement_experience"

    # Build ChromaDB where filter
    if analysis.detected_company and not analysis.is_comparison:
        analysis.chroma_where = {"company": {"$eq": analysis.detected_company}}

    return analysis

