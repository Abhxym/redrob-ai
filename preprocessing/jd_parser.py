"""
preprocessing/jd_parser.py

JD (Job Description) Understanding Engine.

No LLM - Pure regex and keyword extraction.

Extracts:
- Skills: Python, SQL, AWS, FAISS, etc.
- Experience: Years of experience required
- Domain: Backend, Frontend, ML, DevOps, Data, etc.
- Leadership: Whether leadership experience required
"""

import re
from typing import Dict, List, Any
from collections import defaultdict


class JDParser:
    """Parse and extract structured information from job descriptions"""
    
    # Technical Skills Database
    TECH_SKILLS = {
        # Languages
        'Python': ['python', 'py'],
        'JavaScript': ['javascript', 'js', 'node.js', 'nodejs'],
        'TypeScript': ['typescript', 'ts'],
        'Java': [r'java(?![script])'],
        'C++': [r'c\+\+', 'cpp'],
        'C#': ['c#', 'csharp'],
        'Go': [r'go(?:lang)?'],
        'Rust': ['rust'],
        'Ruby': ['ruby'],
        'PHP': ['php'],
        'SQL': [r'sql', r'postgres', r'postgresql', r'mysql', r'sqlite'],
        'R': [r'\br\b'],
        
        # Databases
        'PostgreSQL': ['postgres(?:ql)?', 'pg'],
        'MongoDB': ['mongodb', 'mongo'],
        'Redis': ['redis'],
        'Elasticsearch': ['elasticsearch', 'elastic'],
        'Dynamodb': ['dynamodb', 'dynamo'],
        'Cassandra': ['cassandra'],
        'DynamoDB': ['dynamodb'],
        'Snowflake': ['snowflake'],
        'BigQuery': ['bigquery', 'big query'],
        
        # Cloud Platforms
        'AWS': ['aws', 'amazon web services'],
        'GCP': ['gcp', 'google cloud'],
        'Azure': ['azure', 'microsoft azure'],
        'Kubernetes': ['kubernetes', 'k8s'],
        'Docker': ['docker'],
        
        # ML/AI
        'Machine Learning': ['machine learning', 'ml', 'ml models'],
        'Deep Learning': ['deep learning', 'neural networks', 'cnn', 'rnn', 'lstm'],
        'NLP': ['nlp', 'natural language processing'],
        'Computer Vision': ['computer vision', 'cv', 'image processing'],
        'TensorFlow': ['tensorflow'],
        'PyTorch': ['pytorch'],
        'Scikit-learn': ['scikit-learn', 'sklearn'],
        'FAISS': ['faiss'],
        'Vector Search': ['vector search', 'vector database'],
        'RAG': ['rag', 'retrieval augmented generation'],
        'LLM': ['llm', 'large language model'],
        'Embeddings': ['embeddings', 'vector embeddings'],
        
        # Data Engineering
        'Spark': ['spark', 'pyspark', 'apache spark'],
        'Hadoop': ['hadoop'],
        'Airflow': ['airflow', 'apache airflow'],
        'ETL': ['etl', 'extract transform load'],
        'Data Pipeline': ['data pipeline', 'pipelines'],
        'dbt': ['dbt', 'data build tool'],
        'Kafka': ['kafka'],
        'Scala': ['scala'],
        
        # DevOps/Infrastructure
        'CI/CD': [r'ci/cd', r'ci cd', r'continuous integration'],
        'Terraform': ['terraform'],
        'GitLab': ['gitlab'],
        'GitHub': ['github'],
        'Jenkins': ['jenkins'],
        'ArgoCD': ['argocd', 'argo cd'],
        'Linux': ['linux', 'unix'],
        'Bash': ['bash', 'shell scripting'],
        
        # Frontend
        'React': ['react', 'reactjs'],
        'Vue': ['vue(?:js)?', 'vuejs'],
        'Angular': ['angular', 'angularjs'],
        'HTML': ['html'],
        'CSS': ['css'],
        'REST API': ['rest api', 'rest apis'],
        'GraphQL': ['graphql'],
        
        # Backend
        'Django': ['django'],
        'Flask': ['flask'],
        'FastAPI': ['fastapi', 'fast api'],
        'Spring': ['spring', 'spring boot'],
        'Node.js': ['node.js', 'nodejs'],
        'Microservices': ['microservices'],
        
        # Search & Retrieval
        'BM25': ['bm25'],
        'Elasticsearch': ['elasticsearch'],
        'Solr': ['solr'],
        'Pinecone': ['pinecone'],
        'Weaviate': ['weaviate'],
        
        # Metrics
        'NDCG': [r'ndcg', r'normalized discounted cumulative gain'],
        'Precision': [r'precision@k', r'precision@'],
        'Recall': [r'recall@k', r'recall@'],
        'F1 Score': [r'f1 score', r'f1-score'],
        'AUC': [r'auc', r'area under curve'],
        'MAP': [r'map', r'mean average precision'],
    }
    
    # Domain Keywords
    DOMAIN_KEYWORDS = {
        'Backend': ['backend', 'api', 'server', 'microservice', 'distributed', 'scalability'],
        'Frontend': ['frontend', 'ui', 'ux', 'react', 'angular', 'vue', 'web'],
        'Full-Stack': ['full-stack', 'fullstack', 'full stack'],
        'Data': ['data engineer', 'data science', 'analytics', 'data pipeline', 'etl'],
        'ML': ['machine learning', 'ml engineer', 'ai', 'artificial intelligence', 'deep learning'],
        'DevOps': ['devops', 'dev ops', 'infrastructure', 'kubernetes', 'docker', 'deployment'],
        'QA': ['qa engineer', 'quality assurance', 'testing', 'automation testing'],
        'Search': ['search', 'ranking', 'retrieval', 'ir', 'information retrieval'],
        'Recommendation': ['recommendation', 'personalization', 'ranking'],
    }
    
    # Leadership Keywords
    LEADERSHIP_KEYWORDS = [
        'lead', 'manager', 'senior', 'principal', 'staff',
        'mentor', 'mentoring', 'team lead', 'lead engineer',
        'architect', 'director', 'head of', 'vp',
        'leadership experience', 'manage team', 'manage people'
    ]
    
    # Experience Patterns
    EXPERIENCE_PATTERNS = [
        r'(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s*)?(?:professional\s*)?(?:software\s*)?experience',
        r'experience\s*(?:of\s*)?(\d+)\+?\s*(?:years?|yrs?)',
        r'(\d+)\+?\s*(?:years?|yrs?)\s*(?:in|with|of)\s*(?:industry|professional|software)',
        r'minimum\s*(\d+)\s*(?:years?|yrs?)',
        r'(?:require|need)\s*(\d+)\+?\s*(?:years?|yrs?)',
    ]
    
    def __init__(self):
        """Initialize the JD Parser"""
        self.tech_skills_compiled = self._compile_patterns(self.TECH_SKILLS)
        self.domain_compiled = self._compile_patterns(self.DOMAIN_KEYWORDS)
        self.leadership_compiled = self._compile_leadership_patterns()
    
    def _compile_patterns(self, keyword_dict: Dict[str, List[str]]) -> Dict[str, Any]:
        """Compile regex patterns for efficient matching"""
        compiled = {}
        for key, patterns in keyword_dict.items():
            combined_pattern = '|'.join(f'(?:{p})' for p in patterns)
            compiled[key] = re.compile(combined_pattern, re.IGNORECASE)
        return compiled
    
    def _compile_leadership_patterns(self) -> Any:
        """Compile leadership pattern"""
        combined = '|'.join(f'(?:{p})' for p in self.LEADERSHIP_KEYWORDS)
        return re.compile(combined, re.IGNORECASE)
    
    def extract_skills(self, text: str) -> List[str]:
        """Extract technical skills from text"""
        skills = []
        for skill, pattern in self.tech_skills_compiled.items():
            if pattern.search(text):
                skills.append(skill)
        return sorted(list(set(skills)))  # Remove duplicates and sort
    
    def extract_experience(self, text: str) -> int:
        """Extract years of experience required"""
        for pattern_str in self.EXPERIENCE_PATTERNS:
            pattern = re.compile(pattern_str, re.IGNORECASE)
            match = pattern.search(text)
            if match:
                try:
                    years = int(match.group(1))
                    return years
                except (ValueError, IndexError):
                    continue
        
        # Default to 0 if not found
        return 0
    
    def extract_domain(self, text: str) -> str:
        """Extract primary domain"""
        domain_scores = defaultdict(int)
        
        for domain, pattern in self.domain_compiled.items():
            matches = pattern.findall(text.lower())
            domain_scores[domain] = len(matches)
        
        # Return domain with highest score
        if domain_scores:
            primary_domain = max(domain_scores, key=domain_scores.get)
            return primary_domain
        
        return 'Unknown'
    
    def extract_leadership(self, text: str) -> bool:
        """Check if leadership experience is required"""
        return bool(self.leadership_compiled.search(text))
    
    def parse(self, jd_text: str) -> Dict[str, Any]:
        """
        Parse job description and extract structured information.
        
        Args:
            jd_text: Raw job description text
            
        Returns:
            Dictionary with extracted information:
            {
                'skills': ['Python', 'SQL', 'AWS', ...],
                'experience': 5,
                'domain': 'Backend',
                'leadership': False
            }
        """
        return {
            'skills': self.extract_skills(jd_text),
            'experience': self.extract_experience(jd_text),
            'domain': self.extract_domain(jd_text),
            'leadership': self.extract_leadership(jd_text),
            'text_length': len(jd_text),
            'skill_count': len(self.extract_skills(jd_text))
        }


