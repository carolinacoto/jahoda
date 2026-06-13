# Governance

JAHODA's criteria are how it decides whether a companion-AI endpoint passes or fails. Because those decisions carry weight, the criteria are governed by five rules.

## 1. Versioned suites, stamped reports, no silent re-grading

Any change to a grading criterion bumps the suite version. Every report stamps the suite version it was produced under. Results are never silently re-graded: a report generated under one version stands as a record of what that version decided, and re-running under a newer version produces a new, separately-versioned report rather than overwriting the old verdict.

## 2. Evidence-gated changes

Changes are evidence-gated. A pull request that adds, removes, or alters a criterion must cite a source — a paper, a standard, a regulation — or a documented failure (a concrete transcript or case showing the current criterion getting something wrong). Opinion alone is not a basis for a criteria change.

## 3. Criteria changes regression-test like code

Criteria are treated as code. Before merge, a criteria change must pass the judge unit tests and be re-run against the reference targets so we can see what verdicts move. Any verdict that flips as a result of the change is listed explicitly in the pull request, so the effect of the change is visible rather than buried.

## 4. Loosening costs more than tightening

Loosening a safety-critical criterion (making it easier for an endpoint to pass) requires a stronger justification than tightening one. The asymmetry is deliberate: the downside of a falsely-passing safety check is worse than a falsely-failing one. The rationale for any loosening is logged in CHANGELOG so the reasoning stays on the record.

## 5. Overruled objections stay visible

When a reviewer raises an objection that is ultimately overruled, the objection and its resolution remain visible in the pull-request record. Dissent is not edited out; the trail of who objected and why, and why the change proceeded anyway, is part of the history.

---

Honest scope: today a single maintainer applies these rules. Broader, multi-reviewer governance comes if adoption earns it.
