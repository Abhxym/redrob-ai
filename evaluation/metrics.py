"""
Evaluation Framework - Standard ranking metrics for candidate ranking systems
"""
import numpy as np
from typing import List, Dict


class RankingEvaluator:
    """
    Evaluation metrics for ranking systems:
    - Recall@K
    - MRR (Mean Reciprocal Rank)
    - NDCG (Normalized Discounted Cumulative Gain)
    - MAP (Mean Average Precision)
    """
    
    def __init__(self):
        pass
    
    def recall_at_k(self, relevant_items: List[str], recommended_items: List[str], k: int) -> float:
        """
        Recall@K: Fraction of relevant items in top-K recommendations
        
        Args:
            relevant_items: List of relevant candidate IDs
            recommended_items: List of recommended candidate IDs (ranked)
            k: Number of top items to consider
        
        Returns:
            float: Recall@K score [0, 1]
        """
        if not relevant_items:
            return 0.0
        
        top_k = recommended_items[:k]
        relevant_in_top_k = len(set(top_k) & set(relevant_items))
        
        return relevant_in_top_k / len(relevant_items)
    
    def mean_reciprocal_rank(self, relevant_items: List[str], recommended_items: List[str]) -> float:
        """
        MRR: Average of reciprocal ranks of first relevant item
        
        Args:
            relevant_items: List of relevant candidate IDs
            recommended_items: List of recommended candidate IDs (ranked)
        
        Returns:
            float: MRR score [0, 1]
        """
        for i, item in enumerate(recommended_items, 1):
            if item in relevant_items:
                return 1.0 / i
        
        return 0.0
    
    def ndcg_at_k(self, relevant_scores: Dict[str, float], recommended_items: List[str], k: int) -> float:
        """
        NDCG@K: Normalized Discounted Cumulative Gain
        
        Args:
            relevant_scores: Dict mapping candidate_id to relevance score
            recommended_items: List of recommended candidate IDs (ranked)
            k: Number of top items to consider
        
        Returns:
            float: NDCG@K score [0, 1]
        """
        top_k = recommended_items[:k]
        
        # DCG: Sum of (relevance / log2(rank + 1))
        dcg = 0.0
        for i, item in enumerate(top_k, 1):
            relevance = relevant_scores.get(item, 0.0)
            dcg += relevance / np.log2(i + 1)
        
        # IDCG: DCG of perfect ranking
        sorted_relevances = sorted(relevant_scores.values(), reverse=True)[:k]
        idcg = 0.0
        for i, relevance in enumerate(sorted_relevances, 1):
            idcg += relevance / np.log2(i + 1)
        
        if idcg == 0:
            return 0.0
        
        return dcg / idcg
    
    def average_precision(self, relevant_items: List[str], recommended_items: List[str]) -> float:
        """
        AP: Average Precision - Precision at each relevant item position
        
        Args:
            relevant_items: List of relevant candidate IDs
            recommended_items: List of recommended candidate IDs (ranked)
        
        Returns:
            float: AP score [0, 1]
        """
        if not relevant_items:
            return 0.0
        
        relevant_set = set(relevant_items)
        precisions = []
        num_relevant_seen = 0
        
        for i, item in enumerate(recommended_items, 1):
            if item in relevant_set:
                num_relevant_seen += 1
                precision_at_i = num_relevant_seen / i
                precisions.append(precision_at_i)
        
        if not precisions:
            return 0.0
        
        return np.mean(precisions)
    
    def mean_average_precision(self, queries: List[Dict]) -> float:
        """
        MAP: Mean Average Precision across multiple queries
        
        Args:
            queries: List of dicts with 'relevant_items' and 'recommended_items'
        
        Returns:
            float: MAP score [0, 1]
        """
        aps = []
        for query in queries:
            ap = self.average_precision(query['relevant_items'], query['recommended_items'])
            aps.append(ap)
        
        return np.mean(aps) if aps else 0.0
    
    def evaluate_ranking(self, relevant_items: List[str], recommended_items: List[str], 
                        relevance_scores: Dict[str, float] = None) -> Dict[str, float]:
        """
        Compute all ranking metrics
        
        Args:
            relevant_items: List of relevant candidate IDs
            recommended_items: List of recommended candidate IDs (ranked)
            relevance_scores: Optional dict of relevance scores for NDCG
        
        Returns:
            dict: All metrics
        """
        # If no relevance scores provided, use binary (1 for relevant, 0 for irrelevant)
        if relevance_scores is None:
            relevance_scores = {item: 1.0 for item in relevant_items}
        
        metrics = {
            'Recall@5': self.recall_at_k(relevant_items, recommended_items, 5),
            'Recall@10': self.recall_at_k(relevant_items, recommended_items, 10),
            'Recall@20': self.recall_at_k(relevant_items, recommended_items, 20),
            'MRR': self.mean_reciprocal_rank(relevant_items, recommended_items),
            'NDCG@5': self.ndcg_at_k(relevance_scores, recommended_items, 5),
            'NDCG@10': self.ndcg_at_k(relevance_scores, recommended_items, 10),
            'NDCG@20': self.ndcg_at_k(relevance_scores, recommended_items, 20),
            'MAP': self.average_precision(relevant_items, recommended_items)
        }
        
        return metrics


