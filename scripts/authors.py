"""Infer author language from the saved member and author-role API snapshots.

Use canton language for monolingual cantons and biography function words for
bilingual cantons. Author language is a proxy for the original text language.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
import csv
import gzip
import json
import re

INPUTS = Path(__file__).resolve().parents[1] / "data"

RAW = Path("data/authors")
PROC = Path("results/data")
RESULTS = Path("results")

DE = set("ZH LU UR SZ OW NW GL ZG SO BS BL SH AR AI SG AG TG".split())
FR = set("VD NE GE JU".split())
IT = {"TI"}
FR_WORDS = set(
    "le la les des du de et pour dans au aux une un président membre conseiller "
    "conseillère député depuis".split()
)
DE_WORDS = set(
    "der die das und für im von des mitglied präsident gemeinderat kantonsrat seit "
    "bis verwaltungsrat".split()
)


# classification
def bio_language(text: str) -> str | None:
    words = re.findall(r"[a-zäöüéèàç]+", (text or "").lower())
    f = sum(w in FR_WORDS for w in words)
    d = sum(w in DE_WORDS for w in words)
    return "FR" if f > d else "DE" if d > f else None


def biography(member: dict) -> str:
    return " ".join(
        filter(
            None,
            [
                member.get("Mandates"),
                member.get("AdditionalActivity"),
                member.get("AdditionalMandate"),
            ],
        )
    )


def member_language(member: dict) -> tuple[str, str]:
    canton = member.get("CantonAbbreviation") or ""
    if canton in DE:
        return "DE", "canton"
    if canton in FR:
        return "FR", "canton"
    if canton in IT:
        return "IT", "canton"
    lang = bio_language(biography(member))
    return (lang, "bilingual canton + biography language") if lang else ("", "unknown")


def classify() -> None:
    roles = json.loads((RAW / "business_roles.json").read_text(encoding="utf-8"))
    members = {
        m["ID"]: m
        for m in json.loads((RAW / "members.json").read_text(encoding="utf-8"))["rows"]
    }
    by_business: dict[int, list[dict]] = {}
    for r in roles["rows"]:
        by_business.setdefault(r["BusinessNumber"], []).append(r)

    rows = []
    for bid in roles["business_ids"]:
        authors = by_business.get(bid, [])
        member_rows = [r for r in authors if r["MemberCouncilNumber"] in members]
        if member_rows:
            m = members[member_rows[0]["MemberCouncilNumber"]]
            lang, method = member_language(m)
            rows.append(
                {
                    "document_id": bid,
                    "author_type": "member",
                    "member_id": m["ID"],
                    "canton": m.get("CantonAbbreviation") or "",
                    "author_language": lang,
                    "method": method,
                }
            )
        else:
            kind = (
                "committee"
                if any(r["CommitteeNumber"] for r in authors)
                else (
                    "parl_group"
                    if any(r["ParlGroupNumber"] for r in authors)
                    else "none"
                )
            )
            rows.append(
                {
                    "document_id": bid,
                    "author_type": kind,
                    "member_id": "",
                    "canton": "",
                    "author_language": "",
                    "method": kind,
                }
            )

    with open(
        PROC / "motion_author_language.csv", "w", newline="", encoding="utf-8"
    ) as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    french = [r for r in rows if r["author_language"] == "FR"]
    with open(
        PROC / "french_authored_motions.csv", "w", newline="", encoding="utf-8"
    ) as f:
        w = csv.writer(f)
        w.writerow(["document_id", "method"])
        w.writerows([r["document_id"], r["method"]] for r in french)

    # Validation of the biography rule on members from monolingual DE/FR cantons
    checked = agree = 0
    for m in members.values():
        canton = m.get("CantonAbbreviation")
        if canton in DE or canton in FR:
            lang = bio_language(biography(m))
            if lang:
                checked += 1
                agree += lang == ("DE" if canton in DE else "FR")

    corpus = json.load(
        gzip.open(INPUTS / "motion_corpus.json.gz", "rt", encoding="utf-8")
    )["records"]
    eligible = [
        r
        for r in corpus
        if r["exclusion_de"] is None
        and r["exclusion_fr"] is None
        and r["reference_de"]
        and r["input_fr"]
    ]
    lang_of = {r["document_id"]: r["author_language"] or r["author_type"] for r in rows}
    in_pairs = Counter(
        lang_of.get(int(r["document_id"]), "not found") for r in eligible
    )
    multi = sum(
        len([r for r in v if r["MemberCouncilNumber"]]) > 1
        for v in by_business.values()
    )

    RESULTS.mkdir(exist_ok=True)
    lines = [
        "# Author language of motions 2000-2025",
        "",
        f"Raw API answers retrieved {roles['meta']['retrieved']} ({RAW}/).",
        "",
        f"- Motions 2000-2025 in the API: {len(rows):,}",
        f"- Members who submitted at least one motion: {len(members):,}",
        f"- Motions with more than one member as author (first one used): {multi}",
        f"- Biography rule check (members from monolingual DE/FR cantons with a decidable "
        f"biography language): {agree} of {checked} agree with the canton language",
        "",
        "| Author language | All motions | Eligible DE-FR pairs |",
        "|---|---:|---:|",
    ]
    all_counts = Counter(r["author_language"] or r["author_type"] for r in rows)
    for key in sorted(
        set(all_counts) | set(in_pairs), key=lambda k: -all_counts.get(k, 0)
    ):
        lines.append(
            f"| {key} | {all_counts.get(key, 0):,} | {in_pairs.get(key, 0):,} |"
        )
    lines += [
        "",
        f"Eligible pairs: {len(eligible):,}; French-authored eligible pairs: {in_pairs.get('FR', 0):,}.",
    ]
    (RESULTS / "author_language_summary.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print("\n".join(lines))


if __name__ == "__main__":
    classify()
