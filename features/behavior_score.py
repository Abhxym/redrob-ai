"""
Behavioral Signals Score: Hidden advantage from engagement metrics
"""

class BehaviorScorer:
    def __init__(self):
        # Normalization thresholds
        self.github_max = 100  # commits per month
        self.response_rate_max = 1.0  # 100%
        self.interview_completion_max = 1.0  # 100%
        self.saved_max = 50  # times saved by recruiters
    
    def normalize(self, value, max_val):
        """Normalize value to [0, 1]"""
        return min(value / max_val, 1.0) if max_val > 0 else 0.0
    
    def compute_score(self, github_activity=0, recruiter_response_rate=0.0, 
                     interview_completion_rate=0.0, saved_by_recruiters_30d=0):
        """
        Behavioral score from engagement signals:
        - github_activity_score: Commits/contributions per month
        - recruiter_response_rate: 0.0 to 1.0
        - interview_completion_rate: 0.0 to 1.0
        - saved_by_recruiters_30d: Times bookmarked by recruiters
        
        Returns:
            float: Weighted score in [0.0, 1.0]
        """
        github_score = self.normalize(github_activity, self.github_max)
        response_score = self.normalize(recruiter_response_rate, self.response_rate_max)
        completion_score = self.normalize(interview_completion_rate, self.interview_completion_max)
        saved_score = self.normalize(saved_by_recruiters_30d, self.saved_max)
        
        # Weighted average (response rate and completion rate are most important)
        weights = {
            'github': 0.15,
            'response': 0.35,
            'completion': 0.35,
            'saved': 0.15
        }
        
        total_score = (
            github_score * weights['github'] +
            response_score * weights['response'] +
            completion_score * weights['completion'] +
            saved_score * weights['saved']
        )
        
        return total_score


if __name__ == "__main__":
    scorer = BehaviorScorer()
    
    # Test cases
    print("Highly engaged candidate:")
    score1 = scorer.compute_score(
        github_activity=80,
        recruiter_response_rate=0.90,
        interview_completion_rate=0.95,
        saved_by_recruiters_30d=25
    )
    print(f"  Score: {score1:.2f}")
    
    print("\nModerately engaged candidate:")
    score2 = scorer.compute_score(
        github_activity=20,
        recruiter_response_rate=0.60,
        interview_completion_rate=0.70,
        saved_by_recruiters_30d=10
    )
    print(f"  Score: {score2:.2f}")
    
    print("\nLow engagement candidate:")
    score3 = scorer.compute_score(
        github_activity=5,
        recruiter_response_rate=0.20,
        interview_completion_rate=0.30,
        saved_by_recruiters_30d=2
    )
    print(f"  Score: {score3:.2f}")
