// Helpers for turning the API's profile_text and score payloads into UI-ready data.

export const SIGNALS = [
  { key: 'semantic', label: 'Semantic', color: 'var(--c-semantic)', hint: 'Hybrid BM25 + FAISS relevance, fused with RRF' },
  { key: 'skills', label: 'Skills', color: 'var(--c-skills)', hint: 'JD skills matched via ontology, weighted by proficiency and endorsements' },
  { key: 'experience', label: 'Experience', color: 'var(--c-experience)', hint: 'Merged career-history years vs. JD requirement' },
  { key: 'behavior', label: 'Behavior', color: 'var(--c-behavior)', hint: 'Response, interview completion, GitHub, offers, assessments' },
  { key: 'career', label: 'Career', color: 'var(--c-career)', hint: 'Seniority level and title progression' },
  { key: 'cross_encoder', label: 'Cross-encoder', color: 'var(--c-ce)', hint: 'ms-marco MiniLM cross-encoder reading JD + profile together' },
];

const DEFAULT_WEIGHTS = { semantic: 0.4, skills: 0.25, experience: 0.15, behavior: 0.1, career: 0.1 };

// Effective share of the final score per signal. With the cross-encoder applied, final =
// feature_blend × (Σ weight × signal) + ce_blend × cross_encoder, so feature weights are scaled.
export function effectiveWeights(info) {
  const w = info?.weights ?? DEFAULT_WEIGHTS;
  const blend = info?.ce_blend;
  const f = blend ? blend.feature : 1;
  const out = {};
  for (const s of SIGNALS) {
    out[s.key] = s.key === 'cross_encoder' ? (blend ? blend.cross_encoder : 0) : (w[s.key] ?? 0) * f;
  }
  return out;
}

export function activeSignals(weights) {
  return SIGNALS.filter(s => weights[s.key] > 0);
}

function section(text, name) {
  // (?![\s\S]) is end-of-string; `$` would match every line end under the m flag.
  const re = new RegExp(`^${name}:[ \\t]*\\n([\\s\\S]*?)(?=\\n\\n[A-Z][A-Za-z ]+:|(?![\\s\\S]))`, 'm');
  const m = text.match(re);
  return m ? m[1].trim() : '';
}

function field(text, name) {
  const m = text.match(new RegExp(`^${name}:\\s*(.+)$`, 'm'));
  return m ? m[1].trim() : '';
}

export function parseProfileText(text = '') {
  const skillsLine = section(text, 'Skills') || field(text, 'Skills');

  const history = [];
  for (const block of section(text, 'Career History').split(/\n\s*-\s+/)) {
    const lines = block.replace(/^\s*-\s+/, '').split('\n');
    const head = lines[0]?.trim();
    if (!head) continue;
    const m = head.match(/^(.*?) at (.*?)(?: \((current)\))?(?: \[(\d+) months\])?$/);
    history.push({
      title: m ? m[1] : head,
      company: m ? m[2] : '',
      current: Boolean(m?.[3]),
      months: m?.[4] ? Number(m[4]) : null,
      description: lines.slice(1).join(' ').trim(),
    });
  }

  const education = section(text, 'Education')
    .split('\n')
    .map(l => l.replace(/^\s*-\s+/, '').trim())
    .filter(Boolean);

  const signals = {};
  for (const line of section(text, 'Platform Signals').split('\n')) {
    for (const pair of line.split('|')) {
      const idx = pair.indexOf(':');
      if (idx > 0) signals[pair.slice(0, idx).trim()] = pair.slice(idx + 1).trim();
    }
  }

  const assessments = section(text, 'Skill Assessments')
    .split(',')
    .map(s => s.trim().match(/^(.*?):\s*(\d+)\/100$/))
    .filter(Boolean)
    .map(m => ({ skill: m[1], score: Number(m[2]) }));

  return {
    headline: field(text, 'Headline'),
    currentRole: field(text, 'Current Role'),
    location: field(text, 'Location'),
    experienceYears: parseFloat(field(text, 'Experience')) || 0,
    summary: section(text, 'Summary'),
    skills: skillsLine.split(',').map(s => s.trim()).filter(Boolean),
    history,
    education,
    signals,
    assessments,
  };
}

// Skills mentioned in the JD, used to highlight matches. Case-insensitive word match.
export function jdMentions(jdText, skill) {
  if (!jdText || !skill) return false;
  const escaped = skill.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  return new RegExp(`(^|[^a-z0-9])${escaped}([^a-z0-9]|$)`, 'i').test(jdText);
}

export function initials(text) {
  const words = (text || '?').replace(/[^A-Za-z ]/g, ' ').split(/\s+/).filter(Boolean);
  return (words[0]?.[0] || '?').toUpperCase() + (words[1]?.[0] || '').toUpperCase();
}

export function pct(v) {
  return `${Math.round((v ?? 0) * 100)}`;
}

export function toCsv(rows, weights) {
  const header = ['rank', 'candidate_id', 'current_title', 'location', 'experience_years', 'final_score',
    ...SIGNALS.map(s => `${s.key}_score`), 'matched_skills', 'effective_weights', 'reasoning'];
  const esc = v => {
    const s = String(v ?? '');
    return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  const w = SIGNALS.map(s => `${s.key}=${weights[s.key].toFixed(3)}`).join(' ');
  const lines = rows.map(r =>
    [r.rank, r.candidate_id, r.current_title, r.location, r.experience_years, r.final_score,
      ...SIGNALS.map(s => r.scores[s.key]), r.matched_skills.join('; '), w, r.reasoning.join(' | ')]
      .map(esc).join(','));
  return [header.join(','), ...lines].join('\n');
}

export const SAMPLE_JDS = [
  {
    label: 'Senior ML Engineer',
    text: `Senior Machine Learning Engineer

We're hiring a Senior ML Engineer with 5+ years of experience to build and ship production ranking and recommendation systems.

Requirements:
- Strong Python, PyTorch, and scikit-learn
- Experience with NLP, embeddings, and vector search (FAISS, Milvus)
- MLOps: model serving, monitoring, Docker, Kubernetes, AWS or GCP
- Experience mentoring engineers and leading technical design

Nice to have: LLM fine-tuning (LoRA), Spark, Airflow.`,
  },
  {
    label: 'Data Engineer',
    text: `Data Engineer (3+ years)

Own our batch and streaming data platform.

Requirements:
- Python and SQL expertise
- Spark, Kafka, and Airflow in production
- Data warehouse design (Snowflake or BigQuery), dbt
- Data quality monitoring and on-call ownership
- Cloud experience on AWS or GCP

Bonus: experience supporting ML feature pipelines.`,
  },
  {
    label: 'Computer Vision',
    text: `Computer Vision Engineer

Looking for an engineer with 4+ years building image and video models.

Requirements:
- Image Classification, Object Detection, Segmentation
- PyTorch or TensorFlow, OpenCV
- Model optimization for edge deployment (ONNX, TensorRT)
- Experience with GANs or diffusion models is a plus
- Comfortable with experiment tracking (Weights & Biases)`,
  },
];
