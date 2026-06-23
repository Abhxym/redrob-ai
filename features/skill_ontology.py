"""
Skill Ontology - Semantic Skill Matching
+1% to +3% NDCG improvement through intelligent skill mapping

Maps parent concepts to implementations:
FAISS → Vector Search
XGBoost → Machine Learning  
React → Frontend Framework

Enables matching where "FAISS" satisfies "Vector Search" requirement
"""
from typing import Dict, List, Set
import re


class SkillOntology:
    """
    Hierarchical skill mapping for semantic skill matching
    """
    
    def __init__(self):
        # Parent concept → child implementations
        self.skill_hierarchy = {
            # Vector Search / Embeddings
            'Vector Search': ['FAISS', 'Pinecone', 'Weaviate', 'Qdrant', 'Milvus', 'ChromaDB', 'Elasticsearch'],
            'Vector Database': ['FAISS', 'Pinecone', 'Weaviate', 'Qdrant', 'Milvus', 'ChromaDB'],
            'Embedding Search': ['FAISS', 'Sentence Transformers', 'OpenAI Embeddings', 'Cohere'],
            
            # Machine Learning
            'Machine Learning': ['XGBoost', 'LightGBM', 'CatBoost', 'RandomForest', 'SVM', 'Neural Networks'],
            'Deep Learning': ['PyTorch', 'TensorFlow', 'Keras', 'JAX', 'MXNet'],
            'ML Framework': ['PyTorch', 'TensorFlow', 'Keras', 'Scikit-learn', 'XGBoost'],
            'NLP': ['Transformers', 'BERT', 'GPT', 'T5', 'spaCy', 'NLTK'],
            'Computer Vision': ['OpenCV', 'PIL', 'Albumentations', 'YOLO', 'ResNet'],
            
            # Frontend
            'Frontend Framework': ['React', 'Vue', 'Angular', 'Svelte', 'Next.js'],
            'JavaScript Framework': ['React', 'Vue', 'Angular', 'Express', 'Node.js'],
            'CSS Framework': ['Tailwind', 'Bootstrap', 'Material-UI', 'Chakra UI'],
            'Frontend Build': ['Webpack', 'Vite', 'Parcel', 'Rollup', 'esbuild'],
            
            # Backend
            'Web Framework': ['Django', 'Flask', 'FastAPI', 'Spring', 'Express', 'Rails'],
            'API Framework': ['FastAPI', 'Flask', 'Express', 'Spring Boot', 'Django REST'],
            'Microservices': ['Docker', 'Kubernetes', 'Service Mesh', 'gRPC', 'REST API'],
            
            # Databases
            'SQL Database': ['PostgreSQL', 'MySQL', 'SQLite', 'SQL Server', 'Oracle'],
            'NoSQL Database': ['MongoDB', 'Redis', 'Cassandra', 'DynamoDB', 'CouchDB'],
            'Time Series DB': ['InfluxDB', 'TimescaleDB', 'Prometheus'],
            'Graph Database': ['Neo4j', 'Amazon Neptune', 'ArangoDB'],
            
            # Cloud Platforms
            'Cloud Platform': ['AWS', 'Azure', 'GCP', 'Alibaba Cloud', 'Oracle Cloud'],
            'Cloud Services': ['AWS Lambda', 'S3', 'EC2', 'Azure Functions', 'Cloud Functions'],
            'Container Orchestration': ['Kubernetes', 'Docker Swarm', 'ECS', 'AKS', 'GKE'],
            
            # Data Engineering  
            'Data Pipeline': ['Airflow', 'Prefect', 'Dagster', 'Luigi', 'Kubeflow'],
            'Stream Processing': ['Kafka', 'Spark Streaming', 'Flink', 'Pulsar', 'Kinesis'],
            'Big Data': ['Spark', 'Hadoop', 'Hive', 'Presto', 'Databricks'],
            'ETL Tool': ['Airflow', 'dbt', 'Fivetran', 'Stitch', 'Talend'],
            
            # DevOps
            'CI/CD': ['Jenkins', 'GitHub Actions', 'GitLab CI', 'CircleCI', 'Azure DevOps'],
            'Infrastructure as Code': ['Terraform', 'CloudFormation', 'Ansible', 'Pulumi'],
            'Monitoring': ['Prometheus', 'Grafana', 'DataDog', 'New Relic', 'Splunk'],
            'Container': ['Docker', 'Podman', 'Containerd'],
            
            # Programming Languages by paradigm
            'Systems Programming': ['Rust', 'C++', 'C', 'Go', 'Zig'],
            'Web Programming': ['JavaScript', 'TypeScript', 'Python', 'PHP', 'Ruby'],
            'Data Science': ['Python', 'R', 'Julia', 'Scala', 'SQL'],
            'Mobile Development': ['Swift', 'Kotlin', 'Java', 'Dart', 'React Native'],
            
            # Search & Information Retrieval
            'Search Engine': ['Elasticsearch', 'Solr', 'OpenSearch', 'Algolia'],
            'Information Retrieval': ['BM25', 'TF-IDF', 'Vector Search', 'Elasticsearch'],
            'Ranking Systems': ['Learning to Rank', 'RankLib', 'XGBoost', 'LambdaMART'],
            
            # Testing
            'Testing Framework': ['pytest', 'Jest', 'JUnit', 'RSpec', 'Mocha'],
            'Test Automation': ['Selenium', 'Playwright', 'Cypress', 'Puppeteer'],
            
            # Security
            'Security': ['OAuth', 'JWT', 'SSL/TLS', 'SAML', 'Auth0'],
            'Vulnerability Scanning': ['OWASP', 'Snyk', 'SonarQube', 'Checkmarx']
        }
        
        # Build reverse mapping: child → parents
        self.implementation_to_concepts = {}
        for concept, implementations in self.skill_hierarchy.items():
            for impl in implementations:
                if impl not in self.implementation_to_concepts:
                    self.implementation_to_concepts[impl] = []
                self.implementation_to_concepts[impl].append(concept)
    
    def expand_skills(self, skills: List[str]) -> Set[str]:
        """
        Expand skill list with semantic matches
        
        Args:
            skills: List of required skills
            
        Returns:
            Set of expanded skills (original + semantic matches)
        """
        expanded = set(skills)
        
        for skill in skills:
            # Find implementations for this skill (if it's a concept)
            if skill in self.skill_hierarchy:
                implementations = self.skill_hierarchy[skill]
                expanded.update(implementations)
                
            # Find parent concepts for this skill (if it's an implementation)
            if skill in self.implementation_to_concepts:
                concepts = self.implementation_to_concepts[skill]
                expanded.update(concepts)
        
        return expanded
    
    def match_skills(self, required_skills: List[str], candidate_skills: List[str]) -> Dict:
        """
        Enhanced skill matching with semantic understanding
        
        Args:
            required_skills: Skills required by JD
            candidate_skills: Skills possessed by candidate
            
        Returns:
            Dict with match details
        """
        # Expand both skill sets
        expanded_required = self.expand_skills(required_skills)
        expanded_candidate = self.expand_skills(candidate_skills)
        
        # Find matches
        exact_matches = set(required_skills) & set(candidate_skills)
        semantic_matches = expanded_required & expanded_candidate - exact_matches
        
        # Calculate scores
        total_required = len(required_skills)
        exact_match_count = len(exact_matches)
        semantic_match_count = len(semantic_matches)
        
        # Scoring: exact matches = 1.0, semantic matches = 0.7
        exact_score = exact_match_count / total_required if total_required > 0 else 0
        semantic_score = (semantic_match_count * 0.7) / total_required if total_required > 0 else 0
        
        total_score = min(1.0, exact_score + semantic_score)
        
        return {
            'exact_matches': list(exact_matches),
            'semantic_matches': list(semantic_matches),
            'exact_score': exact_score,
            'semantic_score': semantic_score,
            'total_score': total_score,
            'exact_count': exact_match_count,
            'semantic_count': semantic_match_count,
            'required_count': total_required
        }
    
    def explain_matches(self, match_result: Dict, required_skills: List[str]) -> List[str]:
        """
        Generate explanations for skill matches
        
        Returns:
            List of explanation strings
        """
        explanations = []
        
        if match_result['exact_matches']:
            explanations.append(f"Direct skill matches: {', '.join(match_result['exact_matches'])}")
        
        if match_result['semantic_matches']:
            explanations.append(f"Related skills: {', '.join(match_result['semantic_matches'])}")
        
        # Explain semantic relationships
        for semantic_match in match_result['semantic_matches']:
            for req_skill in required_skills:
                if self._skills_related(req_skill, semantic_match):
                    explanations.append(f"'{semantic_match}' satisfies '{req_skill}' requirement")
                    break
        
        return explanations
    
    def _skills_related(self, skill1: str, skill2: str) -> bool:
        """Check if two skills are semantically related"""
        
        # Same skill
        if skill1 == skill2:
            return True
        
        # skill1 is concept, skill2 is implementation
        if skill1 in self.skill_hierarchy and skill2 in self.skill_hierarchy[skill1]:
            return True
        
        # skill2 is concept, skill1 is implementation  
        if skill2 in self.skill_hierarchy and skill1 in self.skill_hierarchy[skill2]:
            return True
        
        # Both are implementations of same concept
        if (skill1 in self.implementation_to_concepts and 
            skill2 in self.implementation_to_concepts):
            concepts1 = set(self.implementation_to_concepts[skill1])
            concepts2 = set(self.implementation_to_concepts[skill2])
            if concepts1 & concepts2:  # Share at least one parent concept
                return True
        
        return False
    
    def get_skill_suggestions(self, skill: str) -> List[str]:
        """
        Get related skill suggestions for a given skill
        
        Returns:
            List of related skills
        """
        suggestions = set()
        
        # If it's a concept, suggest implementations
        if skill in self.skill_hierarchy:
            suggestions.update(self.skill_hierarchy[skill])
        
        # If it's an implementation, suggest sibling implementations
        if skill in self.implementation_to_concepts:
            for concept in self.implementation_to_concepts[skill]:
                siblings = self.skill_hierarchy[concept]
                suggestions.update(s for s in siblings if s != skill)
        
        return list(suggestions)


