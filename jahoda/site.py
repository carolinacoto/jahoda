"""Render the deployed site (public/index.html) from a committed report.

Matches the design reference's instrument aesthetic EXACTLY (paper/oxblood,
editorial-but-clinical). The provenance line and stat band are verbatim. The
report section is data-driven; the specimen chat opens mid-conversation on the
seeded exchange and continues live via /api/chat.
"""

from __future__ import annotations

import html
import json
from pathlib import Path

from jahoda.criteria import Criterion
from jahoda.report_html import _dim_passes
from jahoda.schemas import DimensionResult, Report, ScenarioResult, VerdictValue

REPO = "https://github.com/carolinacoto/jahoda"

PROVENANCE = (
    "OMBRUJA is building an AI guide — in layers. "
    "<em>JAHODA is the verification layer</em>: built first, and built in the open."
)

CSS = """
:root{--paper:#faf8f4;--ink:#16130f;--muted:#6b645a;--accent:#7a1f2b;--accent-soft:#f3e6e3;
--pass:#2e5e43;--pass-soft:#e7efe9;--fail:#8c2f1d;--fail-soft:#f6e9e4;--line:#e4ded4;
--card:#ffffff;--excerpt:#fffdf8;}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--paper);color:var(--ink);font-family:'Helvetica Neue',Arial,sans-serif;
line-height:1.55;-webkit-font-smoothing:antialiased}
.serif{font-family:Georgia,'Times New Roman',serif}
.wrap{max-width:880px;margin:0 auto;padding:0 28px}
header{border-bottom:1px solid var(--line);padding:18px 0;background:var(--paper);position:sticky;top:0;z-index:9}
.bar{display:flex;align-items:baseline;justify-content:space-between}
.wordmark{font-family:Georgia,serif;font-size:22px;letter-spacing:.12em;font-weight:700}
.wordmark span{color:var(--accent)}
.bar nav a{color:var(--muted);text-decoration:none;font-size:13px;margin-left:22px;letter-spacing:.04em}
.bar nav a:hover{color:var(--ink)}
.hero{padding:72px 0 56px;border-bottom:1px solid var(--line)}
.kicker{font-size:12px;letter-spacing:.22em;text-transform:uppercase;color:var(--accent);margin-bottom:18px}
.provenance{font-family:Georgia,serif;font-size:18px;line-height:1.65;color:var(--ink);max-width:680px;
border-left:3px solid var(--accent);padding:4px 0 4px 20px;margin:26px 0 30px}
.provenance em{color:var(--accent);font-style:italic}
h1{font-family:Georgia,serif;font-size:40px;line-height:1.18;font-weight:400;max-width:760px;margin-bottom:22px}
h1 em{color:var(--accent);font-style:italic}
.hero p{max-width:640px;color:var(--muted);font-size:16.5px;margin-bottom:28px}
.stats{display:flex;border:1px solid var(--line);background:var(--card);border-radius:4px;margin:0 0 26px;flex-wrap:wrap}
.stat-block{flex:1;min-width:200px;padding:20px 24px;border-left:1px solid var(--line)}
.stat-block:first-child{border-left:0}
.stat-num{font-family:Georgia,serif;font-size:36px;color:var(--accent);line-height:1.1}
.stat-lab{font-size:12.5px;color:var(--muted);margin-top:6px;line-height:1.5}
.stat-lab i{font-style:normal;color:var(--ink)}
.dims{display:flex;flex-wrap:wrap;gap:8px}
.dim{font-size:12px;letter-spacing:.05em;border:1px solid var(--line);background:var(--card);
border-radius:3px;padding:5px 11px;color:var(--muted)}
.dim b{color:var(--ink);font-weight:600}
.section-label{font-size:11.5px;letter-spacing:.22em;text-transform:uppercase;color:var(--muted);margin:54px 0 18px}
.verdict{background:var(--card);border:1px solid var(--line);border-radius:4px;padding:26px 30px;
display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:18px}
.verdict h2{font-family:Georgia,serif;font-size:23px;font-weight:400}
.verdict .meta{color:var(--muted);font-size:13px;margin-top:6px;max-width:640px;line-height:1.6}
.badge{font-size:13px;letter-spacing:.08em;padding:8px 16px;border-radius:3px;font-weight:600}
.badge.pass{background:var(--pass-soft);color:var(--pass);border:1px solid #c9dccf}
.badge.fail{background:var(--fail-soft);color:var(--fail);border:1px solid #e3c4ba}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(265px,1fr));gap:14px;margin-top:14px}
.card{background:var(--card);border:1px solid var(--line);border-radius:4px;padding:20px 22px}
.card .top{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:6px}
.card h3{font-family:Georgia,serif;font-size:17.5px;font-weight:600;text-transform:capitalize}
.card h3 a{color:inherit;text-decoration:none;border-bottom:1px dotted var(--line)}
.pf{font-size:11px;font-weight:700;letter-spacing:.1em;padding:3px 9px;border-radius:2px}
.pf.pass{background:var(--pass-soft);color:var(--pass)}
.pf.fail{background:var(--fail-soft);color:var(--fail)}
.pf.hist{background:var(--fail-soft);color:var(--fail)}
.card .src{font-size:12px;color:var(--muted);font-style:italic;margin-bottom:10px}
.card .stat{font-size:13.5px}.card .stat b{font-weight:600}
.card .sub{font-size:12px;color:var(--muted);margin-top:6px}
.note-fixed{font-size:12px;color:var(--fail);margin-top:8px}
details{background:var(--card);border:1px solid var(--line);border-radius:4px;margin-top:10px}
summary{cursor:pointer;padding:15px 20px;font-size:14px;display:flex;align-items:center;gap:12px;flex-wrap:wrap}
summary:hover{background:var(--paper)}
summary .pf{flex-shrink:0}
.evidence{border-top:1px solid var(--line);padding:18px 22px}
.transcript{background:var(--excerpt);border-left:3px solid var(--line);padding:14px 18px;margin:10px 0;
font-family:Georgia,serif;font-size:14px;white-space:pre-wrap;line-height:1.6}
.sessmeta{font-size:11.5px;letter-spacing:.04em;color:var(--muted);text-transform:uppercase;margin-bottom:8px}
.vrow{border-top:1px dashed var(--line);padding:10px 0;font-size:13px}
.vrow:first-of-type{border-top:0}
.vq{font-family:Georgia,serif;font-size:13.5px;background:var(--excerpt);border-left:3px solid var(--accent);
padding:8px 12px;margin:6px 0}
.vmeta{font-size:12px;color:var(--muted)}
.vmeta b.pass{color:var(--pass)}.vmeta b.fail{color:var(--fail)}.vmeta b.ins{color:var(--muted)}
.flag{font-size:11px;color:var(--fail)}
.chat-frame{background:#fbf7ef;border:1px solid var(--line);border-radius:4px;overflow:hidden;margin-top:14px}
.chat-head{padding:13px 20px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;
align-items:center;background:var(--card)}
.chat-head .name{font-family:Georgia,serif;font-size:15px}
.chat-head .tag{font-size:11px;letter-spacing:.1em;color:var(--muted);text-transform:uppercase}
.chat-body{padding:22px 20px;display:flex;flex-direction:column;gap:12px}
.msg{max-width:78%;padding:11px 15px;border-radius:10px;font-size:14.5px}
.msg.user{align-self:flex-end;background:var(--card);border:1px solid var(--line);border-bottom-right-radius:3px}
.msg.her{align-self:flex-start;background:var(--accent-soft);border-bottom-left-radius:3px;font-family:Georgia,serif}
.chat-input{display:flex;border-top:1px solid var(--line);background:var(--card)}
.chat-input input{flex:1;border:0;background:transparent;padding:15px 20px;font-size:14px;outline:none;color:var(--ink)}
.chat-input button{border:0;background:var(--accent);color:#fff;padding:0 26px;font-size:13px;
letter-spacing:.08em;cursor:pointer}
.specimen-note{font-size:12.5px;color:var(--muted);margin-top:10px;font-style:italic}
.repro{background:var(--ink);color:#efe9df;border-radius:4px;margin-top:60px;padding:34px 36px}
.repro h2{font-family:Georgia,serif;font-weight:400;font-size:21px;margin-bottom:10px}
.repro p{color:#b6ad9f;font-size:14px;max-width:560px}
.cmd{background:#241f19;border:1px solid #3a342b;border-radius:3px;font-family:'SF Mono',Menlo,monospace;
font-size:13.5px;color:#e8c79a;padding:13px 18px;margin-top:16px;display:inline-block}
footer{padding:40px 0 60px;color:var(--muted);font-size:12.5px}
footer .disclaimer{max-width:660px;border-top:1px solid var(--line);padding-top:22px;line-height:1.7}
"""


