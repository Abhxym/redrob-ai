"""
Skill Match Score: matched_skills / required_skills
"""
import re

class SkillScorer:
    def __init__(self):
        self.skills_db = [
            "Python", "Java", "JavaScript", "TypeScript", "C++", "Go", "Rust", "Scala", "Ruby", "PHP",
            "SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch", "Cassandra", "DynamoDB",
            "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Terraform", "Jenkins", "CI/CD",
            "TensorFlow", "PyTorch", "Scikit-learn", "Keras", "XGBoost", "Spark", "Hadoop", "Kafka",
            "Pandas", "NumPy", "Airflow", "DBT", "Snowflake", "Redshift", "BigQuery",
            "React", "Vue", "Angular", "Node.js", "Express", "Django", "Flask", "FastAPI", "Spring Boot",
            "FAISS", "Pinecone", "Weaviate", "Milvus", "Vector Database", "RAG", "LLM", "NLP",
            "Git", "Linux", "REST API", "GraphQL", "Microservices", "System Design", "Data Structures",
            "Algorithms", "Machine Learning", "Deep Learning", "Computer Vision", "Reinforcement Learning",
            "A/B Testing", "Metrics", "ETL", "Data Pipeline", "Distributed Systems", "BERT", "Transformers",
            "Recommendation Systems", "Ranking", "Search", "Information Retrieval", "BM25", "NDCG"
        ]
    
    def extract_skills(self, text):
        """Extract skills from text (case-insensitive)"""
        text_lower = text.lower()
        found = set()
        for skill in self.skills_db:
            if re.search(r'\b' + re.escape(skill.lower()) + r'\b', text_lower):
                found.add(skill)
        return found
    
    def compute_score(self, candidate_profile, required_skills):
        """
        Score = matched_skills / required_skills
        
        Args:
            candidate_profile (str): Candidate's profile text
            required_skills (list): Required skills from JD
        
        Returns:
            float: Score in [0.0, 1.0]
        """
        if not required_skills:
            return 1.0
        
        candidate_skills = self.extract_skills(candidate_profile)
        required_set = set(required_skills)
        
        matched = candidate_skills & required_set
        score = len(matched) / len(required_set)
        
        return min(score, 1.0)


if __name__ == "__main__":
    scorer = SkillScorer()
    
    # Test cases
    profile1 = "Senior Engineer with 8 years in Python, PyTorch, FAISS, and AWS. Built RAG systems."
    profile2 = "Backend developer skilled in Java, Spring Boot, MySQL, and Docker."
    
    required = ["Python", "PyTorch", "FAISS", "AWS", "Kubernetes"]
    
    score1 = scorer.compute_score(profile1, required)
    score2 = scorer.compute_score(profile2, required)
    
    print(f"Profile 1 score: {score1:.2f} (4/5 match)")
    print(f"Profile 2 score: {score2:.2f} (0/5 match)")
