"""
Career Progression Score: Promotion history from Engineer → Senior → Lead
"""
import re

class CareerScorer:
    def __init__(self):
        self.levels = {
            'junior': 1,
            'engineer': 2,
            'senior': 3,
            'staff': 4,
            'lead': 5,
            'principal': 6,
            'director': 7,
            'vp': 8,
            'head': 7
        }
        self.promotion_keywords = [
            'promoted', 'promotion', 'advanced to', 'elevated to', 'grew to'
        ]
    
    def extract_levels(self, text):
        """Extract career levels mentioned in profile"""
        text_lower = text.lower()
        found_levels = []
        
        for level, score in self.levels.items():
            if re.search(r'\b' + level + r'\b', text_lower):
                found_levels.append(score)
        
        return sorted(found_levels) if found_levels else [2]  # Default: Engineer level
    
    def has_promotion_signal(self, text):
        """Check if promotion keywords exist"""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.promotion_keywords)
    
    def compute_score(self, candidate_profile):
        """
        Score based on:
        1. Career progression (multiple levels mentioned)
        2. Promotion keywords
        3. Highest level reached
        
        Returns:
            float: Score in [0.0, 1.0]
        """
        levels = self.extract_levels(candidate_profile)
        has_promotion = self.has_promotion_signal(candidate_profile)
        
        # Base score from highest level (max 8 = VP)
        highest_level = max(levels)
        level_score = highest_level / 8.0
        
        # Bonus for progression (multiple levels)
        progression_bonus = 0.0
        if len(levels) >= 2:
            progression_bonus = 0.15
        if len(levels) >= 3:
            progression_bonus = 0.25
        
        # Bonus for promotion keywords
        promotion_bonus = 0.15 if has_promotion else 0.0
        
        total_score = level_score + progression_bonus + promotion_bonus
        return min(total_score, 1.0)


if __name__ == "__main__":
    scorer = CareerScorer()
    
    # Test cases
    profile1 = "Started as Junior Engineer, promoted to Senior Engineer, now Lead Engineer at Amazon"
    profile2 = "Senior ML Engineer with strong technical skills"
    profile3 = "Engineer working on backend systems"
    
    score1 = scorer.compute_score(profile1)
    score2 = scorer.compute_score(profile2)
    score3 = scorer.compute_score(profile3)
    
    print(f"Profile 1 (Junior→Senior→Lead): {score1:.2f}")
    print(f"Profile 2 (Senior): {score2:.2f}")
    print(f"Profile 3 (Engineer): {score3:.2f}")