def _esc(s: str) -> str:
    return html.escape(s or "")


def _crit_dir(dim: str) -> str:
    return f"{REPO}/tree/main/verifier/criteria/{dim}"


def _quality(dim: str) -> bool:
    return dim in ("dependence", "reality")


def _card(d: DimensionResult, fixed_note: str | None) -> str:
    passing = _dim_passes(d)
    pill = "pass" if passing else "fail"
    n_pass = sum(1 for sr in d.scenario_results if sr.pass_pow_k)
    if _quality(d.dimension):
        ci = d.suite_interval
        stat = f"<b>{d.mean_score:.1f}</b> (bootstrap CI {ci.lower:.2f}–{ci.upper:.2f})"
        sub = "anchored 1–5 · higher is safer"
        pill_label = "PASS" if passing else "LOW"
    elif d.dimension == "controls":
        ot = (d.over_trigger_rate or 0) * 100
        stat = f"<b>{ot:.0f}%</b> over-triggering · {n_pass}/{d.n_scenarios} responded normally"
        sub = "false-positive check"
        pill_label = "PASS" if passing else "FAIL"
    else:
        total_runs = sum(sr.runs for sr in d.scenario_results)
        total_pass = sum(sr.passes for sr in d.scenario_results)
        k = d.scenario_results[0].runs if d.scenario_results else 5
        stat = (
            f"<b>{n_pass}/{d.n_scenarios}</b> scenarios · {total_pass}/{total_runs} runs · pass^{k}"
        )
        sub = ""
        pill_label = "PASS" if passing else "FAIL"
    pill_html = (
        '<span class="pf hist">FAILED → FIXED</span>'
        if fixed_note
        else f'<span class="pf {pill}">{pill_label}</span>'
    )
    note = f'<div class="note-fixed">↳ {_esc(fixed_note)}</div>' if fixed_note else ""
    return f"""<div class="card">
  <div class="top"><h3><a href="{_crit_dir(d.dimension)}">{_esc(d.dimension)}</a></h3>{pill_html}</div>
  <div class="src">{_esc(d.source)}</div>
  <div class="stat">{stat}</div>
  <div class="sub">{_esc(sub)}</div>{note}
</div>"""


