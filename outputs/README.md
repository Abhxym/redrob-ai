# Outputs Directory

This directory contains the generated submission files.

## Files

### submission.csv
Standard submission format required for evaluation:
```csv
jd_id,candidate_id,rank,score
JD001,CAND_0000031,1,0.847000
JD001,CAND_0000043,2,0.782000
...
```

### submission_detailed.csv
Extended format with score breakdown and reasoning:
```csv
jd_id,candidate_id,rank,final_score,semantic_score,skill_score,experience_score,behavior_score,career_score,availability_score,reasoning
JD001,CAND_0000031,1,0.847000,0.0280,0.8000,1.0000,0.7800,0.8500,0.7500,"Strong match on Python, FAISS, ML | 6 years experience"
...
```

## Validation

Submission files are automatically validated for:
- Required headers (jd_id, candidate_id, rank, score)
- Unique candidates (no duplicates)
- Sequential ranks (1, 2, 3, ...)
- Descending scores
- Valid score format (float)

## Usage

Generated automatically by running:
```bash
python demo.py
# or
python run.py sample_jd.txt
```
