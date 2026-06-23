"""
Reasoning Generator: Factual explanations for candidate rankings
"""
import sys
sys.path.append('..')

from features.skill_score import SkillScorer
from features.experience_score import ExperienceScorer


class ReasoningGenerator:
    def __init__(self):
        self.skill_scorer = SkillScorer()
        self.exp_scorer = ExperienceScorer()
    
    def generate(self, candidate, jd_requirements, scores, behavioral_data=None):
        """
        Generate factual reasoning for candidate ranking
        
        Args:
            candidate: Dict with candidate_id, profile_text
            jd_requirements: Dict with skills[], experience, domain, leadership
            scores: Dict with all component scores
            behavioral_data: Dict with engagement metrics (optional)
        
        Returns:
            List of factual reasoning statements
        """
        reasons = []
        profile_text = candidate['profile_text']
        
        # Skill match reasoning
        reasons.extend(self._skill_reasoning(profile_text, jd_requirements, scores))
        
        # Experience reasoning
        reasons.extend(self._experience_reasoning(profile_text, jd_requirements, scores))
        
        # Career progression reasoning
        reasons.extend(self._career_reasoning(profile_text, scores))
        
        # Behavioral reasoning
        if behavioral_data and candidate['candidate_id'] in behavioral_data:
            reasons.extend(self._behavioral_reasoning(behavioral_data[candidate['candidate_id']], scores))
        
        # Platform activity
        reasons.extend(self._platform_reasoning(profile_text))
        
        return reasons
    
    def _skill_reasoning(self, profile_text, jd_requirements, scores):
        """Generate skill match reasoning"""
        reasons = []
        required_skills = jd_requirements.get('skills', [])
        
        if not required_skills:
            return reasons
        
        candidate_skills = self.skill_scorer.extract_skills(profile_text)
        matched = candidate_skills & set(required_skills)
        
        if len(matched) >= 4:
            top_matches = list(matched)[:4]
            reasons.append(f"Strong match on {', '.join(top_matches)}.")
        elif len(matched) >= 2:
            reasons.append(f"Relevant skills in {', '.join(list(matched)[:3])}.")
        elif len(matched) == 1:
            reasons.append(f"Has {list(matched)[0]} experience.")
        
        return reasons
    
    def _experience_reasoning(self, profile_text, jd_requirements, scores):
        """Generate experience reasoning"""
        reasons = []
        required_years = jd_requirements.get('experience', 0)
        
        if required_years == 0:
            return reasons
        
        candidate_years = self.exp_scorer.extract_years(profile_text)
        
        if candidate_years >= required_years:
            reasons.append(f"{candidate_years} years relevant experience.")
        elif candidate_years > 0:
            reasons.append(f"{candidate_years} years experience in field.")
        
        return reasons
    
    def _career_reasoning(self, profile_text, scores):
        """Generate career progression reasoning"""
        reasons = []
        profile_lower = profile_text.lower()
        
        # Check for promotions
        if any(word in profile_lower for word in ['promoted', 'promotion', 'advanced to', 'elevated to']):
            reasons.append("Demonstrated career progression through promotions.")
        
        # Check for leadership levels
        if 'lead' in profile_lower or 'principal' in profile_lower:
            reasons.append("Senior-level engineering experience.")
        elif 'senior' in profile_lower:
            reasons.append("Senior engineer with proven track record.")
        
        return reasons
    
    def _behavioral_reasoning(self, metrics, scores):
        """Generate behavioral engagement reasoning"""
        reasons = []
        
        response_rate = metrics.get('recruiter_response_rate', 0)
        completion_rate = metrics.get('interview_completion_rate', 0)
        github_activity = metrics.get('github_activity', 0)
        
        if response_rate >= 0.70:
            reasons.append("High recruiter engagement rate.")
        
        if completion_rate >= 0.75:
            reasons.append("Strong interview completion history.")
        
        if github_activity >= 40:
            reasons.append("Active technical contributor on GitHub.")
        
        return reasons
    
    def _platform_reasoning(self, profile_text):
        """Generate platform activity reasoning"""
        reasons = []
        
        # Extract open to work status
        if 'Open to work: True' in profile_text:
            reasons.append("Currently open to opportunities.")
        
        # Extract notice period
        if 'Notice: 30 days' in profile_text:
            reasons.append("Available to join within 30 days.")
        elif 'Notice: 60 days' in profile_text:
            reasons.append("Available to join within 60 days.")
        
        # GitHub activity from profile
        if 'GitHub activity:' in profile_text and 'not linked' not in profile_text:
            reasons.append("Active on technical platforms.")
        
        return reasons


if __name__ == "__main__":
    generator = ReasoningGenerator()
    
    # Test candidate
    candidate = {
        'candidate_id': 'CAND_0000031',
        'profile_text': """
        Recommendation Systems Engineer with 6.0 years of experience.
        Strong background in Python, FAISS, Machine Learning, and Information Retrieval.
        Started as Engineer, promoted to Senior, now Lead at Swiggy.
        Open to work: True | Notice: 60 days
        GitHub activity: 32.6/100 | Recruiter response rate: 91% | Interview completion: 60%
        """
    }
    
    jd_requirements = {
        'skills': ['Python', 'FAISS', 'Machine Learning', 'Elasticsearch'],
        'experience': 5,
        'domain': 'Search',
        'leadership': False
    }
    
    scores = {
        'skill_score': 0.75,
        'experience_score': 1.0,
        'career_score': 0.85,
        'behavior_score': 0.78
    }
    
    behavioral_data = {
        'CAND_0000031': {
            'github_activity': 32,
            'recruiter_response_rate': 0.91,
            'interview_completion_rate': 0.60,
            'saved_by_recruiters_30d': 15
        }
    }
    
    reasons = generator.generate(candidate, jd_requirements, scores, behavioral_data)
    
    print("=== CANDIDATE REASONING ===\n")
    for reason in reasons:
        print(f"• {reason}")
