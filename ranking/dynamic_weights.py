"""
Dynamic Weight Adjustment - Role-specific ranking weights

Instead of fixed weights for all roles, adjust based on JD requirements.

Examples:
- Senior ML Lead: Emphasize leadership + experience
- Junior Analyst: Emphasize skills + learning potential
- Staff Engineer: Emphasize technical depth + impact
"""
from typing import Dict


class DynamicWeightAdjuster:
    """
    Automatically adjust ranking weights based on JD characteristics
    """
    
    def __init__(self):
        # Default weights
        self.default_weights = {
            'semantic': 0.35,
            'skill': 0.25,
            'experience': 0.15,
            'behavior': 0.10,
            'career': 0.10,
            'availability': 0.05
        }
    
    def get_weights(self, jd_requirements: Dict) -> Dict[str, float]:
        """
        Get dynamic weights based on JD requirements
        
        Args:
            jd_requirements: Dict with skills, experience, domain, leadership
        
        Returns:
            Dict with adjusted weights
        """
        required_exp = jd_requirements.get('experience', 0)
        leadership = jd_requirements.get('leadership', False)
        domain = jd_requirements.get('domain', 'Unknown')
        skills_count = len(jd_requirements.get('skills', []))
        
        # Start with defaults
        weights = self.default_weights.copy()
        
        # Rule 1: Senior leadership roles
        if leadership and required_exp >= 8:
            weights = {
                'semantic': 0.20,
                'skill': 0.20,
                'experience': 0.25,
                'behavior': 0.10,
                'career': 0.20,      # High career progression
                'availability': 0.05
            }
        
        # Rule 2: Junior roles (0-3 years)
        elif required_exp <= 3:
            weights = {
                'semantic': 0.35,
                'skill': 0.35,       # Skills most important
                'experience': 0.05,  # Less weight on experience
                'behavior': 0.15,    # High potential signals
                'career': 0.05,
                'availability': 0.05
            }
        
        # Rule 3: Mid-level roles (4-7 years)
        elif 4 <= required_exp <= 7:
            weights = {
                'semantic': 0.30,
                'skill': 0.30,       # Balanced skills
                'experience': 0.15,
                'behavior': 0.10,
                'career': 0.10,
                'availability': 0.05
            }
        
        # Rule 4: Specialized technical roles (ML, Data, Search)
        if domain in ['Machine Learning', 'Data', 'Search', 'Recommendation']:
            # Increase skill weight
            weights['skill'] += 0.05
            weights['semantic'] -= 0.05
        
        # Rule 5: Many required skills (>8)
        if skills_count > 8:
            # Increase skill match importance
            weights['skill'] += 0.05
            weights['behavior'] -= 0.05
        
        # Normalize to sum to 1.0
        total = sum(weights.values())
        weights = {k: v/total for k, v in weights.items()}
        
        return weights
    
    def explain_weights(self, jd_requirements: Dict, weights: Dict[str, float]) -> str:
        """
        Explain why these weights were chosen
        """
        required_exp = jd_requirements.get('experience', 0)
        leadership = jd_requirements.get('leadership', False)
        domain = jd_requirements.get('domain', 'Unknown')
        
        explanation = []
        
        if leadership and required_exp >= 8:
            explanation.append("Senior leadership role: Emphasizing career progression and experience")
        elif required_exp <= 3:
            explanation.append("Junior role: Emphasizing skills and learning potential over experience")
        elif 4 <= required_exp <= 7:
            explanation.append("Mid-level role: Balanced weighting across all factors")
        
        if domain in ['Machine Learning', 'Data', 'Search', 'Recommendation']:
            explanation.append(f"Specialized {domain} role: Higher weight on technical skills")
        
        if len(jd_requirements.get('skills', [])) > 8:
            explanation.append("Multiple required skills: Prioritizing skill match coverage")
        
        if not explanation:
            explanation.append("Standard role: Using balanced default weights")
        
        return " | ".join(explanation)


if __name__ == "__main__":
    adjuster = DynamicWeightAdjuster()
    
    print("=== Dynamic Weight Adjustment Examples ===\n")
    
    # Test case 1: Senior ML Lead
    jd1 = {
        'skills': ['Python', 'ML', 'Leadership', 'System Design'],
        'experience': 10,
        'domain': 'Machine Learning',
        'leadership': True
    }
    
    weights1 = adjuster.get_weights(jd1)
    explanation1 = adjuster.explain_weights(jd1, weights1)
    
    print("Test 1: Senior ML Lead (10 years, leadership)")
    print(f"Explanation: {explanation1}")
    print("Weights:")
    for key, value in sorted(weights1.items(), key=lambda x: x[1], reverse=True):
        print(f"  {key:<15} {value:.3f} ({value*100:.1f}%)")
    print()
    
    # Test case 2: Junior Analyst
    jd2 = {
        'skills': ['Python', 'SQL', 'Excel'],
        'experience': 2,
        'domain': 'Data',
        'leadership': False
    }
    
    weights2 = adjuster.get_weights(jd2)
    explanation2 = adjuster.explain_weights(jd2, weights2)
    
    print("Test 2: Junior Data Analyst (2 years)")
    print(f"Explanation: {explanation2}")
    print("Weights:")
    for key, value in sorted(weights2.items(), key=lambda x: x[1], reverse=True):
        print(f"  {key:<15} {value:.3f} ({value*100:.1f}%)")
    print()
    
    # Test case 3: Mid-level Software Engineer
    jd3 = {
        'skills': ['Java', 'Spring Boot', 'AWS', 'Docker', 'Kubernetes'],
        'experience': 5,
        'domain': 'Backend',
        'leadership': False
    }
    
    weights3 = adjuster.get_weights(jd3)
    explanation3 = adjuster.explain_weights(jd3, weights3)
    
    print("Test 3: Mid-level Software Engineer (5 years)")
    print(f"Explanation: {explanation3}")
    print("Weights:")
    for key, value in sorted(weights3.items(), key=lambda x: x[1], reverse=True):
        print(f"  {key:<15} {value:.3f} ({value*100:.1f}%)")