class SyntheticLabelGenerator:
    """
    Generate synthetic labels for evaluation when ground truth unavailable
    """
    
    def generate_relevance_labels(self, candidates: List[Dict], jd_requirements: Dict) -> Dict[str, float]:
        """
        Generate synthetic relevance scores based on heuristics
        
        Args:
            candidates: List of candidate dicts with features
            jd_requirements: Job requirements
        
        Returns:
            dict: candidate_id -> relevance_score [0, 1]
        """
        labels = {}
        
        for candidate in candidates:
            # Heuristic: Combine skill match and experience
            skill_score = candidate.get('skill_score', 0.5)
            exp_score = candidate.get('experience_score', 0.5)
            behavior_score = candidate.get('behavior_score', 0.5)
            
            # Weighted relevance
            relevance = (
                0.5 * skill_score +
                0.3 * exp_score +
                0.2 * behavior_score
            )
            
            labels[candidate['candidate_id']] = relevance
        
        return labels
    
    def generate_binary_labels(self, candidates: List[Dict], threshold: float = 0.6) -> List[str]:
        """
        Generate binary relevant/irrelevant labels
        
        Args:
            candidates: List of candidate dicts with scores
            threshold: Score threshold for relevance
        
        Returns:
            List of relevant candidate IDs
        """
        relevant = []
        
        for candidate in candidates:
            # Consider relevant if overall score above threshold
            score = candidate.get('final_score', 0.0)
            if score >= threshold:
                relevant.append(candidate['candidate_id'])
        
        return relevant


if __name__ == "__main__":
    evaluator = RankingEvaluator()
    
    print("=== Ranking Evaluation Framework ===\n")
    
    # Example: Test with mock data
    # Ground truth relevant candidates
    relevant_items = ['CAND_0000031', 'CAND_0000014', 'CAND_0000043', 'CAND_0000010', 'CAND_0000021']
    
    # System recommendations (ranked)
    recommended_items = [
        'CAND_0000031',  # Rank 1 - Relevant
        'CAND_0000043',  # Rank 2 - Relevant
        'CAND_0000025',  # Rank 3 - Not relevant
        'CAND_0000014',  # Rank 4 - Relevant
        'CAND_0000032',  # Rank 5 - Not relevant
        'CAND_0000010',  # Rank 6 - Relevant
        'CAND_0000027',  # Rank 7 - Not relevant
        'CAND_0000021',  # Rank 8 - Relevant
        'CAND_0000038',  # Rank 9 - Not relevant
        'CAND_0000015',  # Rank 10 - Not relevant
    ]
    
    # Relevance scores for NDCG
    relevance_scores = {
        'CAND_0000031': 1.0,  # Highly relevant
        'CAND_0000043': 0.9,
        'CAND_0000014': 0.8,
        'CAND_0000010': 0.7,
        'CAND_0000021': 0.7,
    }
    
    # Evaluate
    metrics = evaluator.evaluate_ranking(relevant_items, recommended_items, relevance_scores)
    
    print("Evaluation Metrics:")
    print("-" * 40)
    for metric, value in metrics.items():
        print(f"  {metric}: {value:.4f}")
    
    print("\n=== Interpretation ===")
    print(f"Recall@10: {metrics['Recall@10']:.2%} of relevant candidates found in top 10")
    print(f"MRR: First relevant candidate at position {1/metrics['MRR']:.0f}")
    print(f"NDCG@10: {metrics['NDCG@10']:.2%} ranking quality vs. ideal")
    print(f"MAP: {metrics['MAP']:.2%} average precision across all relevant items")
