/* global React, ReactDOM, STEPS, RECS, ADDENDA, GLOSSARY, katex */
const { useState, useMemo, useEffect, useRef } = React;

// ─── Math rendering ───────────────────────────────────────────────────────────

function KatexMath({ expr, display = false }) {
  // throwOnError:false renders a visible KaTeX error node for malformed input,
  // which surfaces authoring mistakes rather than silently hiding them.
  const html = katex.renderToString(expr, {
    throwOnError: false,
    displayMode: display,
    output: "html",
  });
  return <span dangerouslySetInnerHTML={{ __html: html }} />;
}

// Splits text on $$...$$ (display) and $...$ (inline) tokens; renders with KaTeX.
function MathText({ text }) {
  if (!text) return null;
  const parts = text.split(/(\$\$[^$]+\$\$|\$[^$]+\$)/g);
  return (
    <>
      {parts.map((part, i) => {
        if (part.startsWith("$$") && part.endsWith("$$")) {
          return <KatexMath key={i} expr={part.slice(2, -2)} display={true} />;
        }
        if (part.startsWith("$") && part.endsWith("$")) {
          return <KatexMath key={i} expr={part.slice(1, -1)} />;
        }
        return <span key={i}>{part}</span>;
      })}
    </>
  );
}

// ─── Tooltip (glossary hover) ─────────────────────────────────────────────────

