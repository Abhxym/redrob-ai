"""
RedRob AI Recruiter - Complete Demo Flow
Production-ready end-to-end candidate ranking system
"""
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from preprocessing.jd_parser import JDParser
from retrieval.hybrid_retrieval import HybridRetriever
from ranking.score_candidates import CandidateRanker
from reasoning.generate_reasoning import ReasoningGenerator
from reasoning.explain import CandidateExplainer
from outputs.submission_generator import SubmissionGenerator


class RedRobRecruiter:
    """
    Complete recruitment pipeline:
    JD → Parse → Retrieve → Score → Rank → Explain → Submit
    """
    
    def __init__(self):
        # Initialize all components
        self.jd_parser = JDParser()
        self.retriever = HybridRetriever()
        self.ranker = CandidateRanker()
        self.reasoning_gen = ReasoningGenerator()
        self.explainer = CandidateExplainer()
        self.submission_gen = SubmissionGenerator()
        
        print("✓ RedRob AI Recruiter initialized")
    
    def load_candidates(self):
        """Load candidate profiles"""
        with open('data/candidate_profiles.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def load_behavioral_data(self):
        """Extract behavioral data from candidate profiles"""
        candidates = self.load_candidates()
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
            
            # Saved by recruiters (use github as proxy)
            saved = int(github / 2) if github > 0 else 0
            
            behavioral_data[candidate_id] = {
                'github_activity': github,
                'recruiter_response_rate': response_rate,
                'interview_completion_rate': completion_rate,
                'saved_by_recruiters_30d': saved
            }
        
        return behavioral_data
    
    def run(self, jd_text: str, jd_id: str = 'JD001', top_k: int = 100, 
            verbose: bool = True) -> dict:
        """
        Complete pipeline execution
        
        Args:
            jd_text: Job description text
            jd_id: Job description identifier
            top_k: Number of candidates to return
            verbose: Print progress messages
        
        Returns:
            dict: Complete results with ranked candidates and paths
        """
        if verbose:
            print("\n" + "="*80)
            print("REDROB AI RECRUITER - DEMO FLOW")
            print("="*80 + "\n")
        
        # Step 1: Parse JD
        if verbose:
            print("Step 1: Parsing Job Description...")
        jd_requirements = self.jd_parser.parse(jd_text)
        if verbose:
            print(f"  ✓ Skills: {len(jd_requirements['skills'])} identified")
            print(f"  ✓ Experience: {jd_requirements['experience']} years")
            print(f"  ✓ Domain: {jd_requirements['domain']}")
            print(f"  ✓ Leadership: {jd_requirements['leadership']}\n")
        
        # Step 2: Hybrid Retrieval (BM25 + FAISS)
        if verbose:
            print("Step 2: Hybrid Retrieval (BM25 + FAISS + RRF)...")
        candidates_pool = self.retriever.search(jd_text, top_k=100)
        if verbose:
            print(f"  ✓ Retrieved: {len(candidates_pool)} candidates\n")
        
        # Step 3: Load candidate data
        if verbose:
            print("Step 3: Loading candidate profiles...")
        all_candidates = self.load_candidates()
        candidate_map = {c['candidate_id']: c for c in all_candidates}
        
        # Enrich with profile text
        for candidate in candidates_pool:
            candidate['profile_text'] = candidate_map[candidate['candidate_id']]['profile_text']
        
        # Step 4: Load behavioral data
        if verbose:
            print("Step 4: Extracting behavioral signals...")
        behavioral_data = self.load_behavioral_data()
        if verbose:
            print(f"  ✓ Loaded: {len(behavioral_data)} candidate metrics\n")
        
        # Step 5: Feature matching and scoring
        if verbose:
            print("Step 5: Feature engineering and scoring...")
        ranked_candidates = self.ranker.rank_candidates(
            candidates_pool,
            jd_requirements,
            behavioral_data,
            top_k=top_k
        )
        if verbose:
            print(f"  ✓ Ranked: Top {len(ranked_candidates)} candidates\n")
        
        # Step 6: Generate reasoning
        if verbose:
            print("Step 6: Generating explanations...")
        
        results = []
        for ranked in ranked_candidates:
            candidate_id = ranked['candidate_id']
            candidate = candidate_map[candidate_id]
            
            # Generate simple reasoning
            reasons = self.reasoning_gen.generate(
                candidate,
                jd_requirements,
                ranked,
                behavioral_data
            )
            
            ranked['reasoning'] = ' | '.join(reasons)
            results.append(ranked)
        
        if verbose:
            print(f"  ✓ Generated reasoning for all candidates\n")
        
        # Step 7: Generate submission
        if verbose:
            print("Step 7: Generating submission CSV...")
        
        submission_path = self.submission_gen.generate(
            results,
            jd_id=jd_id,
            filename='submission.csv'
        )
        
        detailed_path = self.submission_gen.generate_detailed(
            results,
            jd_id=jd_id,
            filename='submission_detailed.csv'
        )
        
        # Step 8: Validate submission
        if verbose:
            print("\nStep 8: Validating submission...")
        
        validation = self.submission_gen.validate_submission(submission_path)
        
        if verbose:
            if validation['valid']:
                print("  ✓ Validation PASSED")
            else:
                print("  ✗ Validation FAILED")
                for error in validation['errors']:
                    print(f"    {error}")
        
        if verbose:
            print("\n" + "="*80)
            print("PIPELINE COMPLETE")
            print("="*80 + "\n")
            print(f"Results:")
            print(f"  • Ranked candidates: {len(results)}")
            print(f"  • Submission CSV: {submission_path}")
            print(f"  • Detailed CSV: {detailed_path}")
            print(f"  • Validation: {'PASSED' if validation['valid'] else 'FAILED'}")
            print()
        
        return {
            'jd_requirements': jd_requirements,
            'ranked_candidates': results,
            'submission_path': submission_path,
            'detailed_path': detailed_path,
            'validation': validation
        }
    
    def print_top_candidates(self, results: dict, top_n: int = 10):
        """Print top N candidates with explanations"""
        candidates = results['ranked_candidates'][:top_n]
        
        print("\n" + "="*80)
        print(f"TOP {top_n} CANDIDATES")
        print("="*80 + "\n")
        
        for i, candidate in enumerate(candidates, 1):
            print(f"Rank {i}: {candidate['candidate_id']}")
            print(f"  Overall Score: {candidate['final_score']:.3f}")
            print(f"  Breakdown:")
            print(f"    • Semantic:    {candidate['semantic_score']:.3f}")
            print(f"    • Skills:      {candidate['skill_score']:.3f}")
            print(f"    • Experience:  {candidate['experience_score']:.3f}")
            print(f"    • Behavior:    {candidate['behavior_score']:.3f}")
            print(f"    • Career:      {candidate['career_score']:.3f}")
            print(f"  Reasoning:")
            for reason in candidate['reasoning'].split(' | '):
                if reason:
                    print(f"    • {reason}")
            print()


def main():
    """Main entry point"""
    # Initialize recruiter
    recruiter = RedRobRecruiter()
    
    # Sample JD (can be loaded from file)
    jd_text = """
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
    
    # Run complete pipeline
    results = recruiter.run(jd_text, jd_id='JD001', top_k=100, verbose=True)
    
    # Display top candidates
    recruiter.print_top_candidates(results, top_n=10)
    
    return results


if __name__ == "__main__":
    main()
