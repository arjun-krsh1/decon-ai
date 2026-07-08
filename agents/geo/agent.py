"""
agent.py — the Market Visibility (GEO) Agent orchestrator.

    probe → extract → analyze → recommend

Call `run(GeoInput | dict)` and get back a GeoOutput matching the §5 contract.
Framework-agnostic and independently runnable; the Decon orchestrator and the
Streamlit dashboard both call this same function.

Failure isolation: one question's probe failing is recorded on that row and the
run continues (brief §8).
"""

from __future__ import annotations

from datetime import datetime

from .schemas import GeoInput, GeoOutput, PerQuestion
from .questions import build_questions
from .probes import resolve_probers
from .extract import extract
from .analyze import analyze, is_branded
from . import playbook
from . import storage


def run(geo_input, progress_cb=None, persist: bool = True) -> GeoOutput:
    """
    Run the full GEO analysis.

    geo_input : GeoInput or dict matching the input contract.
    progress_cb(done, total, message) : optional UI progress hook.
    persist   : write the run to disk for trend history.
    """
    gi = geo_input if isinstance(geo_input, GeoInput) else GeoInput.from_dict(geo_input)

    brands = [gi.brand, *gi.competitors]
    questions = gi.questions or build_questions(gi.brand, gi.category, gi.competitors)
    probers = resolve_probers(gi.models)
    models_used = [p.name for p in probers]

    rows: list[PerQuestion] = []
    total = len(questions) * len(probers)
    done = 0

    for q in questions:
        branded = is_branded(q, brands)
        for prober in probers:
            if progress_cb:
                progress_cb(done, total, f"[{prober.name}] {q[:60]}")
            try:
                pr = prober.probe(q)
                if pr.error:
                    rows.append(PerQuestion(q, branded, [], None, pr.sources or [],
                                            model=prober.name, error=pr.error))
                else:
                    parsed, _used_llm = extract(pr.answer, gi.brand, gi.competitors)
                    rows.append(PerQuestion(
                        question=q,
                        branded=branded,
                        rankedBrands=parsed["rankedBrands"],
                        position=parsed["position"],
                        sources=pr.sources,
                        model=prober.name,
                        answer=pr.answer,
                    ))
            except Exception as e:  # never let one probe kill the run
                rows.append(PerQuestion(q, branded, [], None, [],
                                        model=prober.name, error=str(e)))
            done += 1

    analysis = analyze(rows, gi.brand, gi.competitors)
    plan = playbook.generate(analysis, rows, gi.brand)

    output = GeoOutput(
        brand=gi.brand,
        category=gi.category,
        shortlistRate=analysis["shortlistRate"],
        longlistOnly=analysis["longlistOnly"],
        brandRanking=analysis["brandRanking"],
        sourceTypeMix=analysis["sourceTypeMix"],
        citedDomains=analysis["citedDomains"],
        perQuestion=rows,
        playbook=plan,
        unbrandedCount=analysis["unbrandedCount"],
        brandedCount=analysis["brandedCount"],
        modelsUsed=models_used,
        generatedAt=datetime.now().isoformat(timespec="seconds"),
    )

    if persist:
        try:
            storage.save_run(output.to_dict())
        except Exception as e:
            print(f"[geo] could not persist run: {e}")

    return output
