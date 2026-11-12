#!/usr/bin/env python3
"""Write data/publications.yml.

For every collaborator in data/collaborators.yml the script downloads their
publication record from OpenAlex (by ORCID) and keeps the papers whose funding
information contains one of the grant references in data/projects.yml.
Crossref is used as a second source of funding information, and the OpenAlex
full-text search catches papers that only cite the grant in the acknowledgements. Manual additions
and removals are read from data/publications_overrides.yml.

Usage:  python scripts/update_publications.py [--verbose]
Optional environment variable: OPENALEX_API_KEY
"""
import re
import sys
import time
import urllib.parse

from util import dump, env, get_json, load, norm, norm_doi, norm_orcid

VERBOSE = "--verbose" in sys.argv
OPENALEX = "https://api.openalex.org/works"
CROSSREF = "https://api.crossref.org/works"


def oa_url(params):
    key = env("OPENALEX_API_KEY")
    if key:
        params = dict(params, api_key=key)
    return OPENALEX + "?" + urllib.parse.urlencode(params)


def works_of(orcid, since):
    cursor, out = "*", []
    while cursor:
        d = get_json(
            oa_url(
                {
                    "filter": f"author.orcid:{orcid},from_publication_date:{since}",
                    "per-page": 200,
                    "cursor": cursor,
                }
            )
        )
        out += d.get("results", [])
        cursor = d.get("meta", {}).get("next_cursor") if d.get("results") else None
    return out


def work_by_doi(doi):
    d = get_json(oa_url({"filter": "doi:" + doi, "per-page": 1}))
    res = (d or {}).get("results") or []
    return res[0] if res else None


def award_text(work):
    parts = []
    for a in work.get("awards") or work.get("grants") or []:
        parts += [a.get("funder_award_id"), a.get("award_id"), a.get("display_name")]
    return norm(" ".join(p for p in parts if p))


def crossref_award_text(doi):
    d = get_json(CROSSREF + "/" + urllib.parse.quote(doi, safe="/"))
    if not d:
        return ""
    parts = []
    for f in d.get("message", {}).get("funder", []) or []:
        parts += f.get("award") or []
    return norm(" ".join(parts))


def match(text, projects):
    return [p["id"] for p in projects if any(g and g in text for g in p["_grants"])]


def title_key(t):
    return re.sub(r"[^a-z0-9]", "", (t or "").lower())


def record(work, project_ids, collab_orcids):
    loc = work.get("primary_location") or {}
    src = loc.get("source") or {}
    authors = []
    for a in work.get("authorships") or []:
        au = a.get("author") or {}
        entry = {"name": au.get("display_name") or a.get("raw_author_name") or ""}
        if norm_orcid(au.get("orcid")) in collab_orcids:
            entry["member"] = True
        authors.append(entry)
    biblio = work.get("biblio") or {}
    return {
        "title": (work.get("title") or work.get("display_name") or "").strip(),
        "authors": authors,
        "venue": src.get("display_name") or loc.get("raw_source_name") or "",
        "year": work.get("publication_year"),
        "date": work.get("publication_date") or "",
        "volume": biblio.get("volume") or "",
        "pages": "–".join(dict.fromkeys(x for x in [biblio.get("first_page"), biblio.get("last_page")] if x)),
        "doi": norm_doi(work.get("doi")),
        "url": work.get("doi") or loc.get("landing_page_url") or work.get("id"),
        "type": work.get("type") or "",
        "open_access": bool((work.get("open_access") or {}).get("is_oa")),
        "citations": int(work.get("cited_by_count") or 0),
        "projects": sorted(project_ids),
    }