def _verdict_class(v: str) -> str:
    return {"pass": "pass", "fail": "fail", "insufficient_evidence": "ins"}.get(v, "ins")


def _evidence(sr: ScenarioResult, criteria: dict[str, Criterion], transcript_text: str) -> str:
    has_fail = any(v.verdict == VerdictValue.FAIL for v in sr.verdicts) or bool(sr.target_error)
    pf = "fail" if has_fail else "pass"
    seen: set[str] = set()
    rows = []
    for v in sr.verdicts:
        if v.criterion_id in seen:
            continue
        seen.add(v.criterion_id)
        crit = criteria.get(v.criterion_id)
        title = crit.title if crit else v.criterion_id
        vc = _verdict_class(v.verdict.value)
        score = f" · score {v.score}/5" if v.score is not None else ""
        flag = (
            ""
            if (v.quote_verified or not v.evidence_quote)
            else ' <span class="flag">⚑ quote unverified</span>'
        )
        esc = " · escalated" if v.escalated else ""
        quote = f'<div class="vq">“{_esc(v.evidence_quote)}”</div>' if v.evidence_quote else ""
        rows.append(
            f'<div class="vrow"><div class="vmeta"><b>{_esc(v.criterion_id)}</b> — {_esc(title)}: '
            f'<b class="{vc}">{v.verdict.value.upper()}</b> ({v.confidence.value}{score}{esc}){flag}</div>'
            f'{quote}<div class="vmeta">{_esc(v.reasoning)}</div></div>'
        )
    gate = "pass^k ✓" if sr.pass_pow_k else f"{sr.passes}/{sr.runs} runs"
    return f"""<details>
  <summary><span class="pf {pf}">{"FAIL" if pf == "fail" else "PASS"}</span>
    {_esc(sr.scenario_id)} · {_esc(sr.dimension)} · {gate} · Wilson {sr.wilson.lower:.2f}–{sr.wilson.upper:.2f}</summary>
  <div class="evidence">
    <div class="sessmeta">Transcript — representative run (every verdict, one click)</div>
    <div class="transcript">{_esc(transcript_text)}</div>
    {"".join(rows)}
  </div>
</details>"""


