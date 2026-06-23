"""
Availability Score: Deep behavioral intelligence on candidate availability
"""

class AvailabilityScorer:
    def __init__(self):
        # Weight configuration
        self.weights = {
            'open_to_work': 0.5,
            'recent_activity': 0.3,
            'notice_period': 0.2
        }
    
    def normalize_notice_period(self, notice_days):
        """
        Normalize notice period to [0, 1] score
        30 days = 1.0 (best)
        150 days = 0.0 (worst)
        """
        if notice_days <= 30:
            return 1.0
        elif notice_days >= 150:
            return 0.0
        else:
            return 1.0 - (notice_days - 30) / 120
    
    def compute_score(self, open_to_work=False, notice_period_days=90, last_active_days_ago=30):
        """
        Compute availability score
        
        Args:
            open_to_work: Boolean, actively looking
            notice_period_days: Days until can join
            last_active_days_ago: Days since last platform activity
        
        Returns:
            float: Availability score [0.0, 1.0]
        """
        # Open to work signal
        open_score = 1.0 if open_to_work else 0.0
        
        # Notice period score (lower is better)
        notice_score = self.normalize_notice_period(notice_period_days)
        
        # Recent activity score (more recent is better)
        # 0-7 days = 1.0, 30+ days = 0.0
        if last_active_days_ago <= 7:
            activity_score = 1.0
        elif last_active_days_ago >= 30:
            activity_score = 0.0
        else:
            activity_score = 1.0 - (last_active_days_ago - 7) / 23
        
        # Weighted combination
        final_score = (
            self.weights['open_to_work'] * open_score +
            self.weights['recent_activity'] * activity_score +
            self.weights['notice_period'] * notice_score
        )
        
        return final_score


if __name__ == "__main__":
    scorer = AvailabilityScorer()
    
    print("=== Availability Scoring Examples ===\n")
    
    # Scenario 1: Ideal candidate
    score1 = scorer.compute_score(
        open_to_work=True,
        notice_period_days=30,
        last_active_days_ago=2
    )
    print(f"Ideal Candidate:")
    print(f"  Open to work: True")
    print(f"  Notice: 30 days")
    print(f"  Last active: 2 days ago")
    print(f"  Score: {score1:.3f}\n")
    
    # Scenario 2: Available but long notice
    score2 = scorer.compute_score(
        open_to_work=True,
        notice_period_days=120,
        last_active_days_ago=5
    )
    print(f"Long Notice Candidate:")
    print(f"  Open to work: True")
    print(f"  Notice: 120 days")
    print(f"  Last active: 5 days ago")
    print(f"  Score: {score2:.3f}\n")
    
    # Scenario 3: Passive candidate
    score3 = scorer.compute_score(
        open_to_work=False,
        notice_period_days=90,
        last_active_days_ago=45
    )
    print(f"Passive Candidate:")
    print(f"  Open to work: False")
    print(f"  Notice: 90 days")
    print(f"  Last active: 45 days ago")
    print(f"  Score: {score3:.3f}\n")
