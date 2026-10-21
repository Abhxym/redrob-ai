import { ArrowUpRight } from 'lucide-react';
import Composer from './Composer.jsx';

function Diamond() {
  return <span className="diamond" aria-hidden="true" />;
}

// Bento cards use real facts about the pipeline, not decoration.
export default function Landing({ health, onSubmit, loading, notReady }) {
  const profiles = health?.candidates_loaded ? `${Math.round(health.candidates_loaded / 1000)}k` : '100k';

  return (
    <section className="hero">
      <div className="bento">
        <div className="bento-col">
          <article className="card card-split">
            <div className="card-top">
              <div className="stat">{profiles}</div>
              <span className="round-btn"><ArrowUpRight size={18} /></span>
            </div>
            <p className="card-note">Candidate profiles indexed</p>
            <div className="card-media" aria-hidden="true">
              <div className="stack">
                {Array.from({ length: 7 }, (_, i) => <span key={i} style={{ '--i': i }} />)}
              </div>
            </div>
          </article>

          <article className="card card-sand">
            <div className="card-top">
              <h3 className="card-title">Hybrid<br />retrieval</h3>
              <span className="tag tag-yellow">RRF</span>
            </div>
            <div className="card-foot">
              <p className="card-note">BM25 for exact skills, FAISS for meaning, merged by reciprocal rank fusion.</p>
              <div className="price"><span>top 100</span><small>of 100k</small></div>
            </div>
          </article>

          <article className="card ticket">
            <div className="ticket-row"><span>JD in</span><span>shortlist out</span></div>
            <div className="ticket-main">
              <div>
                <div className="stat">~13s</div>
                <p className="card-note">per ranking, CPU only</p>
              </div>
              <span className="barcode" aria-hidden="true" />
            </div>
          </article>
        </div>

        <div className="bento-col">
          <div className="chip-outline">
            <span className="diamonds" aria-hidden="true"><Diamond /><Diamond /><Diamond /><Diamond /><Diamond /></span>
            <span>0 LLM calls</span>
          </div>

          <article className="card card-sand">
            <div className="dots" aria-hidden="true">
              <span>BM25</span><span>FAISS</span><span>CE</span>
            </div>
            <h3 className="card-title">Five signals</h3>
            <p className="card-note">Semantic fit, skills, experience, behaviour and career, weighted for the type of role.</p>
          </article>

          <article className="card card-sand card-tall">
            <div className="card-head-row"><span className="card-note">Cross-encoder</span><span aria-hidden="true">···</span></div>
            <div className="orb" aria-hidden="true"><span>70/30</span></div>
            <h3 className="card-title">Reranked</h3>
            <p className="card-note">A MiniLM cross-encoder reads the JD and each profile together.</p>
          </article>
        </div>
      </div>

      <div className="hero-copy">
        <h1>
          Explainable candidate ranking you can{' '}
          <span className="nowrap">defend<span className="mark" aria-hidden="true"><span /><span><Diamond /></span></span></span>
        </h1>
        <p className="lede">
          Paste a job description and get a ranked shortlist from 100,000 profiles. Every score is broken down
          into the signals behind it, and every candidate comes with plain reasons, so you can explain why
          someone is at the top.
        </p>

        <Composer onSubmit={onSubmit} loading={loading} notReady={notReady} />

        <div className="duo" id="how">
          <article className="card card-flat">
            <div className="card-top"><Diamond /><span className="rule" /></div>
            <div className="stat">5 + 1</div>
            <p className="card-note">feature signals plus a cross-encoder, each shown with its weight.</p>
          </article>
          <article className="card card-flat">
            <div className="card-top"><Diamond /><span className="rule" /><span className="tag">offline</span></div>
            <div className="stat">$0</div>
            <p className="card-note">per query. Deterministic, the same JD always gives the same ranking.</p>
          </article>
        </div>
      </div>
    </section>
  );
}
