"""
Explainability Layer - Detailed reasoning with strengths and risks
"""
import sys
sys.path.append('..')

from features.skill_score import SkillScorer
from features.experience_score import ExperienceScorer


class CandidateExplainer:
    def __init__(self):
        self.skill_scorer = SkillScorer()
        self.exp_scorer = ExperienceScorer()
    
    def explain(self, candidate, jd_requirements, scores, behavioral_data=None):
        """
        Generate comprehensive explanation for candidate ranking
        
        Args:
            candidate: Dict with candidate_id, profile_text
            jd_requirements: Dict with skills[], experience, domain, leadership
            scores: Dict with all component scores
            behavioral_data: Dict with engagement metrics (optional)
        
        Returns:
            dict: Structured explanation with strengths and risks
        """
        profile_text = candidate['profile_text']
        
        strengths = []
        risks = []
        
        # Skill match analysis
        skill_analysis = self._analyze_skills(profile_text, jd_requirements, scores)
        strengths.extend(skill_analysis['strengths'])
        risks.extend(skill_analysis['risks'])
        
        # Experience analysis
        exp_analysis = self._analyze_experience(profile_text, jd_requirements, scores)
        strengths.extend(exp_analysis['strengths'])
        risks.extend(exp_analysis['risks'])
        
        # Career progression analysis
        career_analysis = self._analyze_career(profile_text, scores)
        strengths.extend(career_analysis['strengths'])
        risks.extend(career_analysis['risks'])
        
        # Behavioral analysis
        if behavioral_data and candidate['candidate_id'] in behavioral_data:
            behavior_analysis = self._analyze_behavior(behavioral_data[candidate['candidate_id']], scores)
            strengths.extend(behavior_analysis['strengths'])
            risks.extend(behavior_analysis['risks'])
        
        # Availability analysis
        avail_analysis = self._analyze_availability(profile_text)
        strengths.extend(avail_analysis['strengths'])
        risks.extend(avail_analysis['risks'])
        
        return {
            'candidate_id': candidate['candidate_id'],
            'overall_score': scores.get('final_score', 0.0),
            'strengths': strengths,
            'risks': risks,
            'summary': self._generate_summary(strengths, risks, scores)
        }
    
    def _analyze_skills(self, profile_text, jd_requirements, scores):
        """Analyze skill match"""
        strengths = []
        risks = []
        
        required_skills = jd_requirements.get('skills', [])
        if not required_skills:
            return {'strengths': strengths, 'risks': risks}
        
        candidate_skills = self.skill_scorer.extract_skills(profile_text)
        matched = candidate_skills & set(required_skills)
        missing = set(required_skills) - candidate_skills
        
        # Strengths
        match_count = len(matched)
        required_count = len(required_skills)
        
        if match_count >= required_count * 0.8:
            strengths.append(f"✓ Matches {match_count}/{required_count} required skills")
            if match_count >= 5:
                top_skills = ', '.join(list(matched)[:5])
                strengths.append(f"✓ Strong expertise in {top_skills}")
        elif match_count >= required_count * 0.5:
            strengths.append(f"✓ Relevant skills: {', '.join(list(matched)[:3])}")
        
        # Risks
        if missing and len(missing) <= 3:
            risks.append(f"⚠ Missing: {', '.join(list(missing))}")
        elif len(missing) > 3:
            risks.append(f"⚠ Limited match on {len(missing)} required skills")
        
        return {'strengths': strengths, 'risks': risks}
    
    def _analyze_experience(self, profile_text, jd_requirements, scores):
        """Analyze experience level"""
        strengths = []
        risks = []
        
        required_years = jd_requirements.get('experience', 0)
        candidate_years = self.exp_scorer.extract_years(profile_text)
        
        if candidate_years >= required_years:
            strengths.append(f"✓ {candidate_years} years relevant experience")
            if candidate_years >= required_years * 1.5:
                strengths.append(f"✓ Senior-level experience ({candidate_years} years)")
        elif candidate_years > 0:
            gap = required_years - candidate_years
            risks.append(f"⚠ {gap} years below required experience")
        
        return {'strengths': strengths, 'risks': risks}
    
    def _analyze_career(self, profile_text, scores):
        """Analyze career progression"""
        strengths = []
        risks = []
        
        profile_lower = profile_text.lower()
        
        # Promotions
        if any(word in profile_lower for word in ['promoted', 'promotion', 'advanced to']):
            strengths.append("✓ Demonstrated career progression")
        
        # Leadership
        if 'lead' in profile_lower or 'principal' in profile_lower:
            strengths.append("✓ Leadership experience")
        elif 'senior' in profile_lower:
            strengths.append("✓ Senior-level role")
        else:
            risks.append("⚠ Limited seniority indicators")
        
        return {'strengths': strengths, 'risks': risks}
    
    def _analyze_behavior(self, metrics, scores):
        """Analyze behavioral signals"""
        strengths = []
        risks = []
        
        response_rate = metrics.get('recruiter_response_rate', 0)
        completion_rate = metrics.get('interview_completion_rate', 0)
        github_activity = metrics.get('github_activity', 0)
        
        # Strengths
        if response_rate >= 0.70:
            strengths.append(f"✓ High recruiter response rate ({int(response_rate * 100)}%)")
        
        if completion_rate >= 0.75:
            strengths.append(f"✓ Strong interview completion ({int(completion_rate * 100)}%)")
        
        if github_activity >= 40:
            strengths.append(f"✓ Active GitHub profile ({int(github_activity)} contributions/month)")
        
        # Risks
        if response_rate < 0.30:
            risks.append(f"⚠ Low recruiter engagement ({int(response_rate * 100)}%)")
        
        if completion_rate < 0.40:
            risks.append(f"⚠ Low interview completion rate")
        
        if github_activity == 0:
            risks.append("⚠ No public GitHub activity")
        
        return {'strengths': strengths, 'risks': risks}
    
    def _analyze_availability(self, profile_text):
        """Analyze availability signals"""
        strengths = []
        risks = []
        
        # Open to work
        if 'Open to work: True' in profile_text:
            strengths.append("✓ Currently open to opportunities")
        else:
            risks.append("⚠ Not actively looking")
        
        # Notice period
        if 'Notice: 30 days' in profile_text:
            strengths.append("✓ Available within 30 days")
        elif 'Notice: 60 days' in profile_text:
            strengths.append("✓ Available within 60 days")
        elif 'Notice: 120 days' in profile_text or 'Notice: 150 days' in profile_text:
            risks.append("⚠ Long notice period (120+ days)")
        
        return {'strengths': strengths, 'risks': risks}
    
    def _generate_summary(self, strengths, risks, scores):
        """Generate one-line summary"""
        score = scores.get('final_score', 0.0)
        
        if score >= 0.8:
            return "Excellent match - Strong across all dimensions"
        elif score >= 0.6:
            return "Good match - Some areas of concern"
        elif score >= 0.4:
            return "Moderate match - Multiple gaps identified"
        else:
            return "Weak match - Significant gaps"
    
    def format_explanation(self, explanation, rank=None):
        """Format explanation for display"""
        output = []
        
        if rank:
            output.append(f"Rank #{rank}")
        else:
            output.append(f"Candidate: {explanation['candidate_id']}")
        
        output.append(f"Overall Score: {explanation['overall_score']:.3f}")
        output.append(f"Summary: {explanation['summary']}\n")
        
        if explanation['strengths']:
            output.append("Strengths:")
            for strength in explanation['strengths']:
                output.append(f"  {strength}")
            output.append("")
        
        if explanation['risks']:
            output.append("Risks:")
            for risk in explanation['risks']:
                output.append(f"  {risk}")
            output.append("")
        
        return '\n'.join(output)


if __name__ == "__main__":
    explainer = CandidateExplainer()
    
    # Test candidate
    candidate = {
        'candidate_id': 'CAND_0000031',
        'profile_text': """
        Recommendation Systems Engineer with 6.0 years of experience.
        Skills: Python, FAISS, Machine Learning, Information Retrieval, Embeddings
        Started as Engineer, promoted to Senior Engineer, now Lead Engineer.
        Open to work: True | Notice: 60 days
        GitHub activity: 32.6/100 | Recruiter response rate: 91% | Interview completion: 60%
        """
    }
    
    jd_requirements = {
        'skills': ['Python', 'FAISS', 'Machine Learning', 'Elasticsearch', 'PyTorch'],
        'experience': 5,
        'domain': 'Search',
        'leadership': False
    }
    
    scores = {
        'final_score': 0.847,
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
    
    # Generate explanation
    explanation = explainer.explain(candidate, jd_requirements, scores, behavioral_data)
    
    # Display
    print("=== CANDIDATE EXPLANATION ===\n")
    print(explainer.format_explanation(explanation, rank=1))
