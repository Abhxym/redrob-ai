"""
Experience Score: candidate_years / required_years (capped at 1.0)
"""
import re

class ExperienceScorer:
    def __init__(self):
        self.patterns = [
            r'(\d+)\+?\s*years?\s+(?:of\s+)?experience',
            r'experience[:\s]+(\d+)\+?\s*years?',
            r'(\d+)\+?\s*years?\s+in',
            r'worked\s+for\s+(\d+)\+?\s*years?',
            r'(\d+)\+?\s*yrs'
        ]
    
    def extract_years(self, text):
        """Extract years of experience from text"""
        text_lower = text.lower()
        for pattern in self.patterns:
            match = re.search(pattern, text_lower)
            if match:
                return int(match.group(1))
        return 0
    
    def compute_score(self, candidate_profile, required_years):
        """
        Score = candidate_years / required_years (capped at 1.0)
        
        Args:
            candidate_profile (str): Candidate's profile text
            required_years (int): Required years from JD
        
        Returns:
            float: Score in [0.0, 1.0]
        """
        if required_years == 0:
            return 1.0
        
        candidate_years = self.extract_years(candidate_profile)
        score = candidate_years / required_years
        
        return min(score, 1.0)


if __name__ == "__main__":
    scorer = ExperienceScorer()
    
    # Test cases
    profile1 = "Senior Engineer with 8 years of experience in ML systems"
    profile2 = "Engineer with 3 years in backend development"
    profile3 = "Junior developer with 1 year experience"
    
    required = 5
    
    score1 = scorer.compute_score(profile1, required)
    score2 = scorer.compute_score(profile2, required)
    score3 = scorer.compute_score(profile3, required)
    
    print(f"Profile 1 (8 years): {score1:.2f} (capped at 1.0)")
    print(f"Profile 2 (3 years): {score2:.2f} (3/5)")
    print(f"Profile 3 (1 year): {score3:.2f} (1/5)")