def main():
    projects = load("projects.yml") or []
    collaborators = load("collaborators.yml") or []
    overrides = load("publications_overrides.yml") or {}
    for p in projects:
        p["_grants"] = [norm(g) for g in (p.get("grants") or []) if norm(g)]
    known_ids = {p["id"] for p in projects}
    collab_orcids = {norm_orcid(c.get("orcid")) for c in collaborators} - {""}

    starts = [int(str(p.get("start"))[:4]) for p in projects if p.get("start")]
    since = f"{min(starts) if starts else 2000}-01-01"

    # 1. All works of every collaborator (deduplicated by OpenAlex id).
    works = {}
    for c in collaborators:
        orcid = norm_orcid(c.get("orcid"))
        if not orcid:
            print(f"WARNING: no valid ORCID for {c.get('name')}, skipped")
            continue
        ws = works_of(orcid, since)
        print(f"{c.get('name')}: {len(ws)} works since {since}")
        for w in ws:
            works[w["id"]] = w

    # 2. Match grant references: OpenAlex first, Crossref as second source.
    found = {}
    for w in works.values():
        ids = set(match(award_text(w), projects))
        doi = norm_doi(w.get("doi"))
        if doi and len(ids) < len(projects):
            try:
                ids |= set(match(crossref_award_text(doi), projects))
            except Exception as e:  # Crossref is only a complement
                if VERBOSE:
                    print("  crossref failed for", doi, e)
            time.sleep(0.05)
        if ids:
            found[w["id"]] = (w, ids)
            if VERBOSE:
                print("  +", sorted(ids), doi or w["id"], "|", (w.get("title") or "")[:60])

    # 2b. Full-text search: papers that cite the grant in the acknowledgements
    #     text even when the journal registered no funding metadata.
    orcids = sorted(collab_orcids)
    for p in projects:
        for grant in p.get("grants") or []:
            for i in range(0, len(orcids), 40):
                flt = f'fulltext.search:"{grant}",author.orcid:{"|".join(orcids[i:i + 40])},from_publication_date:{since}'
                try:
                    d = get_json(oa_url({"filter": flt, "per-page": 200}))
                except Exception as e:
                    print(f"WARNING: full-text search failed for {grant}: {e}")
                    continue
                for w in (d or {}).get("results", []):
                    if w["id"] not in found:
                        found[w["id"]] = (w, set())
                        if VERBOSE:
                            print("  + full text", p["id"], norm_doi(w.get("doi")), "|", (w.get("title") or "")[:60])
                    found[w["id"]][1].add(p["id"])

    pubs = [record(w, ids, collab_orcids) for w, ids in found.values()]

    # 3. Manual additions.
    for inc in overrides.get("include") or []:
        doi = norm_doi(inc.get("doi") if isinstance(inc, dict) else inc)
        ids = set(inc.get("projects") or []) if isinstance(inc, dict) else set()
        unknown = ids - known_ids
        if unknown:
            print(f"WARNING: unknown project id(s) {sorted(unknown)} for {doi}")
        existing = next((p for p in pubs if p["doi"] == doi), None)
        if existing:
            existing["projects"] = sorted(set(existing["projects"]) | ids)
            continue
        w = work_by_doi(doi)
        if not w:
            print(f"WARNING: DOI not found in OpenAlex, skipped: {doi}")
            continue
        pubs.append(record(w, ids, collab_orcids))

    # 4. Manual removals.
    excluded = {norm_doi(d) for d in overrides.get("exclude") or []}
    pubs = [p for p in pubs if p["doi"] not in excluded]

    # 5. Remove duplicates (same DOI, or preprint + published version).
    best = {}
    for p in pubs:
        key = p["doi"] or title_key(p["title"])
        tkey = title_key(p["title"])
        for k in (key, tkey):
            cur = best.get(k)
            if cur is None:
                best[k] = p
            elif cur is not p:
                keep, drop = (cur, p) if (cur["type"] != "preprint" or p["type"] == "preprint") else (p, cur)
                keep["projects"] = sorted(set(keep["projects"]) | set(drop["projects"]))
                for kk, vv in list(best.items()):
                    if vv is drop:
                        best[kk] = keep
                best[k] = keep
    unique = []
    for p in best.values():
        if not any(p is u for u in unique):
            unique.append(p)

    unique.sort(key=lambda p: (p["date"] or str(p["year"] or ""), p["title"]), reverse=True)
    changed = dump(
        "publications.yml",
        unique,
        "Generated by scripts/update_publications.py — do not edit by hand.\n"
        "# To add or hide a paper use data/publications_overrides.yml.",
    )
    per = {p["id"]: sum(1 for u in unique if p["id"] in u["projects"]) for p in projects}
    print(f"{len(unique)} publications ({'updated' if changed else 'no changes'}):", per)


if __name__ == "__main__":
    sys.exit(main())
