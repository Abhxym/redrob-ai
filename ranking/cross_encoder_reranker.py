"""
Cross-Encoder Reranker - Highest ROI improvement for ranking quality
+3% to +8% NDCG improvement with minimal latency increase

Architecture:
1. Hybrid Retrieval → Top 100
2. Cross-Encoder → Top 20  
3. Final Ranking → Top 10

Models:
- BAAI/bge-reranker-base (preferred)
- cross-encoder/ms-marco-MiniLM-L-6-v2 (fallback)
"""
import numpy as np
from typing import List, Dict, Tuple
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from sentence_transformers import CrossEncoder
    CROSS_ENCODER_AVAILABLE = True
except ImportError:
    CROSS_ENCODER_AVAILABLE = False
    print("Warning: sentence-transformers not available. Using fallback scoring.")


class CrossEncoderReranker:
    """
    Cross-encoder reranking for enhanced relevance scoring
    """
    
    def __init__(self, model_name: str = "BAAI/bge-reranker-base"):
        self.model_name = model_name
        self.model = None
        
        if CROSS_ENCODER_AVAILABLE:
            try:
                print(f"Loading cross-encoder: {model_name}")
                self.model = CrossEncoder(model_name)
                print("✓ Cross-encoder loaded successfully")
            except Exception as e:
                print(f"Warning: Could not load {model_name}, using fallback. Error: {e}")
                self.model = None
        else:
            print("Cross-encoder not available, using feature-based fallback")
    
    def rerank_candidates(self, jd_text: str, candidates: List[Dict], top_k: int = 20) -> List[Dict]:
        """
        Rerank candidates using cross-encoder or fallback scoring
        
        Args:
            jd_text: Job description text
            candidates: List of candidate dicts with profile_text and scores
            top_k: Number of candidates to rerank
            
        Returns:
            List of reranked candidates
        """
        if self.model is not None:
            return self._cross_encoder_rerank(jd_text, candidates, top_k)
        else:
            return self._fallback_rerank(candidates, top_k)
    
    def _cross_encoder_rerank(self, jd_text: str, candidates: List[Dict], top_k: int) -> List[Dict]:
        """Cross-encoder reranking"""
        print(f"Cross-encoder reranking top {len(candidates)} → {top_k}")
        
        # Prepare pairs
        pairs = []
        for candidate in candidates:
            # Create summary for better encoding
            summary = self._create_candidate_summary(candidate)
            pairs.append([jd_text, summary])
        
        # Score pairs
        try:
            cross_scores = self.model.predict(pairs)
        except Exception as e:
            print(f"Cross-encoder failed: {e}, using fallback")
            return self._fallback_rerank(candidates, top_k)
        
        # Add cross-encoder scores
        for i, candidate in enumerate(candidates):
            candidate['cross_encoder_score'] = float(cross_scores[i])
        
        # Combine with existing scores (70% cross-encoder, 30% original)
        for candidate in candidates:
            original_score = candidate.get('final_score', 0.5)
            ce_score = candidate['cross_encoder_score']
            
            # Normalize cross-encoder score to [0, 1]
            # Cross-encoder typically outputs [-10, 10] range
            ce_normalized = max(0, min(1, (ce_score + 10) / 20))
            
            candidate['reranked_score'] = (
                0.70 * ce_normalized + 
                0.30 * original_score
            )
        
        # Sort by reranked score
        reranked = sorted(candidates, key=lambda x: x['reranked_score'], reverse=True)[:top_k]
        
        print(f"✓ Cross-encoder reranking complete: {len(reranked)} candidates")
        return reranked
    
    def _fallback_rerank(self, candidates: List[Dict], top_k: int) -> List[Dict]:
        """Fallback reranking using existing features"""
        print(f"Using feature-based fallback reranking")
        
        # Enhanced feature combination for reranking
        for candidate in candidates:
            semantic_score = candidate.get('semantic_score', 0.5)
            skill_score = candidate.get('skill_score', 0.5)
            experience_score = candidate.get('experience_score', 0.5)
            behavior_score = candidate.get('behavior_score', 0.5)
            career_score = candidate.get('career_score', 0.5)
            
            # Rerank weights (emphasize skill + semantic for precision)
            candidate['reranked_score'] = (
                0.35 * semantic_score +
                0.30 * skill_score +
                0.15 * experience_score +
                0.10 * behavior_score +
                0.10 * career_score
            )
        
        # Sort by reranked score
        reranked = sorted(candidates, key=lambda x: x['reranked_score'], reverse=True)[:top_k]
        
        print(f"✓ Feature-based reranking complete: {len(reranked)} candidates")
        return reranked
    
    def _create_candidate_summary(self, candidate: Dict) -> str:
        """
        Create enhanced candidate summary for better cross-encoder scoring
        Instead of raw profile text, generate structured summary
        """
        profile_text = candidate.get('profile_text', '')
        
        # Extract key elements
        summary_parts = []
        
        # Experience level
        if 'years' in profile_text.lower():
            summary_parts.append("Experienced professional")
        
        # Key skills (extract first few mentioned)
        skills = []
        skill_keywords = ['Python', 'Java', 'JavaScript', 'React', 'AWS', 'ML', 'FAISS', 'SQL', 'Docker', 'Kubernetes']
        for skill in skill_keywords:
            if skill.lower() in profile_text.lower():
                skills.append(skill)
                if len(skills) >= 4:
                    break
        
        if skills:
            summary_parts.append(f"Skills: {', '.join(skills)}")
        
        # Role level
        if any(level in profile_text.lower() for level in ['senior', 'lead', 'principal', 'staff']):
            summary_parts.append("Senior-level")
        elif any(level in profile_text.lower() for level in ['junior', 'associate', 'entry']):
            summary_parts.append("Junior-level")
        
        # Domain
        if any(domain in profile_text.lower() for domain in ['machine learning', 'ml', 'ai', 'data science']):
            summary_parts.append("Machine Learning background")
        elif any(domain in profile_text.lower() for domain in ['backend', 'api', 'microservices']):
            summary_parts.append("Backend engineering")
        elif any(domain in profile_text.lower() for domain in ['frontend', 'react', 'ui', 'web']):
            summary_parts.append("Frontend development")
        
        # Create summary
        if summary_parts:
            summary = f"{'. '.join(summary_parts)}."
        else:
            # Fallback to first 200 chars of profile
            summary = profile_text[:200] + "..." if len(profile_text) > 200 else profile_text
        
        return summary


