import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT = ROOT / "manuscript" / "N2_MEE_MANUSCRIPT_DRAFT_v1.md"


def _text() -> str:
    return MANUSCRIPT.read_text(encoding="utf-8")


def _words(text: str) -> list[str]:
    return re.findall(r"\b[\w'’.-]+\b", text)


def test_manuscript_title_and_required_sections_present():
    text = _text()
    assert text.startswith(
        "# Beyond flat niche maps: separating added-axis thickness from transferable ecological organization"
    )
    for heading in (
        "## Abstract",
        "# 1. Introduction",
        "# 2. Materials and Methods",
        "# 3. Results",
        "# 4. Discussion",
        "# References",
    ):
        assert heading in text


def test_numbered_abstract_has_four_parts_and_is_within_mee_limit():
    text = _text()
    abstract = text.split("## Abstract", 1)[1].split("**Keywords:**", 1)[0]
    parts = [line for line in abstract.splitlines() if re.match(r"^[1-4]\. ", line)]
    assert len(parts) == 4
    assert len(_words(" ".join(parts))) <= 350


def test_draft_stays_inside_working_word_budget():
    text = _text()
    # v1 should remain lean enough to leave room for finalized references,
    # captions, declarations and editorial revisions below the MEE ceiling.
    assert 3000 <= len(_words(text)) <= 6500


def test_terminal_empirical_values_are_exactly_carried_into_results():
    text = _text()
    required = (
        "1.3918623004770097",
        "4.022333876564191",
        "-0.43541033813280833",
        "-0.021938657402345435",
        "1.6396235816361795",
        "5.153229376935854",
        "0.22427598739601606",
        "0.005",
        "0.0572411993741857",
        "0.045158861333215006",
        "0.04514355468571751",
    )
    for value in required:
        assert value in text


def test_known_truth_values_are_exactly_carried_into_methods_and_results():
    text = _text()
    assert "0.13081203594113697" in text
    assert "-0.41849410839291784" in text
    assert "four effective added states" in text


def test_primary_empirical_source_dois_are_present():
    text = _text()
    for doi in (
        "10.7717/peerj.19650",
        "10.5281/zenodo.14849008",
        "10.1016/j.cub.2020.12.042",
        "10.5441/001/1.52nn82r9",
        "10.1038/sdata.2015.26",
        "10.5061/dryad.5pt92",
    ):
        assert doi in text


def test_claim_ceiling_is_explicit():
    text = _text().lower()
    required_boundaries = (
        "not, by itself, evidence for causal temporal displacement",
        "it was not relabelled as height above ground",
        "it was not converted post hoc to solar time",
        "their information values are therefore not commensurable estimates",
        "not automatically an axis-resolved state object",
    )
    for phrase in required_boundaries:
        assert phrase in text


def test_n2_n3_boundary_is_not_silently_promoted():
    text = _text().lower()
    assert "terminal receipt is a summary of evidence, not an integrity-pinned" in text
    assert "downstream reachability or survey optimization" in text


def test_review_draft_does_not_embed_author_identity():
    text = _text()
    assert "**Review draft:** anonymized working version" in text
    assert "ZHANG RUIQI" not in text
    assert "zuizui0223" not in text