function Tooltip({ keys }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  const entries = (keys || []).map((k) => GLOSSARY[k]).filter(Boolean);

  // Close on outside click. Hooks must run unconditionally, so this effect is
  // declared before any early return.
  useEffect(() => {
    if (!open) return;
    function handler(e) {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    }
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  if (entries.length === 0) return null;

  return (
    <span className="tip-wrap" ref={ref}>
      <button
        className="tip-badge"
        aria-label="Glossary definitions"
        aria-expanded={open}
        onClick={(e) => { e.stopPropagation(); setOpen((v) => !v); }}
        type="button"
      >?</button>
      {open && (
        <div className="tip-pop" role="tooltip">
          {entries.map((entry, i) => (
            <div key={i} className="tip-entry">
              <div className="tip-term">{entry.term}</div>
              <div className="tip-def"><MathText text={entry.definition} /></div>
            </div>
          ))}
        </div>
      )}
    </span>
  );
}

// ─── Path & state ────────────────────────────────────────────────────────────
const ENTRY = "data_structure";

function useWizard() {
  const [trail, setTrail] = useState([]); // [{stepId, optionId, label, short}]
  const [terminal, setTerminal] = useState(null); // recommendation id

  const clusterTerminals = useMemo(
    () => new Set(["crve_standard", "crve_cr2", "crve_smallG", "crve_tinyG", "crve_twoway"]),
    []
  );

  const flags = useMemo(() => {
    const f = new Set();
    for (const t of trail) if (t.flag) f.add(t.flag);
    if (trail.find((t) => t.stepId === "data_structure" && t.optionId === "panel")) f.add("panel");
    if (
      trail.find((t) => t.stepId === "cluster_dimensions" || t.stepId === "num_clusters") ||
      clusterTerminals.has(terminal)
    ) {
      f.add("k_bm");
    }
    return f;
  }, [trail, terminal, clusterTerminals]);

  const currentStepId = useMemo(() => {
    if (terminal) return null;
    if (trail.length === 0) return ENTRY;
    const last = trail[trail.length - 1];
    return last.next ?? null;
  }, [trail, terminal]);

  function resolveRoute(opt) {
    for (const route of opt.routes || []) {
      const anyFlags = route.ifAnyFlag || [];
      const allFlags = route.ifAllFlags || [];
      const anyMatch = anyFlags.length === 0 || anyFlags.some((flag) => flags.has(flag));
      const allMatch = allFlags.every((flag) => flags.has(flag));
      if (anyMatch && allMatch) return route;
    }
    return opt;
  }

  function choose(stepId, opt) {
    const route = resolveRoute(opt);
    const entry = {
      stepId,
      optionId: opt.id,
      label: opt.label,
      short: STEPS[stepId].short,
      flag: opt.flag,
      next: route.next ?? null,
      terminal: route.terminal ?? null,
    };
    const newTrail = [...trail, entry];
    setTrail(newTrail);
    if (entry.terminal) setTerminal(entry.terminal);
  }

  function back() {
    if (terminal) {
      setTerminal(null);
      setTrail(trail.slice(0, -1));
      return;
    }
    setTrail(trail.slice(0, -1));
  }

  function reset() {
    setTrail([]);
    setTerminal(null);
  }

  function jumpTo(idx) {
    setTrail(trail.slice(0, idx));
    setTerminal(null);
  }

  return { trail, currentStepId, terminal, flags, choose, back, reset, jumpTo };
}

// ─── Components ──────────────────────────────────────────────────────────────

function Header({ onReset, hasProgress }) {
  return (
    <header className="hdr">
      <div className="hdr-l">
        <div className="hdr-eyebrow">Decision tree</div>
        <h1 className="hdr-title">Choosing a standard error</h1>
        <div className="hdr-sub">Answer in order. Each step narrows the options. Most practitioners can stop by Step 6.</div>
      </div>
      <div className="hdr-r">
        <button className="btn btn-ghost" disabled={!hasProgress} onClick={onReset}>Restart</button>
      </div>
    </header>
  );
}

function Stepper({ trail, currentStepId, terminal }) {
  const visited = trail.map((t) => t.stepId);
  const visibleSteps = [...visited];
  if (currentStepId) visibleSteps.push(currentStepId);
  const minDots = 6;
  const dots = [];
  for (let i = 0; i < Math.max(visibleSteps.length + (terminal ? 1 : 0), minDots); i++) {
    const isVisited = i < visited.length;
    const isCurrent = i === visited.length && !terminal;
    const isTerminalDot = terminal && i === visited.length;
    dots.push(
      <div key={i} className={`dot ${isVisited ? "dot-done" : ""} ${isCurrent ? "dot-now" : ""} ${isTerminalDot ? "dot-end" : ""}`}>
        <span className="dot-i">{i + 1}</span>
      </div>
    );
  }
  return <div className="stepper">{dots}</div>;
}

function Question({ step, onChoose }) {
  if (!step) return null;
  return (
    <div className="qcard">
      <div className="qhead">
        <div className="qnum">Step {step.n}</div>
        <h2 className="qtitle">{step.title}</h2>
        {step.why && <p className="qwhy"><MathText text={step.why} /></p>}
      </div>
      <div className="qopts">
        {step.options.map((opt) => (
          // role="button" div (not <button>) so the glossary Tooltip's own
          // <button> is not nested inside a button (invalid HTML).
          <div
            key={opt.id}
            className="ans"
            role="button"
            tabIndex={0}
            onClick={() => onChoose(opt)}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") { e.preventDefault(); onChoose(opt); }
            }}
          >
            <div className="ans-marker" aria-hidden="true">
              <span className="ans-marker-inner" />
            </div>
            <div className="ans-body">
              <div className="ans-label">
                <MathText text={opt.label} />
                {opt.tooltip && opt.tooltip.length > 0 && (
                  <Tooltip keys={opt.tooltip} />
                )}
              </div>
              <div className="ans-desc"><MathText text={opt.desc} /></div>
            </div>
            <div className="ans-arrow" aria-hidden="true">→</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function Recommendation({ recId, flags, onBack, onReset }) {
  const rec = RECS[recId];
  if (!rec) return null;
  const addenda = [];
  if (flags.has("panel")) addenda.push(ADDENDA.panel);
  if (flags.has("sampled_clusters")) addenda.push(ADDENDA.sampled_clusters);
  if (flags.has("k_bm")) addenda.push(ADDENDA.k_bm);
  if (flags.has("exogenous")) addenda.push(ADDENDA.exogenous);
  if (flags.has("observational_confounded")) addenda.push(ADDENDA.observational_confounded);

  return (
    <div className="rec">
      <div className="rec-eyebrow">Recommendation</div>
      <h2 className="rec-headline">{rec.headline}</h2>
      <div className="rec-tag">{rec.tagline}</div>
      <p className="rec-body"><MathText text={rec.body} /></p>

      <div className="rec-section">
        <div className="rec-label">Primary estimator</div>
        <div className="rec-primary"><MathText text={rec.primary} /></div>
      </div>

      {rec.code && rec.code.length > 0 && (
        <div className="rec-section">
          <div className="rec-label">Implementation</div>
          <div className="codeblocks">
            {rec.code.map(([env, snippet], i) => (
              <div className="codeblock" key={i}>
                <div className="codeblock-env">{env}</div>
                <pre className="codeblock-pre"><code>{snippet}</code></pre>
              </div>
            ))}
          </div>
        </div>
      )}

      {rec.checks && rec.checks.length > 0 && (
        <div className="rec-section">
          <div className="rec-label">Robustness & caveats</div>
          <ul className="rec-checks">
            {rec.checks.map((c, i) => <li key={i}><MathText text={c} /></li>)}
          </ul>
        </div>
      )}

      {addenda.length > 0 && (
        <div className="rec-section">
          <div className="rec-label">Also applies to your case</div>
          <div className="addenda">
            {addenda.map((a, i) => (
              <div className="addendum" key={i}>
                <div className="addendum-t">{a.title}</div>
                <div className="addendum-b"><MathText text={a.body} /></div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="rec-actions">
        <button className="btn btn-ghost" onClick={onBack}>← Revise last answer</button>
        <button className="btn btn-primary" onClick={onReset}>Start over</button>
      </div>
    </div>
  );
}

function PathTrail({ trail, onJump, currentStepId, terminal }) {
  return (
    <aside className="trail">
      <div className="trail-h">Your path</div>
      {trail.length === 0 && !currentStepId && (
        <div className="trail-empty">Begin by choosing your data structure →</div>
      )}
      <ol className="trail-list">
        {trail.map((t, i) => (
          <li key={i} className="trail-item">
            <button className="trail-btn" onClick={() => onJump(i)} title="Jump back to this step">
              <div className="trail-step">Step {STEPS[t.stepId].n} · {t.short}</div>
              <div className="trail-choice">{t.label}</div>
            </button>
          </li>
        ))}
        {currentStepId && !terminal && (
          <li className="trail-item trail-now">
            <div className="trail-step">Step {STEPS[currentStepId].n} · {STEPS[currentStepId].short}</div>
            <div className="trail-choice trail-pending">…awaiting answer</div>
          </li>
        )}
        {terminal && (
          <li className="trail-item trail-final">
            <div className="trail-step">Recommendation</div>
            <div className="trail-choice">{RECS[terminal].headline}</div>
          </li>
        )}
      </ol>

      <div className="trail-foot">
        <details>
          <summary>How this tree works</summary>
          <p>
            The right SE is determined by the <em>sampling mechanism</em> and the <em>design (assignment) mechanism</em>—
            not by what residual correlation looks like. Residuals are a symptom; design is the cause.
          </p>
          <p>
            Two studies with identical residual patterns can need entirely different SEs. Work the questions in order;
            each one narrows the options.
          </p>
        </details>
      </div>
    </aside>
  );
}

function App() {
  const w = useWizard();
  const step = w.currentStepId ? STEPS[w.currentStepId] : null;

  return (
    <div className="shell">
      <Header onReset={w.reset} hasProgress={w.trail.length > 0 || !!w.terminal} />
      <Stepper trail={w.trail} currentStepId={w.currentStepId} terminal={w.terminal} />

      <main className="grid">
        <section className="main">
          {step && <Question step={step} onChoose={(opt) => w.choose(w.currentStepId, opt)} />}
          {w.terminal && (
            <Recommendation recId={w.terminal} flags={w.flags} onBack={w.back} onReset={w.reset} />
          )}
          {step && w.trail.length > 0 && (
            <div className="back-row">
              <button className="btn btn-ghost btn-sm" onClick={w.back}>← Back</button>
            </div>
          )}
        </section>

        <PathTrail trail={w.trail} onJump={w.jumpTo} currentStepId={w.currentStepId} terminal={w.terminal} />
      </main>

      <footer className="ftr">
        <span>Synthesis of Abadie–Athey–Imbens–Wooldridge (2023, 2020), Bell &amp; McCaffrey (2002), Cameron &amp; Miller (2015), Cameron–Gelbach–Miller (2011), Bertrand–Duflo–Mullainathan (2004), Conley &amp; Kelly (2025), Imbens &amp; Kolesár (2016), Jackson (2019), Moulton (1986), Newey–West (1987, 1994), Andrews (1991), Webb (2014), Wooldridge (2023), Gelman (2023).</span>
      </footer>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