def main():
    """Demo JD Parser"""
    
    # Test Job Descriptions
    test_jds = [
        {
            'title': 'Backend Engineer - Search Systems',
            'jd': """
            We're hiring a Backend Engineer to build search and ranking systems.
            
            Requirements:
            - 5+ years of software engineering experience
            - Strong Python and SQL skills
            - Experience with distributed systems and microservices
            - Familiarity with FAISS or vector search
            - Experience with Kubernetes and Docker
            - Background in information retrieval or ranking systems is a plus
            
            Nice to Have:
            - Experience with machine learning pipelines
            - AWS or GCP experience
            - Leadership or mentoring experience
            """
        },
        {
            'title': 'ML Engineer - Recommendations',
            'jd': """
            Lead ML Engineer for recommendation systems.
            
            You should have:
            - 3+ years as ML engineer
            - Strong Python, PyTorch, TensorFlow
            - Experience with deep learning
            - SQL and data pipeline knowledge
            - Team leadership and mentoring skills
            
            We use:
            - Spark for data processing
            - Kubernetes for deployment
            - BigQuery for analytics
            - RAG and LLM applications
            """
        },
        {
            'title': 'Frontend React Developer',
            'jd': """
            Frontend Developer needed.
            
            Skills:
            - React and TypeScript (5 years)
            - HTML, CSS
            - REST APIs and GraphQL
            - Senior level with leadership experience
            - Mentoring junior developers
            """
        },
        {
            'title': 'Data Engineer',
            'jd': """
            Data Engineering role building ETL pipelines.
            
            Need:
            - 2 years data engineering
            - Spark and Airflow
            - SQL and Postgres
            - Hadoop ecosystem
            - dbt for transformations
            """
        },
    ]
    
    # Parse
    parser = JDParser()
    
    print("=" * 100)
    print("JD UNDERSTANDING ENGINE - REGEX & KEYWORD EXTRACTION")
    print("=" * 100)
    print()
    
    for test_case in test_jds:
        print(f"Title: {test_case['title']}")
        print("-" * 100)
        
        result = parser.parse(test_case['jd'])
        
        print(f"Skills ({result['skill_count']}): {', '.join(result['skills'])}")
        print(f"Experience Required: {result['experience']} years")
        print(f"Domain: {result['domain']}")
        print(f"Leadership Required: {'Yes' if result['leadership'] else 'No'}")
        print()
    
    # Show extraction statistics
    print("=" * 100)
    print("EXTRACTION STATISTICS")
    print("=" * 100)
    
    all_skills = set()
    for test_case in test_jds:
        result = parser.parse(test_case['jd'])
        all_skills.update(result['skills'])
    
    print(f"Total unique skills extracted: {len(all_skills)}")
    print(f"Available domains: {len(parser.DOMAIN_KEYWORDS)}")
    print(f"Available skills database: {len(parser.TECH_SKILLS)}")
    print(f"Leadership keywords: {len(parser.LEADERSHIP_KEYWORDS)}")
    
    # Show some extracted skills
    print(f"\nSample skills found: {', '.join(sorted(list(all_skills))[:10])}")


if __name__ == "__main__":
    main()
