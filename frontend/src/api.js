import axios from 'axios';

const API_BASE = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 60000, // pipeline can take up to 200ms, but allow more for startup
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
 * GET /api/candidates
 */
export async function getCandidates() {
  const { data } = await api.get('/api/candidates');
  return data;
}

/**
 * GET /api/candidates/:id
 */
export async function getCandidate(id) {
  const { data } = await api.get(`/api/candidates/${id}`);
  return data;
}
