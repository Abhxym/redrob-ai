"""
XGBoost Ranker - Learn optimal feature weights instead of manual tuning
"""
import pandas as pd
import numpy as np


class XGBoostRanker:
    def __init__(self):
        self.model = None
        self.feature_names = [
            'semantic_score',
            'bm25_score',
            'skill_score',
            'experience_score',
            'career_score',
            'behavior_score',
            'availability_score',
            'career_growth_score',
            'leadership_score',
            'promotion_velocity'
        ]
    
    def create_synthetic_labels(self, candidates):
        """
        Create synthetic training labels based on heuristics
        Used when no ground truth labels available
        
        Heuristic: Combine multiple signals to create pseudo-labels
        """
        labels = []
        
        for candidate in candidates:
            # Strong signals get high labels
            label = (
                0.3 * candidate.get('skill_score', 0.5) +
                0.2 * candidate.get('experience_score', 0.5) +
                0.2 * candidate.get('behavior_score', 0.5) +
                0.15 * candidate.get('availability_score', 0.5) +
                0.15 * candidate.get('career_growth_score', 0.5)
            )
            
            # Add noise to avoid overfitting to heuristic
            label += np.random.normal(0, 0.05)
            labels.append(max(0, min(1, label)))
        
        return np.array(labels)
    
    def train(self, candidates, labels=None):
        """
        Train XGBoost ranker
        
        Args:
            candidates: List of candidate dicts with features
            labels: Ground truth labels (optional, will create synthetic if None)
        """
        try:
            import xgboost as xgb
        except ImportError:
            print("XGBoost not installed. Using fallback weighted scoring.")
            return False
        
        # Extract features
        X = []
        for candidate in candidates:
            features = [candidate.get(feat, 0.5) for feat in self.feature_names]
            X.append(features)
        
        X = np.array(X)
        
        # Create or use labels
        if labels is None:
            y = self.create_synthetic_labels(candidates)
        else:
            y = np.array(labels)
        
        # Train XGBoost model
        self.model = xgb.XGBRanker(
            objective='rank:pairwise',
            learning_rate=0.1,
            n_estimators=100,
            max_depth=4,
            tree_method='hist'
        )
        
        # Create group sizes (all candidates in one query group)
        group = [len(candidates)]
        
        self.model.fit(X, y, group=group, verbose=False)
        
        return True
    
    def predict(self, candidates):
        """
        Predict scores using trained XGBoost model
        
        Args:
            candidates: List of candidate dicts with features
        
        Returns:
            np.array: Predicted scores
        """
        if self.model is None:
            # Fallback to weighted scoring
            return self.fallback_scoring(candidates)
        
        try:
            import xgboost as xgb
            
            X = []
            for candidate in candidates:
                features = [candidate.get(feat, 0.5) for feat in self.feature_names]
                X.append(features)
            
            X = np.array(X)
            scores = self.model.predict(X)
            
            return scores
        except:
            return self.fallback_scoring(candidates)
    
    def fallback_scoring(self, candidates):
        """Fallback weighted scoring if XGBoost unavailable"""
        scores = []
        for candidate in candidates:
            score = (
                0.35 * candidate.get('semantic_score', 0.5) +
                0.20 * candidate.get('skill_score', 0.5) +
                0.15 * candidate.get('experience_score', 0.5) +
                0.10 * candidate.get('behavior_score', 0.5) +
                0.10 * candidate.get('availability_score', 0.5) +
                0.10 * candidate.get('career_growth_score', 0.5)
            )
            scores.append(score)
        
        return np.array(scores)
    
    def get_feature_importance(self):
        """Get feature importance from trained model"""
        if self.model is None:
            return None
        
        try:
            importance = self.model.feature_importances_
            return dict(zip(self.feature_names, importance))
        except:
            return None


if __name__ == "__main__":
    # Test with mock candidates
    ranker = XGBoostRanker()
    
    candidates = [
        {
            'candidate_id': 'C001',
            'semantic_score': 0.8,
            'bm25_score': 0.7,
            'skill_score': 0.9,
            'experience_score': 1.0,
            'career_score': 0.8,
            'behavior_score': 0.85,
            'availability_score': 0.9,
            'career_growth_score': 0.75,
            'leadership_score': 0.7,
            'promotion_velocity': 0.3
        },
        {
            'candidate_id': 'C002',
            'semantic_score': 0.6,
            'bm25_score': 0.5,
            'skill_score': 0.4,
            'experience_score': 0.6,
            'career_score': 0.5,
            'behavior_score': 0.6,
            'availability_score': 0.4,
            'career_growth_score': 0.3,
            'leadership_score': 0.4,
            'promotion_velocity': 0.1
        },
        {
            'candidate_id': 'C003',
            'semantic_score': 0.7,
            'bm25_score': 0.8,
            'skill_score': 0.7,
            'experience_score': 0.8,
            'career_score': 0.9,
            'behavior_score': 0.75,
            'availability_score': 0.7,
            'career_growth_score': 0.85,
            'leadership_score': 0.9,
            'promotion_velocity': 0.4
        }
    ]
    
    print("=== XGBoost Ranker Test ===\n")
    
    # Train
    print("Training XGBoost ranker...")
    success = ranker.train(candidates)
    
    if success:
        print("✓ Model trained successfully\n")
        
        # Get feature importance
        importance = ranker.get_feature_importance()
        if importance:
            print("Feature Importance:")
            sorted_features = sorted(importance.items(), key=lambda x: x[1], reverse=True)
            for feat, imp in sorted_features:
                print(f"  {feat}: {imp:.3f}")
    else:
        print("✓ Using fallback weighted scoring\n")
    
    # Predict
    print("\nPredictions:")
    scores = ranker.predict(candidates)
    
    for i, (candidate, score) in enumerate(zip(candidates, scores), 1):
        print(f"  {candidate['candidate_id']}: {score:.3f}")
