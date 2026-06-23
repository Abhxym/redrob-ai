from retrieval import retrieve
from ranking import rank
from reasoning import reason
from outputs import save


def run_pipeline(job_description: str, candidates: list) -> None:
    retrieved = retrieve(job_description, candidates)
    ranked = rank(job_description, retrieved)
    reasoned = reason(job_description, ranked)
    save(reasoned)


if __name__ == "__main__":
    run_pipeline()