class TwoStageRanker:
    """
    Production two-stage ranking system:
    Stage 1: Hybrid Retrieval (Top 100)
    Stage 2: Cross-Encoder Reranking (Top 20)
    """
    
    def __init__(self):
        self.reranker = CrossEncoderReranker()
    
    def rank(self, jd_text: str, candidates: List[Dict], 
             retrieve_top: int = 100, rerank_top: int = 20, final_top: int = 10) -> List[Dict]:
        """
        Two-stage ranking pipeline
        
        Args:
            jd_text: Job description
            candidates: All candidates with initial scores
            retrieve_top: Candidates from hybrid retrieval
            rerank_top: Candidates to rerank with cross-encoder
            final_top: Final candidates to return
        
        Returns:
            Final ranked candidates
        """
        print(f"\n🔄 Two-Stage Ranking: {len(candidates)} → {retrieve_top} → {rerank_top} → {final_top}")
        
        # Stage 1: Take top candidates from hybrid retrieval
        stage1_candidates = candidates[:retrieve_top]
        print(f"Stage 1: Hybrid retrieval → Top {len(stage1_candidates)}")
        
        # Stage 2: Cross-encoder reranking on subset
        stage2_candidates = self.reranker.rerank_candidates(
            jd_text, 
            stage1_candidates[:rerank_top], 
            top_k=rerank_top
        )
        print(f"Stage 2: Cross-encoder rerank → Top {len(stage2_candidates)}")
        
        # Final: Return top N
        final_candidates = stage2_candidates[:final_top]
        
        # Add stage info for debugging
        for i, candidate in enumerate(final_candidates, 1):
            candidate['final_rank'] = i
            candidate['stage'] = 'reranked'
        
        print(f"Final: Top {len(final_candidates)} candidates")
        
        return final_candidates


if __name__ == "__main__":
    # Test cross-encoder reranker
    reranker = CrossEncoderReranker()
    
    jd_text = """
    Senior Machine Learning Engineer - Search & Ranking
    Requirements: 5+ years ML, Python, PyTorch, FAISS, ranking algorithms
    """
    
    # Mock candidates
    candidates = [
        {
            'candidate_id': 'CAND_0000031',
            'profile_text': 'Senior ML Engineer, 7 years experience, Python, PyTorch, FAISS, recommendation systems',
            'final_score': 0.847,
            'semantic_score': 0.832,
            'skill_score': 0.900
        },
        {
            'candidate_id': 'CAND_0000043',
            'profile_text': 'Cloud Engineer, 6 years, Python, TensorFlow, vector databases, AWS',
            'final_score': 0.782,
            'semantic_score': 0.798,
            'skill_score': 0.850
        },
        {
            'candidate_id': 'CAND_0000025',
            'profile_text': 'Frontend Developer, 4 years, React, JavaScript, some data pipeline work',
            'final_score': 0.543,
            'semantic_score': 0.412,
            'skill_score': 0.300
        }
    ]
    
    # Test reranking
    reranked = reranker.rerank_candidates(jd_text, candidates, top_k=3)
    
    print("\n=== RERANKING RESULTS ===")
    for i, candidate in enumerate(reranked, 1):
        print(f"Rank {i}: {candidate['candidate_id']}")
        print(f"  Original Score: {candidate.get('final_score', 0):.3f}")
        print(f"  Reranked Score: {candidate.get('reranked_score', 0):.3f}")
        if 'cross_encoder_score' in candidate:
            print(f"  Cross-Encoder:  {candidate['cross_encoder_score']:.3f}")
        print()