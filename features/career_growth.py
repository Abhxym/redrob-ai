"""
Career Growth Score: Measure career trajectory and progression velocity
"""
import re

class CareerGrowthScorer:
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
        """Extract career levels from profile"""
        text_lower = text.lower()
        found_levels = []
        
        for level, score in self.levels.items():
            if re.search(r'\b' + level + r'\b', text_lower):
                found_levels.append(score)
        
        return sorted(found_levels) if found_levels else [2]
    
    def count_promotions(self, text):
        """Count explicit promotion mentions"""
        text_lower = text.lower()
        count = sum(1 for keyword in self.promotion_keywords if keyword in text_lower)
        return count
    
    def extract_years_experience(self, text):
        """Extract years of experience"""
        patterns = [
            r'(\d+\.?\d*)\s*years?\s+(?:of\s+)?experience',
            r'experience[:\s]+(\d+\.?\d*)\s*years?',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                return float(match.group(1))
        return 1.0
    
    def compute_score(self, profile_text):
        """
        Compute career growth score
        
        Measures:
        1. Promotion count (explicit mentions)
        2. Promotion velocity (promotions per year)
        3. Level progression (Junior → Senior → Lead)
        4. Leadership transition (reached leadership role)
        
        Returns:
            dict: Detailed career growth metrics
        """
        levels = self.extract_levels(profile_text)
        promotion_count = self.count_promotions(profile_text)
        years_exp = self.extract_years_experience(profile_text)
        
        # Promotion velocity
        promotion_velocity = promotion_count / max(years_exp, 1)
        
        # Level progression score
        if len(levels) >= 3:
            level_progression = 1.0  # Multiple levels = strong progression
        elif len(levels) == 2:
            level_progression = 0.6
        else:
            level_progression = 0.2
        
        # Leadership transition (reached lead/principal/director)
        highest_level = max(levels)
        leadership_transition = 1.0 if highest_level >= 5 else 0.0
        
        # Career trajectory score (growth rate)
        trajectory = min(1.0, (highest_level - min(levels)) / 4.0) if len(levels) > 1 else 0.0
        
        # Final growth score (weighted combination)
        growth_score = (
            0.25 * min(promotion_count / 3, 1.0) +  # Promotion count (capped at 3)
            0.25 * min(promotion_velocity / 0.5, 1.0) +  # Velocity (0.5 = excellent)
            0.25 * level_progression +  # Level progression
            0.15 * leadership_transition +  # Leadership achieved
            0.10 * trajectory  # Growth trajectory
        )
        
        return {
            'growth_score': growth_score,
            'promotion_count': promotion_count,
            'promotion_velocity': promotion_velocity,
            'level_progression': level_progression,
            'leadership_transition': leadership_transition,
            'highest_level': highest_level,
            'trajectory': trajectory
        }


if __name__ == "__main__":
    scorer = CareerGrowthScorer()
    
    print("=== Career Growth Scoring Examples ===\n")
    
    # High growth profile
    profile1 = """
    Started as Junior Engineer in 2018, promoted to Senior Engineer in 2020,
    elevated to Lead Engineer in 2023. 6 years of experience leading teams.
    """
    result1 = scorer.compute_score(profile1)
    print(f"High Growth Candidate:")
    print(f"  Promotions: {result1['promotion_count']}")
    print(f"  Velocity: {result1['promotion_velocity']:.2f}")
    print(f"  Leadership: {result1['leadership_transition']}")
    print(f"  Growth Score: {result1['growth_score']:.3f}\n")
    
    # Moderate growth profile
    profile2 = """
    Senior Software Engineer with 8 years of experience building systems.
    Strong technical background in backend development.
    """
    result2 = scorer.compute_score(profile2)
    print(f"Moderate Growth Candidate:")
    print(f"  Promotions: {result2['promotion_count']}")
    print(f"  Velocity: {result2['promotion_velocity']:.2f}")
    print(f"  Leadership: {result2['leadership_transition']}")
    print(f"  Growth Score: {result2['growth_score']:.3f}\n")
    
    # Low growth profile
    profile3 = """
    Engineer with 5 years of experience in software development.
    Working on various projects and systems.
    """
    result3 = scorer.compute_score(profile3)
    print(f"Low Growth Candidate:")
    print(f"  Promotions: {result3['promotion_count']}")
    print(f"  Velocity: {result3['promotion_velocity']:.2f}")
    print(f"  Leadership: {result3['leadership_transition']}")
    print(f"  Growth Score: {result3['growth_score']:.3f}\n")
