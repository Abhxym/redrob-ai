"""
preprocessing/build_candidate_profiles.py

Converts raw candidate JSON into recruiter-style plain-text profile documents
suitable for embedding models.

Output: data/candidate_profiles.json
  [{"candidate_id": "CAND_0000001", "profile_text": "..."}, ...]
"""

import json
import pathlib

RAW_DATA = pathlib.Path(
    "[PUB] India_runs_data_and_ai_challenge/"
    "India_runs_data_and_ai_challenge/sample_candidates.json"
)
OUTPUT = pathlib.Path("data/candidate_profiles.json")

PROFICIENCY_ORDER = ["beginner", "intermediate", "advanced", "expert"]


def _skills_text(skills: list) -> str:
    # Sort by proficiency (desc) then endorsements (desc) for most relevant first
    sorted_skills = sorted(
        skills,
        key=lambda s: (PROFICIENCY_ORDER.index(s.get("proficiency", "beginner")), s.get("endorsements", 0)),
        reverse=True,
    )
    return ", ".join(s["name"] for s in sorted_skills)


def _career_text(career: list) -> str:
    lines = []
    for job in career:
        status = " (current)" if job.get("is_current") else ""
        duration = f"{job['duration_months']} months"
        lines.append(f"  - {job['title']} at {job['company']}{status} [{duration}]")
        if job.get("description"):
            lines.append(f"    {job['description'].strip()}")
    return "\n".join(lines)


def _education_text(education: list) -> str:
    lines = []
    for edu in education:
        tier = edu.get("tier", "")
        tier_str = f" ({tier})" if tier else ""
        lines.append(
            f"  - {edu['degree']} in {edu['field_of_study']}, "
            f"{edu['institution']}{tier_str} ({edu['start_year']}–{edu['end_year']})"
        )
    return "\n".join(lines)


def _certifications_text(certs: list) -> str:
    return ", ".join(f"{c['name']} by {c['issuer']} ({c['year']})" for c in certs)


def _signals_text(signals: dict) -> str:
    github = signals["github_activity_score"]
    github_str = f"{github}/100" if github != -1 else "not linked"

    offer = signals["offer_acceptance_rate"]
    offer_str = f"{offer:.0%}" if offer != -1 else "no history"

    salary = signals["expected_salary_range_inr_lpa"]
    sal_min, sal_max = sorted([salary["min"], salary["max"]])  # fix inverted ranges

    return (
        f"  Open to work: {signals['open_to_work_flag']} | "
        f"Notice: {signals['notice_period_days']} days | "
        f"Work mode: {signals['preferred_work_mode']} | "
        f"Relocate: {signals['willing_to_relocate']}\n"
        f"  GitHub activity: {github_str} | "
        f"Recruiter response rate: {signals['recruiter_response_rate']:.0%} | "
        f"Interview completion: {signals['interview_completion_rate']:.0%} | "
        f"Offer acceptance: {offer_str}\n"
        f"  Expected salary: {sal_min}–{sal_max} LPA INR"
    )


def build_profile_text(candidate: dict) -> str:
    p = candidate["profile"]
    signals = candidate["redrob_signals"]

    sections = [
        f"Candidate ID: {candidate['candidate_id']}",
        f"Headline: {p['headline']}",
        f"Current Role: {p['current_title']} at {p['current_company']} ({p['current_industry']})",
        f"Location: {p['location']}, {p['country']}",
        f"Experience: {p['years_of_experience']} years",
        "",
        "Summary:",
        p["summary"].strip(),
        "",
        "Skills:",
        _skills_text(candidate["skills"]),
    ]

    if candidate.get("certifications"):
        sections += ["", "Certifications:", _certifications_text(candidate["certifications"])]

    sections += [
        "",
        "Career History:",
        _career_text(candidate["career_history"]),
        "",
        "Education:",
        _education_text(candidate["education"]),
        "",
        "Platform Signals:",
        _signals_text(signals),
    ]

    if signals.get("skill_assessment_scores"):
        scores = ", ".join(
            f"{skill}: {score:.0f}/100"
            for skill, score in signals["skill_assessment_scores"].items()
        )
        sections += ["", "Skill Assessments:", f"  {scores}"]

    return "\n".join(sections)


def build_profiles(input_path: pathlib.Path, output_path: pathlib.Path) -> None:
    with open(input_path, encoding="utf-8") as f:
        candidates = json.load(f)

    profiles = [
        {"candidate_id": c["candidate_id"], "profile_text": build_profile_text(c)}
        for c in candidates
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(profiles, f, indent=2, ensure_ascii=False)

    print(f"Built {len(profiles)} profiles -> {output_path}")


if __name__ == "__main__":
    build_profiles(RAW_DATA, OUTPUT)
