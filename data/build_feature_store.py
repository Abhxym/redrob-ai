"""
Candidate Feature Store - Precompute and store all candidate features
"""
import json
import pandas as pd
from datetime import datetime
import sys
sys.path.append('..')

from features.skill_score import SkillScorer
from features.experience_score import ExperienceScorer
from features.career_score import CareerScorer
from features.behavior_score import BehaviorScorer


class FeatureStoreBuilder:
    def __init__(self):
        self.skill_scorer = SkillScorer()
        self.exp_scorer = ExperienceScorer()
        self.career_scorer = CareerScorer()
        self.behavior_scorer = BehaviorScorer()
    
    def extract_behavioral_metrics(self, profile_text):
        """Extract behavioral signals from profile"""
        # GitHub activity
        github = 0
        if 'GitHub activity:' in profile_text and 'not linked' not in profile_text:
            try:
                github_str = profile_text.split('GitHub activity:')[1].split('/')[0].strip()
                github = float(github_str)
            except:
                github = 0
        
        # Recruiter response rate
        response_rate = 0.5
        if 'Recruiter response rate:' in profile_text:
            try:
                rate_str = profile_text.split('Recruiter response rate:')[1].split('%')[0].strip()
                response_rate = float(rate_str) / 100
            except:
                response_rate = 0.5
        
        # Interview completion rate
        completion_rate = 0.5
        if 'Interview completion:' in profile_text:
            try:
                comp_str = profile_text.split('Interview completion:')[1].split('%')[0].strip()
                completion_rate = float(comp_str) / 100
            except:
                completion_rate = 0.5
        
        # Offer acceptance
        offer_acceptance = 0.5
        if 'Offer acceptance:' in profile_text:
            try:
                offer_str = profile_text.split('Offer acceptance:')[1].strip().split()[0]
                if offer_str != 'no':
                    offer_acceptance = float(offer_str.replace('%', '')) / 100
            except:
                offer_acceptance = 0.5
        
        return {
            'github_activity': github,
            'recruiter_response_rate': response_rate,
            'interview_completion_rate': completion_rate,
            'offer_acceptance_rate': offer_acceptance
        }
    
    def extract_availability_metrics(self, profile_text):
        """Extract availability signals"""
        # Open to work
        open_to_work = 1.0 if 'Open to work: True' in profile_text else 0.0
        
        # Notice period (lower is better)
        notice_period = 90  # default
        if 'Notice: 30 days' in profile_text:
            notice_period = 30
        elif 'Notice: 60 days' in profile_text:
            notice_period = 60
        elif 'Notice: 90 days' in profile_text:
            notice_period = 90
        elif 'Notice: 120 days' in profile_text:
            notice_period = 120
        elif 'Notice: 150 days' in profile_text:
            notice_period = 150
        
        # Normalize notice period (30 days = 1.0, 150 days = 0.0)
        notice_score = max(0.0, 1.0 - (notice_period - 30) / 120)
        
        # Recent activity (proxy: open to work is recent activity)
        recent_activity = open_to_work
        
        return {
            'open_to_work': open_to_work,
            'notice_period_days': notice_period,
            'notice_period_score': notice_score,
            'recent_activity': recent_activity
        }
    
    def extract_career_growth_metrics(self, profile_text):
        """Extract career growth signals"""
        profile_lower = profile_text.lower()
        
        # Count promotions
        promotion_keywords = ['promoted', 'promotion', 'advanced to', 'elevated to', 'grew to']
        promotion_count = sum(1 for keyword in promotion_keywords if keyword in profile_lower)
        
        # Extract career history length
        career_lines = [line for line in profile_text.split('\n') if 'Career History:' in line]
        job_count = profile_text.count('at ') if 'Career History:' in profile_text else 1
        
        # Extract years of experience
        years_exp = self.exp_scorer.extract_years(profile_text)
        
        # Promotion velocity (promotions per year)
        promotion_velocity = promotion_count / max(years_exp, 1)
        
        # Leadership transition
        has_leadership = any(level in profile_lower for level in ['lead', 'principal', 'director', 'head', 'vp'])
        leadership_transition = 1.0 if has_leadership and promotion_count > 0 else 0.0
        
        return {
            'promotion_count': promotion_count,
            'promotion_velocity': promotion_velocity,
            'job_count': job_count,
            'leadership_transition': leadership_transition
        }
    
    def build_feature_store(self, candidates_file='data/candidate_profiles.json', 
                           output_file='data/candidate_features.parquet'):
        """Build and save feature store"""
        print("Building Candidate Feature Store...")
        
        # Load candidates
        with open(candidates_file, 'r', encoding='utf-8') as f:
            candidates = json.load(f)
        
        features_list = []
        
        for candidate in candidates:
            candidate_id = candidate['candidate_id']
            profile_text = candidate['profile_text']
            
            # Extract base features
            years_experience = self.exp_scorer.extract_years(profile_text)
            
            # Behavioral metrics
            behavioral = self.extract_behavioral_metrics(profile_text)
            behavior_score = self.behavior_scorer.compute_score(
                github_activity=behavioral['github_activity'],
                recruiter_response_rate=behavioral['recruiter_response_rate'],
                interview_completion_rate=behavioral['interview_completion_rate'],
                saved_by_recruiters_30d=int(behavioral['github_activity'] / 2)
            )
            
            # Availability metrics
            availability = self.extract_availability_metrics(profile_text)
            availability_score = (
                0.5 * availability['open_to_work'] +
                0.3 * availability['recent_activity'] +
                0.2 * availability['notice_period_score']
            )
            
            # Career growth metrics
            career_growth = self.extract_career_growth_metrics(profile_text)
            career_score = self.career_scorer.compute_score(profile_text)
            
            # Leadership score (from career scorer)
            levels = self.career_scorer.extract_levels(profile_text)
            leadership_score = max(levels) / 8.0 if levels else 0.25
            
            # Combine all features
            feature_row = {
                'candidate_id': candidate_id,
                'years_experience': years_experience,
                'leadership_score': leadership_score,
                'behavior_score': behavior_score,
                'github_score': behavioral['github_activity'],
                'response_rate': behavioral['recruiter_response_rate'],
                'interview_completion_rate': behavioral['interview_completion_rate'],
                'offer_acceptance_rate': behavioral['offer_acceptance_rate'],
                'career_growth_score': career_score,
                'availability_score': availability_score,
                'open_to_work': availability['open_to_work'],
                'notice_period_days': availability['notice_period_days'],
                'notice_period_score': availability['notice_period_score'],
                'promotion_count': career_growth['promotion_count'],
                'promotion_velocity': career_growth['promotion_velocity'],
                'job_count': career_growth['job_count'],
                'leadership_transition': career_growth['leadership_transition']
            }
            
            features_list.append(feature_row)
        
        # Create DataFrame
        df = pd.DataFrame(features_list)
        
        # Save to Parquet
        df.to_parquet(output_file, index=False)
        
        print(f"✓ Feature store created: {output_file}")
        print(f"  Candidates: {len(df)}")
        print(f"  Features: {len(df.columns)}")
        print(f"\nFeature columns:")
        for col in df.columns:
            print(f"  - {col}")
        
        return df


if __name__ == "__main__":
    builder = FeatureStoreBuilder()
    df = builder.build_feature_store()
    
    print("\n=== Sample Features ===")
    print(df.head(3).to_string())
    
    print("\n=== Feature Statistics ===")
    print(df.describe().to_string())
