import axios from 'axios';

// Empty base → same origin. In dev, Vite proxies /api to FastAPI on :8000.
const API_BASE = import.meta.env.VITE_API_BASE ?? '';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 120000, // first request warms up the embedding + cross-encoder models
});

/**
 * POST /api/rank
 * @param {string} jdText - Job description text
 * @param {number} topK - Number of candidates to return (1-50)
 */
export async function rankCandidates(jdText, topK = 10) {
  const { data } = await api.post('/api/rank', {
    jd_text: jdText,
    top_k: topK,
  });
  return data;
}

/**
 * GET /api/health
 */
export async function getHealth() {
  const { data } = await api.get('/api/health');
  return data;
}

/**
 * GET /api/candidates/:id
 */
export async function getCandidate(id) {
  const { data } = await api.get(`/api/candidates/${id}`);
  return data;
}
