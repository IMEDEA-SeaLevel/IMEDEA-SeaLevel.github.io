#!/usr/bin/env python3
"""Build the static site into _site/ from data/, templates/ and static/."""
import datetime
import itertools
import shutil

from jinja2 import Environment, FileSystemLoader, select_autoescape

from util import ROOT, load

OUT = ROOT / "_site"
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
MAX_AUTHORS = 10


def ym(value, end=False):
    """'2026-09' / 2022 / date -> (year, month); month defaults to Jan (or Dec for an end)."""
    if value in (None, ""):
        return None
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.year, value.month
    parts = str(value).split("-")
    return int(parts[0]), int(parts[1]) if len(parts) > 1 else (12 if end else 1)


def fmt(value):
    if value in (None, ""):
        return ""
    s = str(value)
    if len(s) <= 4:
        return s
    y, m = ym(value)
    return f"{MONTHS[m - 1]} {y}"


def main():
    today = datetime.date.today()
    site = load("site.yml")
    projects = load("projects.yml") or []
    publications = load("publications.yml") or []
    repositories = load("repositories.yml") or []

    now = (today.year, today.month)
    for p in projects:
        start, end = ym(p.get("start")), ym(p.get("end"), end=True)
        if start and start > now:
            p["status"] = "Upcoming"
        elif end and end < now:
            p["status"] = "Completed"
        else:
            p["status"] = "Ongoing"
        p["period"] = " – ".join(x for x in [fmt(p.get("start")), fmt(p.get("end"))] if x)
        mine = [pub for pub in publications if p["id"] in (pub.get("projects") or [])]
        p["pubs"] = mine
        p["n_pubs"] = len(mine)
        p["citations"] = sum(pub.get("citations") or 0 for pub in mine)
        p["n_oa"] = sum(1 for pub in mine if pub.get("open_access"))
        p["n_venues"] = len({pub.get("venue") for pub in mine if pub.get("venue") and pub.get("type") != "preprint"})
        p["_sort"] = (p["status"] == "Completed", tuple(-x for x in (start or (0, 0))))
    projects.sort(key=lambda p: p["_sort"])

    for pub in publications:
        authors = pub.get("authors") or []
        if len(authors) > MAX_AUTHORS:
            # keep the first authors plus any group member further down the list
            shown = authors[: MAX_AUTHORS - 2] + [a for a in authors[MAX_AUTHORS - 2 :] if a.get("member")]
        else:
            shown = authors
        pub["shown_authors"] = shown
        pub["more_authors"] = len(authors) - len(shown)
    by_year = [
        (year, list(items))
        for year, items in itertools.groupby(publications, key=lambda p: p.get("year") or "n.d.")
    ]

    env = Environment(
        loader=FileSystemLoader(ROOT / "templates"),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    ctx = dict(
        site=site,
        projects=projects,
        publications=publications,
        repositories=repositories,
        by_year=by_year,
        acronyms={p["id"]: p["acronym"] for p in projects},
        total_citations=sum(pub.get("citations") or 0 for pub in publications),
        today=today.strftime("%-d %B %Y"),
    )
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copytree(ROOT / "static", OUT / "static")
    (OUT / ".nojekyll").write_text("")
    pages = [
        ("projects", "index.html"),
        ("publications", "publications.html"),
        ("repositories", "repositories.html"),
        ("", "404.html"),
    ]
    for page, tpl in pages:
        # the 404 page can be served from any path, so it needs absolute links
        root = "/" if tpl == "404.html" else "./"
        canonical = "" if tpl == "index.html" else tpl
        html = env.get_template(tpl).render(page=page, root=root, canonical=canonical, **ctx)
        (OUT / tpl).write_text(html, encoding="utf-8")
    print(f"Built {OUT} — {len(repositories)} repositories, {len(projects)} projects, {len(publications)} publications")


if __name__ == "__main__":
    main()
