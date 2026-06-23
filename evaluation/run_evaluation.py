"""
Evaluation Runner - Demonstrate evaluation methodology for ranking system
"""
import json
import sys
sys.path.append('..')

from evaluation.metrics import RankingEvaluator, SyntheticLabelGenerator


class EvaluationRunner:
    """
    Run complete evaluation suite on ranking system
    """
    
    def __init__(self):
        self.evaluator = RankingEvaluator()
        self.label_generator = SyntheticLabelGenerator()
    
    def load_test_cases(self):
        """
        Load or create test cases for evaluation
        In production, these would be labeled by domain experts
        """
        test_cases = [
            {
                'jd_name': 'Senior ML Engineer - Search & Ranking',
                'relevant_candidates': [
                    'CAND_0000031',  # Recommendation Systems Engineer
                    'CAND_0000043',  # Cloud Engineer with ML
                    'CAND_0000014',  # Frontend Engineer with FAISS
                    'CAND_0000010',  # Data Engineer with ML
                    'CAND_0000021',  # Project Manager with AI
                ],
                'relevance_scores': {
                    'CAND_0000031': 1.0,
                    'CAND_0000043': 0.85,
                    'CAND_0000014': 0.80,
                    'CAND_0000010': 0.75,
                    'CAND_0000021': 0.70,
                }
            },
            {
                'jd_name': 'Data Engineer - Pipelines & Infrastructure',
                'relevant_candidates': [
                    'CAND_0000001',  # Backend Engineer with Spark
                    'CAND_0000010',  # Data Engineer
                    'CAND_0000025',  # Frontend Engineer with data pipelines
                    'CAND_0000035',  # Full Stack with data experience
                ],
                'relevance_scores': {
                    'CAND_0000001': 0.95,
                    'CAND_0000010': 1.0,
                    'CAND_0000025': 0.75,
                    'CAND_0000035': 0.80,
                }
            }
        ]
        
        return test_cases
    
    def evaluate_system(self, system_rankings: dict, test_cases: list) -> dict:
        """
        Evaluate ranking system against test cases
        
        Args:
            system_rankings: Dict mapping jd_name to list of ranked candidate_ids
            test_cases: List of test case dicts with ground truth
        
        Returns:
            dict: Aggregated metrics
        """
        all_metrics = []
        
        for test_case in test_cases:
            jd_name = test_case['jd_name']
            relevant_items = test_case['relevant_candidates']
            relevance_scores = test_case['relevance_scores']
            
            # Get system's ranking for this JD
            recommended_items = system_rankings.get(jd_name, [])
            
            if not recommended_items:
                print(f"Warning: No recommendations for '{jd_name}'")
                continue
            
            # Evaluate
            metrics = self.evaluator.evaluate_ranking(
                relevant_items,
                recommended_items,
                relevance_scores
            )
            
            metrics['jd_name'] = jd_name
            all_metrics.append(metrics)
        
        # Aggregate metrics
        aggregated = self._aggregate_metrics(all_metrics)
        
        return {
            'individual': all_metrics,
            'aggregated': aggregated
        }
    
    def _aggregate_metrics(self, all_metrics: list) -> dict:
        """Compute average metrics across all test cases"""
        if not all_metrics:
            return {}
        
        metric_names = [k for k in all_metrics[0].keys() if k != 'jd_name']
        aggregated = {}
        
        for metric_name in metric_names:
            values = [m[metric_name] for m in all_metrics]
            aggregated[metric_name] = sum(values) / len(values)
        
        return aggregated
    
    def print_evaluation_report(self, results: dict):
        """Print detailed evaluation report"""
        print("\n" + "="*80)
        print("RANKING SYSTEM EVALUATION REPORT")
        print("="*80 + "\n")
        
        # Individual test cases
        print("Individual Test Case Results:")
        print("-" * 80)
        
        for metrics in results['individual']:
            jd_name = metrics['jd_name']
            print(f"\n{jd_name}")
            print("  " + "-" * 70)
            
            print(f"  Recall@10:  {metrics['Recall@10']:.4f}  ({metrics['Recall@10']*100:.1f}%)")
            print(f"  Recall@20:  {metrics['Recall@20']:.4f}  ({metrics['Recall@20']*100:.1f}%)")
            print(f"  MRR:        {metrics['MRR']:.4f}  (First relevant at rank {1/metrics['MRR']:.0f})")
            print(f"  NDCG@10:    {metrics['NDCG@10']:.4f}  ({metrics['NDCG@10']*100:.1f}%)")
            print(f"  NDCG@20:    {metrics['NDCG@20']:.4f}  ({metrics['NDCG@20']*100:.1f}%)")
            print(f"  MAP:        {metrics['MAP']:.4f}  ({metrics['MAP']*100:.1f}%)")
        
        # Aggregated metrics
        print("\n" + "="*80)
        print("AGGREGATED METRICS (Average Across All Test Cases)")
        print("="*80 + "\n")
        
        agg = results['aggregated']
        
        print(f"  Recall@5:   {agg['Recall@5']:.4f}  ({agg['Recall@5']*100:.1f}%)")
        print(f"  Recall@10:  {agg['Recall@10']:.4f}  ({agg['Recall@10']*100:.1f}%)")
        print(f"  Recall@20:  {agg['Recall@20']:.4f}  ({agg['Recall@20']*100:.1f}%)")
        print(f"  MRR:        {agg['MRR']:.4f}")
        print(f"  NDCG@5:     {agg['NDCG@5']:.4f}  ({agg['NDCG@5']*100:.1f}%)")
        print(f"  NDCG@10:    {agg['NDCG@10']:.4f}  ({agg['NDCG@10']*100:.1f}%)")
        print(f"  NDCG@20:    {agg['NDCG@20']:.4f}  ({agg['NDCG@20']*100:.1f}%)")
        print(f"  MAP:        {agg['MAP']:.4f}  ({agg['MAP']*100:.1f}%)")
        
        print("\n" + "="*80)
        print("INTERPRETATION")
        print("="*80 + "\n")
        
        self._print_interpretation(agg)
    
    def _print_interpretation(self, metrics: dict):
        """Print interpretation of metrics"""
        print("Key Insights:\n")
        
        # Recall
        recall10 = metrics['Recall@10']
        if recall10 >= 0.80:
            print(f"✓ Excellent Recall@10 ({recall10*100:.1f}%) - Finding most relevant candidates")
        elif recall10 >= 0.60:
            print(f"○ Good Recall@10 ({recall10*100:.1f}%) - Finding majority of relevant candidates")
        else:
            print(f"✗ Low Recall@10 ({recall10*100:.1f}%) - Missing many relevant candidates")
        
        # MRR
        mrr = metrics['MRR']
        avg_rank = 1 / mrr if mrr > 0 else float('inf')
        if avg_rank <= 3:
            print(f"✓ Excellent MRR ({mrr:.3f}) - First relevant candidate in top 3")
        elif avg_rank <= 5:
            print(f"○ Good MRR ({mrr:.3f}) - First relevant candidate in top 5")
        else:
            print(f"✗ Low MRR ({mrr:.3f}) - First relevant candidate at rank {avg_rank:.0f}")
        
        # NDCG
        ndcg10 = metrics['NDCG@10']
        if ndcg10 >= 0.80:
            print(f"✓ Excellent NDCG@10 ({ndcg10*100:.1f}%) - Near-optimal ranking")
        elif ndcg10 >= 0.60:
            print(f"○ Good NDCG@10 ({ndcg10*100:.1f}%) - Reasonable ranking quality")
        else:
            print(f"✗ Low NDCG@10 ({ndcg10*100:.1f}%) - Suboptimal ranking")
        
        # MAP
        map_score = metrics['MAP']
        if map_score >= 0.70:
            print(f"✓ Excellent MAP ({map_score*100:.1f}%) - High precision throughout")
        elif map_score >= 0.50:
            print(f"○ Good MAP ({map_score*100:.1f}%) - Decent precision")
        else:
            print(f"✗ Low MAP ({map_score*100:.1f}%) - Low precision")


if __name__ == "__main__":
    runner = EvaluationRunner()
    
    # Load test cases
    test_cases = runner.load_test_cases()
    
    # Mock system rankings (in real use, these come from main.py)
    system_rankings = {
        'Senior ML Engineer - Search & Ranking': [
            'CAND_0000031', 'CAND_0000043', 'CAND_0000014', 'CAND_0000010',
            'CAND_0000025', 'CAND_0000021', 'CAND_0000032', 'CAND_0000038',
            'CAND_0000015', 'CAND_0000027'
        ],
        'Data Engineer - Pipelines & Infrastructure': [
            'CAND_0000001', 'CAND_0000010', 'CAND_0000035', 'CAND_0000025',
            'CAND_0000032', 'CAND_0000014', 'CAND_0000043', 'CAND_0000027',
            'CAND_0000038', 'CAND_0000015'
        ]
    }
    
    # Run evaluation
    results = runner.evaluate_system(system_rankings, test_cases)
    
    # Print report
    runner.print_evaluation_report(results)
