"""
Ranking Engine: Weighted scoring and Top 100 candidate selection
"""
import sys
sys.path.append('..')

from features.skill_score import SkillScorer
from features.experience_score import ExperienceScorer
from features.career_score import CareerScorer
from features.behavior_score import BehaviorScorer


class CandidateRanker:
    def __init__(self):
        self.skill_scorer = SkillScorer()
        self.exp_scorer = ExperienceScorer()
        self.career_scorer = CareerScorer()
        self.behavior_scorer = BehaviorScorer()
        
        # Weights
        self.weights = {
            'semantic': 0.40,
            'skill': 0.25,
            'experience': 0.15,
            'behavior': 0.10,
            'career': 0.10
        }
    
    def score_candidate(self, candidate, jd_requirements, behavioral_data=None):
        """
        Compute final score for single candidate
        
        Args:
            candidate: Dict with 'candidate_id', 'profile_text', 'semantic_score'
            jd_requirements: Dict with 'skills' (list), 'experience' (int)
            behavioral_data: Dict with engagement metrics (optional)
        
        Returns:
            Dict with all scores and final_score
        """
        profile_text = candidate['profile_text']
        semantic_score = candidate.get('semantic_score', candidate.get('rrf_score', 0.0))
        
        # Compute feature scores
        skill_score = self.skill_scorer.compute_score(
            profile_text, 
            jd_requirements.get('skills', [])
        )
        
        exp_score = self.exp_scorer.compute_score(
            profile_text,
            jd_requirements.get('experience', 0)
        )
        
        career_score = self.career_scorer.compute_score(profile_text)
        
        # Behavioral score (default to 0.5 if no data)
        if behavioral_data and candidate['candidate_id'] in behavioral_data:
            metrics = behavioral_data[candidate['candidate_id']]
            behavior_score = self.behavior_scorer.compute_score(**metrics)
        else:
            behavior_score = 0.5
        
        # Final weighted score
        final_score = (
            self.weights['semantic'] * semantic_score +
            self.weights['skill'] * skill_score +
            self.weights['experience'] * exp_score +
            self.weights['behavior'] * behavior_score +
            self.weights['career'] * career_score
        )
        
        return {
            'candidate_id': candidate['candidate_id'],
            'final_score': final_score,
            'semantic_score': semantic_score,
            'skill_score': skill_score,
            'experience_score': exp_score,
            'behavior_score': behavior_score,
            'career_score': career_score
        }
    
    def rank_candidates(self, candidates, jd_requirements, behavioral_data=None, top_k=100):
        """
        Score and rank all candidates, return Top K
        
        Args:
            candidates: List of candidate dicts from hybrid retrieval
            jd_requirements: Dict with 'skills', 'experience' from JD parser
            behavioral_data: Dict mapping candidate_id to engagement metrics
            top_k: Number of top candidates to return (default 100)
        
        Returns:
            List of scored and ranked candidates (Top K)
        """
        scored = []
        for candidate in candidates:
            score_result = self.score_candidate(candidate, jd_requirements, behavioral_data)
            scored.append(score_result)
        
        # Sort by final_score descending
        ranked = sorted(scored, key=lambda x: x['final_score'], reverse=True)
        
        return ranked[:top_k]


if __name__ == "__main__":
    # Test with mock data
    ranker = CandidateRanker()
    
    candidates = [
        {
            'candidate_id': 'C001',
            'profile_text': 'Senior ML Engineer with 8 years experience. Promoted from Engineer to Senior to Lead. Expert in Python, PyTorch, FAISS, AWS.',
            'rrf_score': 0.028
        },
        {
            'candidate_id': 'C002',
            'profile_text': 'Engineer with 3 years in backend. Skilled in Java, Spring Boot, MySQL.',
            'rrf_score': 0.015
        },
        {
            'candidate_id': 'C003',
            'profile_text': 'Principal Engineer with 12 years experience. Built search systems with Elasticsearch and Python.',
            'rrf_score': 0.025
        }
    ]
    
    jd_requirements = {
        'skills': ['Python', 'PyTorch', 'FAISS', 'AWS', 'Machine Learning'],
        'experience': 5
    }
    
    behavioral_data = {
        'C001': {
            'github_activity': 60,
            'recruiter_response_rate': 0.85,
            'interview_completion_rate': 0.90,
            'saved_by_recruiters_30d': 15
        },
        'C003': {
            'github_activity': 40,
            'recruiter_response_rate': 0.70,
            'interview_completion_rate': 0.80,
            'saved_by_recruiters_30d': 20
        }
    }
    
    ranked = ranker.rank_candidates(candidates, jd_requirements, behavioral_data)
    
    print("=== RANKED CANDIDATES ===\n")
    for i, candidate in enumerate(ranked, 1):
        print(f"Rank {i}: {candidate['candidate_id']}")
        print(f"  Final Score: {candidate['final_score']:.3f}")
        print(f"  - Semantic: {candidate['semantic_score']:.3f} (40%)")
        print(f"  - Skill: {candidate['skill_score']:.3f} (25%)")
        print(f"  - Experience: {candidate['experience_score']:.3f} (15%)")
        print(f"  - Behavior: {candidate['behavior_score']:.3f} (10%)")
        print(f"  - Career: {candidate['career_score']:.3f} (10%)")
        print()