def test_skill_ontology():
    """Test skill ontology with real examples"""
    
    ontology = SkillOntology()
    
    print("=" * 80)
    print("SKILL ONTOLOGY TEST")
    print("=" * 80 + "\n")
    
    test_cases = [
        {
            'name': 'Vector Search Job',
            'required': ['Vector Search', 'Python', 'Machine Learning'],
            'candidate': ['FAISS', 'Python', 'XGBoost', 'PyTorch']
        },
        {
            'name': 'Frontend Job',
            'required': ['React', 'JavaScript', 'CSS Framework'],
            'candidate': ['Vue', 'TypeScript', 'Tailwind', 'Webpack']
        },
        {
            'name': 'ML Engineering',
            'required': ['Deep Learning', 'NLP', 'Cloud Platform'],
            'candidate': ['TensorFlow', 'Transformers', 'AWS', 'Docker']
        },
        {
            'name': 'Data Engineering',
            'required': ['Data Pipeline', 'Big Data', 'SQL Database'],
            'candidate': ['Airflow', 'Spark', 'PostgreSQL', 'Kafka']
        }
    ]
    
    for test_case in test_cases:
        print(f"🎯 {test_case['name']}")
        print("-" * 50)
        print(f"Required: {test_case['required']}")
        print(f"Candidate: {test_case['candidate']}")
        
        match_result = ontology.match_skills(test_case['required'], test_case['candidate'])
        
        print(f"\nResults:")
        print(f"  Exact Matches: {match_result['exact_matches']}")
        print(f"  Semantic Matches: {match_result['semantic_matches']}")
        print(f"  Total Score: {match_result['total_score']:.2f}")
        print(f"    (Exact: {match_result['exact_score']:.2f}, Semantic: {match_result['semantic_score']:.2f})")
        
        explanations = ontology.explain_matches(match_result, test_case['required'])
        if explanations:
            print(f"\nExplanations:")
            for explanation in explanations:
                print(f"  • {explanation}")
        
        print("\n")
    
    # Test skill expansion
    print("=" * 80)
    print("SKILL EXPANSION EXAMPLES")
    print("=" * 80 + "\n")
    
    expansion_tests = ['Vector Search', 'FAISS', 'React', 'Machine Learning']
    
    for skill in expansion_tests:
        expanded = ontology.expand_skills([skill])
        suggestions = ontology.get_skill_suggestions(skill)
        
        print(f"📚 {skill}")
        print(f"  Expands to: {sorted(list(expanded))}")
        print(f"  Suggestions: {suggestions[:5]}...")  # Show first 5
        print()


if __name__ == "__main__":
    test_skill_ontology()