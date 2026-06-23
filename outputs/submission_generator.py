"""
Submission Generator - Generate validated submission.csv
"""
import csv
import os
from typing import List, Dict


class SubmissionGenerator:
    """
    Generate submission CSV in required format
    """
    
    def __init__(self, output_dir='outputs'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def generate(self, ranked_candidates: List[Dict], jd_id: str = 'JD001', 
                filename: str = 'submission.csv') -> str:
        """
        Generate submission CSV from ranked candidates
        
        Args:
            ranked_candidates: List of ranked candidate dicts with scores
            jd_id: Job description identifier
            filename: Output filename
        
        Returns:
            str: Path to generated CSV
        """
        output_path = os.path.join(self.output_dir, filename)
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow(['jd_id', 'candidate_id', 'rank', 'score'])
            
            # Rows
            for rank, candidate in enumerate(ranked_candidates, 1):
                writer.writerow([
                    jd_id,
                    candidate['candidate_id'],
                    rank,
                    f"{candidate['final_score']:.6f}"
                ])
        
        print(f"✓ Submission generated: {output_path}")
        return output_path
    
    def generate_detailed(self, ranked_candidates: List[Dict], jd_id: str = 'JD001',
                         filename: str = 'submission_detailed.csv') -> str:
        """
        Generate detailed submission with all scores and reasoning
        
        Args:
            ranked_candidates: List of ranked candidate dicts
            jd_id: Job description identifier
            filename: Output filename
        
        Returns:
            str: Path to generated CSV
        """
        output_path = os.path.join(self.output_dir, filename)
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = [
                'jd_id', 'candidate_id', 'rank', 'final_score',
                'semantic_score', 'skill_score', 'experience_score',
                'behavior_score', 'career_score', 'availability_score',
                'reasoning'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            writer.writeheader()
            
            for rank, candidate in enumerate(ranked_candidates, 1):
                row = {
                    'jd_id': jd_id,
                    'candidate_id': candidate['candidate_id'],
                    'rank': rank,
                    'final_score': f"{candidate.get('final_score', 0):.6f}",
                    'semantic_score': f"{candidate.get('semantic_score', 0):.4f}",
                    'skill_score': f"{candidate.get('skill_score', 0):.4f}",
                    'experience_score': f"{candidate.get('experience_score', 0):.4f}",
                    'behavior_score': f"{candidate.get('behavior_score', 0):.4f}",
                    'career_score': f"{candidate.get('career_score', 0):.4f}",
                    'availability_score': f"{candidate.get('availability_score', 0):.4f}",
                    'reasoning': candidate.get('reasoning', '')
                }
                writer.writerow(row)
        
        print(f"✓ Detailed submission generated: {output_path}")
        return output_path
    
    def validate_submission(self, filepath: str) -> Dict[str, any]:
        """
        Validate submission CSV format
        
        Args:
            filepath: Path to submission CSV
        
        Returns:
            dict: Validation results
        """
        validation = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'stats': {}
        }
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                # Check headers
                required_headers = ['jd_id', 'candidate_id', 'rank', 'score']
                if not all(h in reader.fieldnames for h in required_headers):
                    validation['valid'] = False
                    validation['errors'].append(f"Missing required headers. Expected: {required_headers}")
                    return validation
                
                rows = list(reader)
                validation['stats']['total_rows'] = len(rows)
                
                # Validate each row
                seen_candidates = set()
                prev_score = float('inf')
                
                for i, row in enumerate(rows, 1):
                    # Check rank sequence
                    rank = int(row['rank'])
                    if rank != i:
                        validation['warnings'].append(f"Rank mismatch at row {i}: expected {i}, got {rank}")
                    
                    # Check candidate uniqueness
                    candidate_id = row['candidate_id']
                    if candidate_id in seen_candidates:
                        validation['errors'].append(f"Duplicate candidate: {candidate_id}")
                        validation['valid'] = False
                    seen_candidates.add(candidate_id)
                    
                    # Check score format and descending order
                    try:
                        score = float(row['score'])
                        if score > prev_score:
                            validation['warnings'].append(f"Scores not in descending order at rank {rank}")
                        prev_score = score
                    except ValueError:
                        validation['errors'].append(f"Invalid score format at rank {rank}: {row['score']}")
                        validation['valid'] = False
                
                validation['stats']['unique_candidates'] = len(seen_candidates)
                validation['stats']['score_range'] = f"[{min(float(r['score']) for r in rows):.4f}, {max(float(r['score']) for r in rows):.4f}]"
        
        except FileNotFoundError:
            validation['valid'] = False
            validation['errors'].append(f"File not found: {filepath}")
        except Exception as e:
            validation['valid'] = False
            validation['errors'].append(f"Validation error: {str(e)}")
        
        return validation
    
    def print_validation_report(self, validation: Dict):
        """Print validation report"""
        print("\n" + "="*60)
        print("SUBMISSION VALIDATION REPORT")
        print("="*60 + "\n")
        
        if validation['valid']:
            print("✓ Validation PASSED")
        else:
            print("✗ Validation FAILED")
        
        print(f"\nStatistics:")
        for key, value in validation.get('stats', {}).items():
            print(f"  {key}: {value}")
        
        if validation['errors']:
            print(f"\nErrors ({len(validation['errors'])}):")
            for error in validation['errors']:
                print(f"  ✗ {error}")
        
        if validation['warnings']:
            print(f"\nWarnings ({len(validation['warnings'])}):")
            for warning in validation['warnings']:
                print(f"  ⚠ {warning}")
        
        print()


if __name__ == "__main__":
    # Test submission generation
    generator = SubmissionGenerator()
    
    # Mock ranked candidates
    ranked_candidates = [
        {
            'candidate_id': 'CAND_0000031',
            'final_score': 0.847,
            'semantic_score': 0.028,
            'skill_score': 0.80,
            'experience_score': 1.0,
            'behavior_score': 0.78,
            'career_score': 0.85,
            'availability_score': 0.75,
            'reasoning': 'Strong match on Python, FAISS, ML | 6 years experience'
        },
        {
            'candidate_id': 'CAND_0000043',
            'final_score': 0.782,
            'semantic_score': 0.025,
            'skill_score': 0.75,
            'experience_score': 0.9,
            'behavior_score': 0.65,
            'career_score': 0.80,
            'availability_score': 0.60,
            'reasoning': 'Relevant ML skills | 8 years experience'
        },
        {
            'candidate_id': 'CAND_0000014',
            'final_score': 0.756,
            'semantic_score': 0.022,
            'skill_score': 0.70,
            'experience_score': 0.85,
            'behavior_score': 0.70,
            'career_score': 0.75,
            'availability_score': 0.80,
            'reasoning': 'Has FAISS experience | Senior-level'
        }
    ]
    
    # Generate standard submission
    filepath = generator.generate(ranked_candidates, jd_id='JD001')
    
    # Generate detailed submission
    detailed_filepath = generator.generate_detailed(ranked_candidates, jd_id='JD001')
    
    # Validate
    validation = generator.validate_submission(filepath)
    generator.print_validation_report(validation)
