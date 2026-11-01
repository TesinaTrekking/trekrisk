# AGENTS.md

Project: probabilistic analysis of the weather at 5 trekking zones in Córdoba, shown in a single Streamlit dashboard (the *tablero*, see `GLOSSARY.md` and `docs/adr/0001-tablero-unico.md`). Final integrative project for Statistics and Applied Probability (ISAU / UPC, Villa Carlos Paz).

**The full specification is in `SPEC.md`. Read it before writing code and follow it.** If something in the spec is ambiguous or contradictory, ask before deciding.

## Commands

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py             # web interface
pytest                           # tests for core/
```

## Structure

```
app.py                  # Streamlit entry point: sidebar and the single dashboard
interfaz/               # UI support code: formatting, styles, filters, cards
core/                   # pure logic, does NOT import streamlit
  config.py  api.py  datos.py  eventos.py
  probabilidad.py  simulacion.py  interpretacion.py
data/                   # one CSV per zone, versioned in git
tests/
.streamlit/config.toml  # visual theme
```

## Rules

- **Real data only.** Never generate, invent, or simulate weather data. The only permitted "draw" is resampling with replacement of real days (see `SPEC.md`, section 7).
- **`core/` does not import Streamlit.** The interface only calls functions in `core/` and displays what they return.
- **Every number shown includes its case counts** (favorable and total). If there are fewer than 30 cases, show a warning.
- **Interpretive text is generated in `core/interpretacion.py`**, not in the screens.
- **Thresholds come from the sidebar**; never hardcode them in functions. The seed is the constant `SEMILLA` in `core/config.py` and is not shown in the UI.
- **The UI never downloads data.** The CSVs in `data/` are archive data; `core/api.py` is kept only as a record of their provenance.
- **Code:** function, variable, and column names in Spanish without accents (`probabilidad_condicional`, `fecha`); docstrings and comments in Spanish; type hints on all public functions; small, pure functions.
- **Interface** in Spanish (Argentina): decimal comma, percentages as `12,3 %`.
- **No dependencies beyond** `requests`, `pandas`, `numpy`, `streamlit`, `plotly`, `pytest`. If you need another, ask.
- **Do not add features that are not in the spec** (no regression, no inference, no forecasting, no database, no login, no console/CLI).
- Before implementing the download, **verify the exact endpoint and parameter names in the Open-Meteo documentation**.
- There is no multipage navigation: one dashboard only. Verify that the installed Streamlit version supports any widget you use (`st.pills`, `st.fragment`).

## Workflow

1. Work **one phase at a time** (see `SPEC.md`, section 12) and do not start the next until the current one meets its done criterion.
2. At the end of each phase: run `pytest` and make a commit following the "Commits" convention.
3. If a test fails, fix the code, not the test, unless the test's expected value is miscalculated. In that case, explain why.
4. At the end of each phase, summarize in a few lines what you did and what decisions you made.

## Commits

Format: `type: description`, single line, in Spanish, lowercase, no trailing period.

| type | when to use |
| --- | --- |
| `feat` | new functionality |
| `fix` | bug fix |
| `refactor` | internal change that does not alter behavior |
| `chore` | auxiliary tasks: dependencies, configuration, data, README |

Examples:

```
feat: agrega descarga de clima desde open-meteo
fix: corrige el cálculo de lluvia_ayer en el primer día de cada zona
refactor: separa la validación de datos en funciones más chicas
chore: agrega los csv de las 5 zonas
```

Rules:

- **No co-authorship or Claude signatures** in commits. No `Co-Authored-By` lines, no "Generated with Claude Code", no similar mentions, in neither title nor body.
- No body and no emojis, unless explicitly requested.
- One commit per logical change; do not mix new functionality with refactors.

## Agent skills

### Issue tracker

Issues and specs live as markdown files in `.scratch/`. See `docs/agents/issue-tracker.md`.

### Triage labels

Default five-role vocabulary (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`), recorded in each issue's `Status:` line. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: one `GLOSSARY.md` + `docs/adr/` at the repo root. See `docs/agents/domain.md`.
