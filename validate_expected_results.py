#!/usr/bin/env python
"""
Validation: Confirm FAISS retrieval returns sensible ML engineer matches

Expected top 5 matches for query:
"Need machine learning engineer with Python and recommendation systems experience"

Should match candidates with ML/recommendation systems experience.
Should NOT match frontend developers or non-technical roles.
"""

import json

# Load candidate profiles
with open('data/candidate_profiles.json', 'r', encoding='utf-8') as f:
    candidates = json.load(f)

# Expected good matches (have ML, recommendation systems, or Python expertise)
expected_matches = {
    'CAND_0000031': 'Recommendation Systems Engineer | Search, Ranking & Retrieval',
    'CAND_0000010': 'Data Engineer | Data pipelines & analytics',
    'CAND_0000001': 'Backend Engineer | SQL, Spark, Cloud',
    'CAND_0000043': 'Cloud Engineer | Full-stack development',
    'CAND_0000027': 'DevOps Engineer | Cloud & DevOps',
    'CAND_0000015': 'Software Engineer | Cloud & DevOps',
    'CAND_0000032': '.NET Developer | Full-stack development',
    'CAND_0000035': 'Full Stack Developer | Backend systems & APIs',
}

# Bad matches (should NOT appear in top 5)
bad_matches = {
    'CAND_0000014': 'Frontend Engineer | Full-stack development',
    'CAND_0000018': 'Frontend Engineer | Full-stack development',
    'CAND_0000025': 'Frontend Engineer | Cloud & DevOps',
    'CAND_0000044': 'Frontend Engineer | Backend systems & APIs',
}

print("=" * 70)
print("FAISS RETRIEVAL VALIDATION TEST")
print("=" * 70)

print("\nQuery: 'Need machine learning engineer with Python and recommendation systems experience.'")

print("\n✓ EXPECTED GOOD MATCHES (Should be in top 5):")
print("-" * 70)
for cid, headline in sorted(expected_matches.items()):
    for candidate in candidates:
        if candidate['candidate_id'] == cid:
            profile = candidate['profile_text']
            has_ml = any(keyword in profile.lower() for keyword in ['ml', 'machine learning', 'python', 'recommendation'])
            has_recommendation = 'recommendation' in profile.lower()
            marker = "⭐ PRIORITY" if has_recommendation else "✓"
            print(f"{marker} {cid}: {headline}")
            break

print("\n✗ BAD MATCHES (Should NOT be in top 5):")
print("-" * 70)
for cid, headline in sorted(bad_matches.items()):
    for candidate in candidates:
        if candidate['candidate_id'] == cid:
            print(f"✗ {cid}: {headline}")
            break

print("\n" + "=" * 70)
print("SUCCESS CRITERIA")
print("=" * 70)
print("""
The FAISS index returns sensible results if:
1. Top matches include CAND_0000031 (Recommendation Systems Engineer)
2. Most of top 5 are from expected_matches list
3. None are from bad_matches list
4. Results reflect semantic similarity to "machine learning + Python + recommendations"

Run: python retrieval/faiss_search.py
And verify output matches these expectations.
""")

# Show key skills that should be matched
print("Key skills to look for in top matches:")
print("-" * 70)
ml_skills = ['recommendation', 'embeddings', 'faiss', 'llm', 'nlp', 'machine learning',
             'python', 'data science', 'deep learning', 'neural', 'pinecone']
for skill in ml_skills:
    matching = [c['candidate_id'] for c in candidates if skill.lower() in c['profile_text'].lower()]
    if matching:
        print(f"  {skill.upper()}: {len(matching)} candidates - {matching[:5]}...")
