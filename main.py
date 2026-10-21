"""
RedRob AI Recruiter - End-to-End Pipeline
"""
import json
import csv
from preprocessing.jd_parser import JDParser
from retrieval.hybrid_retrieval import HybridRetriever
from ranking.score_candidates import CandidateRanker
from reasoning.generate_reasoning import ReasoningGenerator


def load_candidates():
    """Load candidate profiles"""
    with open('data/candidate_profiles.json', 'r', encoding='utf-8') as f:
        return json.load(f)


def load_behavioral_data():
    """Extract behavioral data from candidate profiles"""
    candidates = load_candidates()
    behavioral_data = {}
    
    for candidate in candidates:
        profile_text = candidate['profile_text']
        candidate_id = candidate['candidate_id']
        
        # Extract GitHub activity
        github = 0
        if 'GitHub activity:' in profile_text and 'not linked' not in profile_text:
            try:
                github_str = profile_text.split('GitHub activity:')[1].split('/')[0].strip()
                github = float(github_str)
            except:
                github = 0
        
        # Extract recruiter response rate
        response_rate = 0.5
        if 'Recruiter response rate:' in profile_text:
            try:
                rate_str = profile_text.split('Recruiter response rate:')[1].split('%')[0].strip()
                response_rate = float(rate_str) / 100
            except:
                response_rate = 0.5
        
        # Extract interview completion rate
        completion_rate = 0.5
        if 'Interview completion:' in profile_text:
            try:
                comp_str = profile_text.split('Interview completion:')[1].split('%')[0].strip()
                completion_rate = float(comp_str) / 100
            except:
                completion_rate = 0.5
        
        # Saved by recruiters (mock - use github as proxy)
        saved = int(github / 2) if github > 0 else 0
        
        behavioral_data[candidate_id] = {
            'github_activity': github,
            'recruiter_response_rate': response_rate,
            'interview_completion_rate': completion_rate,
            'saved_by_recruiters_30d': saved
        }
    
    return behavioral_data


def main(jd_text, top_k=10):
    """
    End-to-End Pipeline
    
    Args:
        jd_text: Job description text
        top_k: Number of top candidates to return
    
    Returns:
        List of ranked candidates with scores and reasoning
    """
    print("=== RedRob AI Recruiter ===\n")
    
    # Step 1: Parse JD
    print("Step 1: Parsing Job Description...")
    jd_parser = JDParser()
    jd_requirements = jd_parser.parse(jd_text)
    print(f"  Skills: {len(jd_requirements['skills'])} identified")
    print(f"  Experience: {jd_requirements['experience']} years")
    print(f"  Domain: {jd_requirements['domain']}")
    print(f"  Leadership: {jd_requirements['leadership']}\n")
    
    # Step 2: Hybrid Retrieval
    print("Step 2: Hybrid Retrieval (BM25 + FAISS)...")
    retriever = HybridRetriever()
    candidates_pool = retriever.search(jd_text)['results']  # RRF-fused top 100
    print(f"  Retrieved: {len(candidates_pool)} candidates\n")
    
    # Step 3: Load full candidate data
    print("Step 3: Loading candidate profiles...")
    all_candidates = load_candidates()
    candidate_map = {c['candidate_id']: c for c in all_candidates}
    
    # Enrich with profile text
    for candidate in candidates_pool:
        candidate['profile_text'] = candidate_map[candidate['candidate_id']]['profile_text']
    
    # Step 4: Load behavioral data
    print("Step 4: Loading behavioral signals...")
    behavioral_data = load_behavioral_data()
    print(f"  Loaded: {len(behavioral_data)} candidate metrics\n")
    
    # Step 5: Ranking
    print("Step 5: Scoring and ranking candidates...")
    ranker = CandidateRanker()
    ranked_candidates = ranker.rank_candidates(
        candidates_pool,
        jd_requirements,
        behavioral_data,
        top_k=top_k
    )
    print(f"  Ranked: Top {len(ranked_candidates)} candidates\n")
    
    # Step 6: Generate reasoning
    print("Step 6: Generating reasoning...")
    reasoning_gen = ReasoningGenerator()
    
    results = []
    for ranked in ranked_candidates:
        candidate_id = ranked['candidate_id']
        candidate = candidate_map[candidate_id]
        
        reasons = reasoning_gen.generate(
            candidate,
            jd_requirements,
            ranked,
            behavioral_data
        )
        
        results.append({
            'candidate_id': candidate_id,
            'final_score': ranked['final_score'],
            'semantic_score': ranked['semantic_score'],
            'skill_score': ranked['skill_score'],
            'experience_score': ranked['experience_score'],
            'behavior_score': ranked['behavior_score'],
            'career_score': ranked['career_score'],
            'reasoning': ' | '.join(reasons)
        })
    
    print("  Generated reasoning for all candidates\n")
    
    return results


def save_to_csv(results, filename='output/ranked_candidates.csv'):
    """Save results to CSV"""
    import os
    os.makedirs('output', exist_ok=True)
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'candidate_id', 'final_score', 'semantic_score', 'skill_score',
            'experience_score', 'behavior_score', 'career_score', 'reasoning'
        ])
        writer.writeheader()
        writer.writerows(results)
    
    print(f"Results saved to: {filename}")


def print_results(results):
    """Pretty print top candidates"""
    print("\n" + "="*80)
    print("TOP CANDIDATES")
    print("="*80 + "\n")
    
    for i, result in enumerate(results, 1):
        print(f"Rank {i}: {result['candidate_id']}")
        print(f"  Final Score: {result['final_score']:.3f}")
        print(f"  Breakdown:")
        print(f"    • Semantic: {result['semantic_score']:.3f}")
        print(f"    • Skills: {result['skill_score']:.3f}")
        print(f"    • Experience: {result['experience_score']:.3f}")
        print(f"    • Behavior: {result['behavior_score']:.3f}")
        print(f"    • Career: {result['career_score']:.3f}")
        print(f"  Reasoning:")
        for reason in result['reasoning'].split(' | '):
            if reason:
                print(f"    • {reason}")
        print()


if __name__ == "__main__":
    # Sample Job Description
    jd = """
    Senior Machine Learning Engineer - Search & Ranking
    
    We're looking for an experienced ML engineer to build and scale our search ranking systems.
    
    Requirements:
    - 5+ years of experience in machine learning and software engineering
    - Strong proficiency in Python, PyTorch, and TensorFlow
    - Experience with search systems: FAISS, Elasticsearch, or similar vector databases
    - Hands-on experience with ranking algorithms and recommendation systems
    - Knowledge of NLP, embeddings, and information retrieval
    - Experience with MLOps tools and deployment pipelines
    - Strong software engineering fundamentals
    
    Nice to have:
    - Experience with LLMs and fine-tuning
    - Knowledge of distributed systems
    - Contributions to open-source ML projects
    
    This is a senior IC role working on high-impact ML systems.
    """
    
    # Run pipeline
    results = main(jd, top_k=10)
    
    # Display results
    print_results(results)
    
    # Save to CSV
    save_to_csv(results)
