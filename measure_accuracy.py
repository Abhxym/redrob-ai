"""
Accuracy Measurement System for RedRob AI Recruiter

Measures ranking quality using:
1. Synthetic labels (when no ground truth)
2. Manual labels (expert annotations)
3. Cross-validation across multiple JDs
"""
import json
import numpy as np
from typing import List, Dict, Tuple
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from evaluation.metrics import RankingEvaluator
from demo import RedRobRecruiter


class AccuracyMeasurement:
    """
    Comprehensive accuracy measurement for candidate ranking
    """
    
    def __init__(self):
        self.evaluator = RankingEvaluator()
        self.recruiter = RedRobRecruiter()
    
    def create_ground_truth_labels(self) -> Dict[str, Dict]:
        """
        Create ground truth labels for evaluation
        
        In production: Domain experts would label
        For demo: Use heuristic-based labels
        """
        ground_truth = {
            'ML_Engineer_Search': {
                'jd_text': """
                Senior Machine Learning Engineer - Search & Ranking
                Requirements: 5+ years ML, Python, PyTorch, FAISS, Elasticsearch, 
                ranking algorithms, recommendation systems
                """,
                'highly_relevant': [
                    'CAND_0000031',  # Recommendation Systems Engineer, FAISS, ML
                    'CAND_0000043',  # Cloud Engineer with ML/FAISS
                ],
                'relevant': [
                    'CAND_0000014',  # Frontend with FAISS
                    'CAND_0000010',  # Data Engineer with ML
                    'CAND_0000021',  # Project Manager with AI/ML
                    'CAND_0000032',  # .NET with ML background
                ],
                'somewhat_relevant': [
                    'CAND_0000025',  # Frontend with data pipelines
                    'CAND_0000027',  # DevOps with ML
                    'CAND_0000015',  # Software Engineer with ML learning
                ],
                'not_relevant': [
                    'CAND_0000002',  # Operations Manager
                    'CAND_0000003',  # Customer Support
                    'CAND_0000005',  # Accountant
                ]
            },
            'Data_Engineer': {
                'jd_text': """
                Data Engineer - Pipelines & Infrastructure
                Requirements: 3+ years data engineering, Python, Spark, Airflow,
                SQL, ETL pipelines, data warehousing
                """,
                'highly_relevant': [
                    'CAND_0000001',  # Backend Engineer, Spark, Airflow
                    'CAND_0000010',  # Data Engineer, Spark, ML
                ],
                'relevant': [
                    'CAND_0000035',  # Full Stack with data pipelines
                    'CAND_0000025',  # Frontend with Spark, data pipelines
                    'CAND_0000033',  # Has Airflow, ETL
                ],
                'somewhat_relevant': [
                    'CAND_0000044',  # Frontend with Databricks
                    'CAND_0000026',  # Has ETL, Airflow
                ],
                'not_relevant': [
                    'CAND_0000022',  # Mechanical Engineer
                    'CAND_0000024',  # HR Manager
                ]
            },
            'Software_Engineer_Cloud': {
                'jd_text': """
                Software Engineer - Cloud & DevOps
                Requirements: 4+ years software engineering, AWS/Azure/GCP,
                Docker, Kubernetes, CI/CD, Python or Java
                """,
                'highly_relevant': [
                    'CAND_0000027',  # DevOps with AWS, Docker, Terraform
                    'CAND_0000015',  # Software Engineer, cloud
                    'CAND_0000023',  # Software Engineer, cloud & DevOps
                ],
                'relevant': [
                    'CAND_0000043',  # Cloud Engineer
                    'CAND_0000038',  # Java Developer with cloud
                    'CAND_0000011',  # QA with AWS
                ],
                'somewhat_relevant': [
                    'CAND_0000032',  # .NET Developer
                    'CAND_0000035',  # Full Stack
                ],
                'not_relevant': [
                    'CAND_0000028',  # Operations Manager
                    'CAND_0000030',  # Marketing Manager
                ]
            }
        }
        
        return ground_truth
    
    def convert_to_relevance_scores(self, ground_truth_item: Dict) -> Dict[str, float]:
        """
        Convert categorical labels to relevance scores
        
        highly_relevant: 1.0
        relevant: 0.75
        somewhat_relevant: 0.5
        not_relevant: 0.0
        """
        relevance_scores = {}
        
        for cand in ground_truth_item.get('highly_relevant', []):
            relevance_scores[cand] = 1.0
        
        for cand in ground_truth_item.get('relevant', []):
            relevance_scores[cand] = 0.75
        
        for cand in ground_truth_item.get('somewhat_relevant', []):
            relevance_scores[cand] = 0.5
        
        for cand in ground_truth_item.get('not_relevant', []):
            relevance_scores[cand] = 0.0
        
        return relevance_scores
    
    def measure_accuracy(self) -> Dict:
        """
        Measure system accuracy across multiple test JDs
        """
        print("\n" + "="*80)
        print("ACCURACY MEASUREMENT - REDROB AI RECRUITER")
        print("="*80 + "\n")
        
        ground_truth = self.create_ground_truth_labels()
        all_results = []
        
        for jd_name, gt_data in ground_truth.items():
            print(f"Testing: {jd_name}")
            print("-" * 80)
            
            # Run system
            results = self.recruiter.run(
                gt_data['jd_text'],
                jd_id=jd_name,
                top_k=100,
                verbose=False
            )
            
            # Get system ranking
            system_ranking = [c['candidate_id'] for c in results['ranked_candidates']]
            
            # Get ground truth relevant items
            relevant_items = (
                gt_data.get('highly_relevant', []) +
                gt_data.get('relevant', [])
            )
            
            # Get relevance scores
            relevance_scores = self.convert_to_relevance_scores(gt_data)
            
            # Evaluate
            metrics = self.evaluator.evaluate_ranking(
                relevant_items,
                system_ranking,
                relevance_scores
            )
            
            metrics['jd_name'] = jd_name
            metrics['relevant_count'] = len(relevant_items)
            all_results.append(metrics)
            
            # Print individual results
            print(f"  Recall@10:  {metrics['Recall@10']:.3f} ({metrics['Recall@10']*100:.1f}%)")
            print(f"  NDCG@10:    {metrics['NDCG@10']:.3f} ({metrics['NDCG@10']*100:.1f}%)")
            print(f"  MRR:        {metrics['MRR']:.3f}")
            print(f"  MAP:        {metrics['MAP']:.3f}\n")
        
        # Aggregate metrics
        aggregated = self._aggregate_metrics(all_results)
        
        print("="*80)
        print("OVERALL ACCURACY METRICS")
        print("="*80 + "\n")
        
        self._print_accuracy_report(aggregated, all_results)
        
        return {
            'individual': all_results,
            'aggregated': aggregated
        }
    
    def _aggregate_metrics(self, all_results: List[Dict]) -> Dict:
        """Compute average metrics"""
        if not all_results:
            return {}
        
        metric_names = [k for k in all_results[0].keys() 
                       if k not in ['jd_name', 'relevant_count']]
        
        aggregated = {}
        for metric_name in metric_names:
            values = [m[metric_name] for m in all_results]
            aggregated[metric_name] = np.mean(values)
        
        return aggregated
    
    def _print_accuracy_report(self, aggregated: Dict, individual: List[Dict]):
        """Print detailed accuracy report"""
        
        # Overall metrics
        print("Average Performance Across All Test Cases:\n")
        print(f"  Recall@5:   {aggregated['Recall@5']:.3f}  ({aggregated['Recall@5']*100:.1f}%)")
        print(f"  Recall@10:  {aggregated['Recall@10']:.3f}  ({aggregated['Recall@10']*100:.1f}%)")
        print(f"  Recall@20:  {aggregated['Recall@20']:.3f}  ({aggregated['Recall@20']*100:.1f}%)")
        print(f"  MRR:        {aggregated['MRR']:.3f}")
        print(f"  NDCG@10:    {aggregated['NDCG@10']:.3f}  ({aggregated['NDCG@10']*100:.1f}%)")
        print(f"  MAP:        {aggregated['MAP']:.3f}  ({aggregated['MAP']*100:.1f}%)")
        
        # Overall accuracy grade
        print("\n" + "="*80)
        print("OVERALL SYSTEM ACCURACY")
        print("="*80 + "\n")
        
        # Primary metric: NDCG@10 (industry standard for ranking)
        ndcg10 = aggregated['NDCG@10']
        recall10 = aggregated['Recall@10']
        mrr = aggregated['MRR']
        
        # Calculate weighted accuracy score
        accuracy_score = (
            0.40 * ndcg10 +      # Ranking quality
            0.30 * recall10 +    # Coverage
            0.30 * mrr           # Top result quality
        )
        
        print(f"Primary Metric (NDCG@10):  {ndcg10:.1%}")
        print(f"Coverage (Recall@10):      {recall10:.1%}")
        print(f"Top Result (MRR):          {mrr:.3f}\n")
        print(f"Overall Accuracy Score:    {accuracy_score:.1%}")
        
        # Grade
        if accuracy_score >= 0.85:
            grade = "A (Excellent)"
            comment = "Production-ready ranking quality"
        elif accuracy_score >= 0.75:
            grade = "B (Good)"
            comment = "Strong performance, minor improvements possible"
        elif accuracy_score >= 0.65:
            grade = "C (Fair)"
            comment = "Acceptable but needs optimization"
        else:
            grade = "D (Needs Improvement)"
            comment = "Significant ranking quality issues"
        
        print(f"Grade:                     {grade}")
        print(f"Assessment:                {comment}\n")
        
        # Breakdown by metric
        print("="*80)
        print("METRIC BREAKDOWN")
        print("="*80 + "\n")
        
        self._print_metric_analysis("Recall@10", recall10)
        self._print_metric_analysis("NDCG@10", ndcg10)
        self._print_metric_analysis("MRR", mrr)
        
        print()
    
    def _print_metric_analysis(self, metric_name: str, value: float):
        """Print analysis for individual metric"""
        
        thresholds = {
            'Recall@10': [(0.80, 'Excellent'), (0.60, 'Good'), (0.40, 'Fair')],
            'NDCG@10': [(0.85, 'Excellent'), (0.70, 'Good'), (0.55, 'Fair')],
            'MRR': [(0.80, 'Excellent'), (0.60, 'Good'), (0.40, 'Fair')]
        }
        
        rating = 'Needs Improvement'
        for threshold, label in thresholds.get(metric_name, []):
            if value >= threshold:
                rating = label
                break
        
        symbol = "✓" if rating in ['Excellent', 'Good'] else "○" if rating == 'Fair' else "✗"
        
        print(f"{symbol} {metric_name}: {value:.3f} - {rating}")
        
        # Interpretation
        if metric_name == 'Recall@10':
            print(f"   → Finding {value*100:.0f}% of relevant candidates in top 10")
        elif metric_name == 'NDCG@10':
            print(f"   → Ranking quality is {value*100:.0f}% of ideal ordering")
        elif metric_name == 'MRR':
            avg_rank = 1 / value if value > 0 else float('inf')
            print(f"   → First relevant candidate typically at rank {avg_rank:.1f}")
        
        print()
    
    def compare_to_baselines(self) -> Dict:
        """
        Compare system to baseline methods
        
        NOTE: These are ESTIMATED improvements based on architecture.
        Actual performance requires ground truth labels.
        
        Baselines:
        1. BM25 only (keyword search)
        2. FAISS only (semantic search)
        3. Random ranking
        4. Our hybrid system
        """
        print("\n" + "="*80)
        print("BASELINE COMPARISON (ESTIMATED)")
        print("="*80 + "\n")
        
        print("NOTE: These are expected improvements based on system architecture.")
        print("Actual metrics require human-labeled relevance judgments.\n")
        
        # Expected baseline performance (based on typical results in literature)
        baselines = {
            'Random': {
                'Expected_Recall@10': 0.15,
                'Expected_NDCG@10': 0.25,
                'Expected_MRR': 0.20,
                'Description': 'Random candidate selection'
            },
            'BM25 Only': {
                'Expected_Recall@10': 0.62,
                'Expected_NDCG@10': 0.68,
                'Expected_MRR': 0.55,
                'Description': 'Keyword matching only'
            },
            'FAISS Only': {
                'Expected_Recall@10': 0.58,
                'Expected_NDCG@10': 0.65,
                'Expected_MRR': 0.52,
                'Description': 'Semantic search only'
            },
            'RedRob AI (Ours)': {
                'Expected_Recall@10': '15-20% improvement over single-method',
                'Expected_NDCG@10': '15-20% improvement over single-method',
                'Expected_MRR': '15-20% improvement over single-method',
                'Description': 'Hybrid retrieval + multi-signal ranking'
            }
        }
        
        print(f"{'Method':<25} {'Description':<50}")
        print("-" * 80)
        
        for method, metrics in baselines.items():
            print(f"{method:<25} {metrics['Description']:<50}")
        
        print("\n" + "="*80)
        print("ARCHITECTURAL ADVANTAGES")
        print("="*80 + "\n")
        
        print("Our System (RedRob AI):")
        print("  ✓ Hybrid Retrieval: Combines BM25 (keywords) + FAISS (semantics)")
        print("  ✓ RRF Fusion: Balances different ranking signals")
        print("  ✓ Multi-Signal Scoring: 7 feature dimensions")
        print("  ✓ Behavioral Intelligence: Response rates, activity")
        print("  ✓ Career Growth Analysis: Promotion velocity")
        print("  ✓ Availability Scoring: Open to work, notice period")
        print("\nExpected Improvement: 15-20% over single-method baselines")
        print("(Based on typical hybrid retrieval performance in literature)\n")
        
        return baselines


def main():
    """Run accuracy measurement"""
    measurement = AccuracyMeasurement()
    
    # Measure accuracy
    results = measurement.measure_accuracy()
    
    # Compare to baselines
    measurement.compare_to_baselines()
    
    print("\n" + "="*80)
    print("ACCURACY MEASUREMENT COMPLETE")
    print("="*80 + "\n")
    
    return results


if __name__ == "__main__":
    main()
