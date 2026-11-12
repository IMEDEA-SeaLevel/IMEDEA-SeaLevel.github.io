# IMEDEA Sea Level — website

Source of <https://imedea-sealevel.github.io>. Three pages: **Repositories** (home),
**Projects** and **Publications**. Everything is generated from the files in `data/`.

## Everyday edits

| I want to…                         | Edit                                 |
|------------------------------------|--------------------------------------|
| add or change a project            | `data/projects.yml`                  |
| add a person whose papers are scanned | `data/collaborators.yml` (name + ORCID) |
| add a paper the tool missed, or hide one | `data/publications_overrides.yml` |
| change the site title or intro text | `data/site.yml`                     |

Each file starts with a comment explaining its fields. Edit it on GitHub (pencil icon),
commit, and the site rebuilds by itself in a couple of minutes.

`data/publications.yml` and `data/repositories.yml` are generated — do not edit them.

## How the automatic parts work

- **Repositories**: `scripts/update_repositories.py` lists the *public* repositories of the
  organisation. Private repositories are never shown.
- **Publications**: `scripts/update_publications.py` downloads the publication record of every
  collaborator from OpenAlex (by ORCID) and keeps the papers whose funding information contains a
  grant reference from `data/projects.yml` (OpenAlex first, Crossref as a second source). It also
  runs an OpenAlex full-text search for each grant reference, which catches papers that only mention
  the grant in the acknowledgements. Coverage is good but not guaranteed: if a paper is missing, add
  it by DOI in `data/publications_overrides.yml`.
- A GitHub Action (`.github/workflows/site.yml`) runs both scripts, commits any change in `data/`,
  builds the site and deploys it to GitHub Pages: on every push, every Monday, and on demand
  (Actions → *Update data, build and deploy* → *Run workflow*).

## Things to know

- GitHub Pages must be set to **Source: GitHub Actions** (Settings → Pages).
- Optional but recommended: a free OpenAlex API key stored as the repository secret
  `OPENALEX_API_KEY` (Settings → Secrets and variables → Actions). Without it the publications
  update may occasionally be rate-limited; the site is then built from the last saved data.
- GitHub pauses scheduled workflows after 60 days without any activity in the repository. If the
  weekly update stops, re-enable it in the Actions tab (or just run it by hand).

## Run locally

```bash
pip install -r requirements.txt
python scripts/update_repositories.py
python scripts/update_publications.py --verbose
python scripts/build.py
python -m http.server -d _site 8000     # http://localhost:8000
```