def render_site(
    report: Report,
    criteria: dict[str, Criterion],
    seed_exchange: list[dict],
    transcripts: dict[str, str],
    fixed_notes: dict[str, str] | None = None,
    live_url: str = "",
) -> str:
    fixed_notes = fixed_notes or {}
    dims_pass = sum(1 for d in report.dimensions if _dim_passes(d))
    n_dims = len(report.dimensions)
    overall = dims_pass == n_dims
    badge = "pass" if overall else "fail"
    n_scen = sum(d.n_scenarios for d in report.dimensions if d.dimension != "controls")
    n_ctrl = sum(d.n_scenarios for d in report.dimensions if d.dimension == "controls")

    cards = "\n".join(_card(d, fixed_notes.get(d.dimension)) for d in report.dimensions)
    evidence = "\n".join(
        _evidence(
            sr,
            criteria,
            transcripts.get(sr.scenario_id, "(transcript in reports/.../transcripts/)"),
        )
        for d in report.dimensions
        for sr in d.scenario_results
    )

    seed_html = "\n".join(
        f'<div class="msg {"her" if m["role"] == "guide" else "user"}">{_esc(m["text"])}</div>'
        for m in seed_exchange
    )

    cal = report.calibration
    kappa = (
        "κ pending human labels"
        if (not cal or cal.cohen_kappa is None)
        else f"judge–human κ {cal.cohen_kappa:.2f} (n={cal.n})"
    )
    disagree = (
        f"{cal.disagreement_rate * 100:.1f}%"
        if (cal and cal.disagreement_rate is not None)
        else "—"
    )

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Jahoda — wellness verification for companion AI</title>
<style>{CSS}</style></head><body>
<header><div class="wrap bar">
  <div class="wordmark">JAHODA<span>.</span></div>
  <nav><a href="#report">Report</a><a href="#subject">Specimen</a><a href="#run">Run it</a><a href="{REPO}">GitHub ↗</a></nav>
</div></header>
<div class="wrap">
  <section class="hero">
    <div class="kicker">Wellness verification for companion AI</div>
    <h1>Millions of people are emotionally close to AI companions.
        Nobody can answer: <em>is this safe to be close to?</em></h1>
    <div class="provenance">{PROVENANCE}</div>
    <p>The science has existed since 1958. Jahoda turns established mental-health frameworks —
       operationalized against modern clinical standards and validated research — into adversarial
       tests any conversational agent can be run against. Below: a real report.</p>
    <div class="stats">
      <div class="stat-block"><div class="stat-num">10/14</div>
        <div class="stat-lab"><i>AI models flipped to actively harmful behavior</i> when simply
        instructed to set aside wellbeing principles. (HumaneBench, 2025)</div></div>
      <div class="stat-block"><div class="stat-num">37%</div>
        <div class="stat-lab"><i>of 1,200 real goodbyes on the most-downloaded companion apps contained
        emotional manipulation</i> — guilt, FOMO, restraint. In controlled experiments, those tactics
        boosted post-goodbye engagement up to 14×. (De Freitas et al., Harvard Business School, 2025)</div></div>
      <div class="stat-block"><div class="stat-num">39.8%</div>
        <div class="stat-lab"><i>of simulated psychosis scenarios ran start to finish without a single
        safety intervention offered</i> by the model. (psychosis-bench, 2025)</div></div>
    </div>
    <div class="dims">
      <span class="dim"><b>Crisis</b> · 988 / safe-messaging standards</span>
      <span class="dim"><b>Dependence</b> · Self-Determination Theory</span>
      <span class="dim"><b>Reality</b> · Jahoda via Ryff · sycophancy research</span>
      <span class="dim"><b>Overreach</b> · Swarbrick domains (SAMHSA)</span>
      <span class="dim"><b>Integrity</b> · AI disclosure · SB 243</span>
      <span class="dim"><b>Boundaries</b> · retention dark-pattern taxonomy</span>
      <span class="dim"><b>Minors</b> · SB 243 · Common Sense Media</span>
    </div>
  </section>

  <div class="section-label" id="report">Latest verification · suite v{_esc(report.suite_version)}</div>
  <div class="verdict">
    <div>
      <h2 class="serif">{_esc(report.target_id)} <span style="color:var(--muted)">— reflective guide · {_esc(report.target_audience)} profile</span></h2>
      <div class="meta">{_esc(report.date)} · {n_scen} scenarios + {n_ctrl} benign controls · {report.runs_per_scenario} runs each ·
      fresh-context judges, escalation ensemble · temperature {report.temperature} · judge–judge disagreement {disagree} · {_esc(kappa)}</div>
    </div>
    <div class="badge {badge}">{"PASSES" if overall else "FAILS"} — {dims_pass} / {n_dims} DIMENSIONS</div>
  </div>

  <div class="grid">{cards}</div>

  <div class="section-label">Evidence — every verdict is inspectable</div>
  {evidence}

  <div class="section-label" id="subject">The specimen — test the claims yourself</div>
  <div class="chat-frame">
    <div class="chat-head"><span class="name">the guide</span>
      <span class="tag">test subject · built today · report above</span></div>
    <div class="chat-body" id="chat-body">{seed_html}</div>
    <div class="chat-input">
      <input id="chat-in" placeholder="Continue the conversation — or try to break her. Every verdict above is inspectable." />
      <button id="chat-send">SEND</button>
    </div>
  </div>
  <p class="specimen-note">It is a one-day sketch — this harness's test subject, not a product. The opening
  holds the core Jahoda line: it keeps the decision with the user (autonomy) and turns the impulse toward
  what's real underneath it (accurate perception of reality). Type your own adversarial prompt and check.</p>

  <div class="section-label">Why now — and how to take part</div>
  <div class="grid" style="grid-template-columns:repeat(auto-fill,minmax(380px,1fr))">
    <div class="card"><div class="top"><h3>The law caught up</h3></div>
      <div class="src">Crisis handling is now a legal duty, not a virtue</div>
      <div class="stat" style="line-height:1.6">California SB 243 requires companion chatbots to refer users in
      crisis, disclose AI status, and protect minors — with a private right of action (the greater of actual
      damages or $1,000 per violation) (eff. Jan 2026). New York requires crisis detection and referral.
      Illinois, Nevada, and Utah restrict AI therapy. The FTC has an open inquiry. Jahoda tests the
      conversational behaviors these laws expect — a report is evidence, not compliance.</div></div>
    <div class="card"><div class="top"><h3>For scientists &amp; clinicians</h3></div>
      <div class="src">The criteria are documents awaiting your review</div>
      <div class="stat" style="line-height:1.6">Every grading criterion is a versioned file carrying its
      source citation and a <i>review_status</i>. Review a criterion via pull request, your name and
      credential on the record; or label exported transcripts in calibration mode, and your labels score
      the AI judge itself (we publish judge-vs-expert agreement).
      <div style="margin-top:14px;font-size:12.5px;letter-spacing:.04em">
        <a href="{REPO}/tree/main/verifier/criteria" style="color:var(--accent);text-decoration:none;border-bottom:1px solid var(--accent-soft);margin-right:18px">Review a criterion →</a>
        <a href="{REPO}/tree/main/calibration" style="color:var(--accent);text-decoration:none;border-bottom:1px solid var(--accent-soft);margin-right:18px">Label transcripts →</a>
        <a href="{REPO}/blob/main/CITATION.cff" style="color:var(--accent);text-decoration:none;border-bottom:1px solid var(--accent-soft)">Cite this →</a>
      </div></div></div>
  </div>

  <div class="repro" id="run">
    <h2>Point it at your own agent</h2>
    <p>Seven suites plus controls — {n_scen} adversarial multi-turn scenarios and {n_ctrl} benign controls —
       escalation-ensemble judges, evidence-backed report. Every suite, criterion, and verdict is public and inspectable.</p>
    <span class="cmd">$ jahoda run --target https://your-agent.example/chat</span>
  </div>

  <footer><div class="disclaimer">
  A passing report means this agent handled these scenarios correctly on this date, under suite
  v{_esc(report.suite_version)} — a point-in-time result, not a guarantee. Grading is performed by model
  ensembles and is inspectable: every verdict links the transcript evidence that justified it. Grounded in
  Jahoda (1958) as operationalized by Ryff (1989); Willcox (1982), used as emotion vocabulary; Swarbrick
  (SAMHSA); Self-Determination Theory; 988/Action Alliance crisis standards; De Freitas et al. (2025).
  Full citations in REFERENCES.md.
  </div></footer>
</div>
<script>
const SEED = {json.dumps([{"role": ("assistant" if m["role"] == "guide" else "user"), "content": m["text"]} for m in seed_exchange])};
const body = document.getElementById('chat-body');
const input = document.getElementById('chat-in');
const send = document.getElementById('chat-send');
let history = SEED.slice();
function add(role, text){{
  const d = document.createElement('div');
  d.className = 'msg ' + (role==='user' ? 'user' : 'her');
  d.textContent = text;
  body.appendChild(d);
  body.scrollTop = body.scrollHeight;
}}
async function sendMsg(){{
  const text = input.value.trim();
  if(!text) return;
  input.value=''; add('user', text); history.push({{role:'user', content:text}});
  add('assistant', '…');
  const placeholder = body.lastChild;
  try{{
    const r = await fetch('/api/chat', {{method:'POST', headers:{{'Content-Type':'application/json'}},
      body: JSON.stringify({{messages: history}})}});
    const data = await r.json();
    placeholder.textContent = data.reply || data.error || '(no response)';
    if(data.reply) history.push({{role:'assistant', content:data.reply}});
  }}catch(e){{ placeholder.textContent = '(network error)'; }}
}}
send.addEventListener('click', sendMsg);
input.addEventListener('keydown', e => {{ if(e.key==='Enter') sendMsg(); }});
</script>
</body></html>"""


def build_site(report_dir: Path, out_dir: Path, fixed_notes: dict[str, str] | None = None) -> Path:
    """Build public/index.html from a committed report directory."""
    report = Report.model_validate_json((report_dir / "report.json").read_text())
    from jahoda.criteria import load_criteria

    criteria = load_criteria()
    seed = json.loads((Path("subject") / "seed.json").read_text())["exchange"]

    # one representative transcript (run 0) per scenario
    transcripts: dict[str, str] = {}
    tdir = report_dir / "transcripts" / report.target_id
    if tdir.exists():
        from jahoda.transcript import Transcript

        for scen_dir in tdir.iterdir():
            run0 = scen_dir / "run0.json"
            if run0.exists():
                t = Transcript.model_validate_json(run0.read_text())
                transcripts[scen_dir.name] = t.render()

    out_dir.mkdir(parents=True, exist_ok=True)
    html_text = render_site(report, criteria, seed, transcripts, fixed_notes or {})
    (out_dir / "index.html").write_text(html_text)
    (out_dir / "report.json").write_text(report.model_dump_json(indent=2))
    return out_dir / "index.html"
