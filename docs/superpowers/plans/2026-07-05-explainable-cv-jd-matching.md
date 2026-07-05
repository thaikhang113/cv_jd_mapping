# Explainable CV-JD Matching Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build explainable matching: better experience parsing, skill evidence, match detail modal, and JD required/nice-to-have skill weighting, with repeated backend/frontend/production tests.

**Architecture:** Keep the existing FARM stack and MongoDB collections. Add small pure Python matching/parser helpers first, then store richer match fields in `matching_results`, then expose them in current REST APIs and React pages. Avoid new dependencies; use stdlib regex plus existing scikit-learn.

**Tech Stack:** FastAPI, Motor/MongoDB, Pydantic, pytest, React/Vite, Axios, Playwright CLI, Azure App Service, Vercel.

---

## File Map

- Modify: `backend/app/services/cv_parser.py` — improve `parse_cv_text()` and add `extract_experience_years()`.
- Modify: `backend/app/services/matching.py` — add skill evidence, required/nice skill weighting, score explanation fields.
- Modify: `backend/app/schemas/common.py` — extend `JobIn` with `nice_to_have_skills` and optionally keep `required_skills` backward compatible.
- Modify: `backend/app/routes/jobs.py` — normalize required/nice skills on create/update.
- Modify: `backend/app/routes/matches.py` — keep match output enriched and sorted.
- Modify: `backend/app/services/cv_worker.py` — ensure queued CV processing persists new match fields.
- Modify: `frontend/src/pages/CreateJob.jsx` — add separate required/nice-to-have skill inputs.
- Modify: `frontend/src/pages/Applications.jsx` — replace inline-only detail with a `View Analysis` modal.
- Modify: `frontend/src/pages/Ranking.jsx` — add `View Analysis` per candidate.
- Create: `frontend/src/components/MatchDetailModal.jsx` — reusable explainable match modal.
- Modify: `frontend/src/style.css` — modal and evidence styling.
- Modify: `backend/scripts/seed.py` — seed jobs include `nice_to_have_skills`.
- Test: `backend/tests/test_cv_parser.py` — parser/extraction tests.
- Test: `backend/tests/test_matching.py` — scoring/evidence tests.
- Optional Test: `frontend` via production Playwright smoke script in temp folder, not committed.

---

### Task 1: Baseline Safety Check

**Files:**
- Read: `backend/app/services/cv_parser.py`
- Read: `backend/app/services/matching.py`
- Read: `frontend/src/pages/Applications.jsx`
- Read: `frontend/src/pages/Ranking.jsx`

- [ ] **Step 1: Confirm clean branch**

Run:

```powershell
git status --short --branch
git branch -a
```

Expected:

```text
## main...origin/main
* main
  remotes/origin/HEAD -> origin/main
  remotes/origin/main
```

- [ ] **Step 2: Create feature branch**

Run:

```powershell
git switch -c feature/explainable-matching
```

Expected: branch switched to `feature/explainable-matching`.

- [ ] **Step 3: Run current focused checks**

Run:

```powershell
python -m py_compile backend\app\services\cv_parser.py backend\app\services\matching.py backend\app\routes\matches.py
npm run build --prefix frontend
```

Expected: both commands pass.

---

### Task 2: Experience Parser

**Files:**
- Modify: `backend/app/services/cv_parser.py`
- Create: `backend/tests/test_cv_parser.py`

- [ ] **Step 1: Write failing parser tests**

Create `backend/tests/test_cv_parser.py`:

```python
from app.services.cv_parser import extract_experience_years, parse_cv_text


def test_extract_experience_years_from_explicit_years():
    text = "Backend Developer with 4 years experience building APIs."
    assert extract_experience_years(text) == 4


def test_extract_experience_years_from_vietnamese_years():
    text = "Có 2 năm kinh nghiệm với Python, FastAPI và MongoDB."
    assert extract_experience_years(text) == 2


def test_extract_experience_years_from_date_ranges():
    text = "Backend Engineer 2021 - 2024. Intern 2020 - 2021."
    assert extract_experience_years(text) == 4


def test_parse_cv_text_includes_experience_confidence():
    data = parse_cv_text("Python FastAPI MongoDB. 2021 - 2024. Ho Chi Minh University")
    assert data["experience_years"] == 3
    assert data["experience_source"] == "date_range"
    assert data["experience_evidence"]
```

- [ ] **Step 2: Run RED test**

Run:

```powershell
$env:PYTHONPATH='backend'; pytest backend\tests\test_cv_parser.py -q
```

Expected: FAIL because `extract_experience_years`, `experience_source`, or `experience_evidence` missing.

- [ ] **Step 3: Implement parser minimally**

In `backend/app/services/cv_parser.py`, add:

```python
import re
from datetime import datetime


def extract_experience_years(text: str) -> float:
    lower = text.lower()
    explicit = [float(x) for x in re.findall(r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?|năm)", lower)]
    if explicit:
        return max(explicit)
    current_year = datetime.utcnow().year
    ranges = []
    for start, end in re.findall(r"\b(20\d{2}|19\d{2})\s*(?:-|–|to|đến)\s*(20\d{2}|19\d{2}|nay|present|current)\b", lower):
        start_year = int(start)
        end_year = current_year if end in {"nay", "present", "current"} else int(end)
        if 0 <= end_year - start_year <= 40:
            ranges.append(end_year - start_year)
    return float(sum(ranges)) if ranges else 0


def experience_metadata(text: str) -> dict:
    lower = text.lower()
    explicit_match = re.search(r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?|năm)", lower)
    if explicit_match:
        return {"experience_source": "explicit", "experience_evidence": explicit_match.group(0)}
    range_match = re.search(r"\b(20\d{2}|19\d{2})\s*(?:-|–|to|đến)\s*(20\d{2}|19\d{2}|nay|present|current)\b", lower)
    if range_match:
        return {"experience_source": "date_range", "experience_evidence": range_match.group(0)}
    return {"experience_source": "unknown", "experience_evidence": ""}
```

Then update `parse_cv_text()`:

```python
experience_years = extract_experience_years(text)
meta = experience_metadata(text)
return {
    ...,
    "experience_years": experience_years,
    **meta,
}
```

- [ ] **Step 4: Run GREEN test**

Run:

```powershell
$env:PYTHONPATH='backend'; pytest backend\tests\test_cv_parser.py -q
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

Run:

```powershell
git add backend/app/services/cv_parser.py backend/tests/test_cv_parser.py
git commit -m "Add explainable experience parser"
```

---

### Task 3: Skill Evidence Extraction

**Files:**
- Modify: `backend/app/services/matching.py`
- Modify: `backend/tests/test_matching.py`

- [ ] **Step 1: Add failing evidence test**

Append to `backend/tests/test_matching.py`:

```python

def test_compute_match_returns_skill_evidence():
    cv = {
        "raw_text": "Projects: Built APIs with Python and FastAPI. Skills: MongoDB, Docker.",
        "extracted_data": {"skills": ["python", "fastapi", "mongodb", "docker"], "experience_years": 3, "location": "Remote"},
    }
    job = {
        "title": "Backend",
        "description": "Need Python FastAPI Docker",
        "required_skills": ["python", "fastapi"],
        "nice_to_have_skills": ["docker", "kubernetes"],
        "required_experience": 2,
        "location": "Remote",
    }
    result = compute_match(cv, job)
    assert result["skill_evidence"]["python"]
    assert result["skill_evidence"]["fastapi"]
    assert result["missing_required_skills"] == []
    assert result["missing_nice_to_have_skills"] == ["kubernetes"]
```

- [ ] **Step 2: Run RED test**

Run:

```powershell
$env:PYTHONPATH='backend'; pytest backend\tests\test_matching.py::test_compute_match_returns_skill_evidence -q
```

Expected: FAIL because fields missing.

- [ ] **Step 3: Implement skill evidence helper**

Add to `backend/app/services/matching.py`:

```python
def skill_evidence(raw_text: str, skills: set[str]) -> dict:
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    if not lines:
        lines = [raw_text]
    evidence = {}
    for skill in skills:
        lower_skill = skill.lower()
        hit = next((line for line in lines if lower_skill in line.lower()), "")
        evidence[skill] = hit[:240]
    return evidence
```

- [ ] **Step 4: Extend `compute_match()` output**

Inside `compute_match()`:

```python
required_skills = norm_list(job.get("required_skills", []))
nice_skills = norm_list(job.get("nice_to_have_skills", []))
all_job_skills = required_skills | nice_skills
matched_required = sorted(cv_skills & required_skills)
matched_nice = sorted(cv_skills & nice_skills)
missing_required = sorted(required_skills - cv_skills)
missing_nice = sorted(nice_skills - cv_skills)
```

Return fields:

```python
"matched_required_skills": matched_required,
"matched_nice_to_have_skills": matched_nice,
"missing_required_skills": missing_required,
"missing_nice_to_have_skills": missing_nice,
"skill_evidence": skill_evidence(cv.get("raw_text", ""), set(matched_required + matched_nice)),
```

Keep legacy fields:

```python
"matched_skills": sorted(cv_skills & all_job_skills),
"missing_skills": sorted(all_job_skills - cv_skills),
```

- [ ] **Step 5: Run GREEN test**

Run:

```powershell
$env:PYTHONPATH='backend'; pytest backend\tests\test_matching.py -q
```

Expected: all matching tests pass.

- [ ] **Step 6: Commit**

Run:

```powershell
git add backend/app/services/matching.py backend/tests/test_matching.py
git commit -m "Add skill evidence to matching"
```

---

### Task 4: JD Required/Nice-to-Have Model

**Files:**
- Modify: `backend/app/schemas/common.py`
- Modify: `backend/app/routes/jobs.py`
- Modify: `frontend/src/pages/CreateJob.jsx`
- Modify: `frontend/src/pages/JobDetail.jsx`
- Modify: `frontend/src/pages/Jobs.jsx`
- Modify: `backend/scripts/seed.py`
- Test: `backend/tests/test_matching.py`

- [ ] **Step 1: Add failing scoring test for required vs nice skills**

Append to `backend/tests/test_matching.py`:

```python

def test_required_skills_outweigh_nice_to_have_skills():
    cv = {"raw_text": "Python FastAPI", "extracted_data": {"skills": ["python", "fastapi"], "experience_years": 2, "location": "Remote"}}
    job = {"title": "Backend", "description": "Python FastAPI Docker Kubernetes", "required_skills": ["python", "fastapi"], "nice_to_have_skills": ["docker", "kubernetes"], "required_experience": 2, "location": "Remote"}
    result = compute_match(cv, job)
    assert result["required_skill_score"] == 30
    assert result["nice_skill_score"] == 0
    assert result["skill_score"] == 30
    assert result["missing_nice_to_have_skills"] == ["docker", "kubernetes"]
```

- [ ] **Step 2: Run RED test**

Run:

```powershell
$env:PYTHONPATH='backend'; pytest backend\tests\test_matching.py::test_required_skills_outweigh_nice_to_have_skills -q
```

Expected: FAIL because new scoring fields missing.

- [ ] **Step 3: Extend backend schema**

In `backend/app/schemas/common.py`, update `JobIn`:

```python
class JobIn(BaseModel):
    title: str
    company_name: str
    location: str
    required_skills: List[str] = []
    nice_to_have_skills: List[str] = []
    required_experience: float = 0
    salary_range: Optional[str] = None
    description: str
    status: str = "open"
```

- [ ] **Step 4: Normalize job skills in routes**

In `backend/app/routes/jobs.py`, add:

```python
def clean_skills(values):
    return sorted({str(v).strip().lower() for v in values or [] if str(v).strip()})


def job_payload(payload: JobIn):
    data = payload.model_dump()
    data["required_skills"] = clean_skills(data.get("required_skills"))
    data["nice_to_have_skills"] = clean_skills(data.get("nice_to_have_skills"))
    return data
```

Use in create/update:

```python
doc = job_payload(payload)
```

```python
data = job_payload(payload)
data["updated_at"] = now_utc()
```

- [ ] **Step 5: Update matching weights**

Set scoring in `backend/app/services/matching.py`:

```python
required_skill_score = 30 if not required_skills else round((len(matched_required) / len(required_skills)) * 30, 2)
nice_skill_score = 10 if not nice_skills else round((len(matched_nice) / len(nice_skills)) * 10, 2)
skill_score = round(required_skill_score + nice_skill_score, 2)
```

Keep total formula still 100:

```python
total = round(skill_score + experience_score + location_score + similarity_score, 2)
```

- [ ] **Step 6: Update Create Job UI**

Replace `frontend/src/pages/CreateJob.jsx` form state:

```jsx
const [form,setForm]=useState({title:'',company_name:'',location:'',required_skills:'',nice_to_have_skills:'',required_experience:0,salary_range:'',description:'',status:'open'})
```

On submit:

```jsx
const csv = (value) => value.split(',').map(s=>s.trim()).filter(Boolean)
await api.post('/api/jobs', {
  ...form,
  required_skills: csv(form.required_skills),
  nice_to_have_skills: csv(form.nice_to_have_skills),
  required_experience: Number(form.required_experience)
})
```

Render explicit labels:

```jsx
{['title','company_name','location','required_skills','nice_to_have_skills','required_experience','salary_range'].map(...)}
```

- [ ] **Step 7: Update Job views**

In `frontend/src/pages/JobDetail.jsx`, show:

```jsx
<p><b>Required skills:</b> {(job.required_skills || []).join(', ') || 'Not specified'}</p>
<p><b>Nice-to-have skills:</b> {(job.nice_to_have_skills || []).join(', ') || 'None'}</p>
```

In `frontend/src/pages/Jobs.jsx`, show both required and nice skills in one cell.

- [ ] **Step 8: Run tests**

Run:

```powershell
$env:PYTHONPATH='backend'; pytest backend\tests\test_matching.py -q
npm run build --prefix frontend
```

Expected: all pass.

- [ ] **Step 9: Commit**

Run:

```powershell
git add backend/app/schemas/common.py backend/app/routes/jobs.py backend/app/services/matching.py backend/tests/test_matching.py frontend/src/pages/CreateJob.jsx frontend/src/pages/JobDetail.jsx frontend/src/pages/Jobs.jsx backend/scripts/seed.py
git commit -m "Support required and nice-to-have JD skills"
```

---

### Task 5: Match Detail Modal

**Files:**
- Create: `frontend/src/components/MatchDetailModal.jsx`
- Modify: `frontend/src/pages/Applications.jsx`
- Modify: `frontend/src/pages/Ranking.jsx`
- Modify: `frontend/src/style.css`

- [ ] **Step 1: Create modal component**

Create `frontend/src/components/MatchDetailModal.jsx`:

```jsx
function scoreLabel(score) {
  if (score >= 80) return 'Strong Match'
  if (score >= 60) return 'Good Match'
  return 'Weak Match'
}

export default function MatchDetailModal({ match, onClose }) {
  if (!match) return null
  return <div className="modal-backdrop" onClick={onClose}>
    <div className="modal-card match-modal" onClick={e=>e.stopPropagation()}>
      <div className="page-head"><div><p className="eyebrow">Match Analysis</p><h2>{Math.round(match.overall_score)}% · {scoreLabel(match.overall_score)}</h2></div><button className="btn" onClick={onClose}>Close</button></div>
      <div className="grid two">
        <div className="card"><h3>Score breakdown</h3><p>Required skills: {Math.round(match.required_skill_score || 0)}/30</p><p>Nice-to-have: {Math.round(match.nice_skill_score || 0)}/10</p><p>Experience: {Math.round(match.experience_score || 0)}/20</p><p>Location: {Math.round(match.location_score || 0)}/10</p><p>Text similarity: {Math.round(match.similarity_score || 0)}/30</p></div>
        <div className="card"><h3>Experience</h3><p>CV: {match.cv_experience_years ?? 0} years</p><p>Required: {match.required_experience ?? 0} years</p><p>{match.experience_match ? 'Passed' : 'Gap detected'}</p></div>
      </div>
      <div className="card"><h3>Matched required skills</h3>{(match.matched_required_skills || []).map(s => <span className="badge badge-success" key={s}>{s}</span>)}</div>
      <div className="card"><h3>Missing required skills</h3>{(match.missing_required_skills || []).length ? match.missing_required_skills.map(s => <span className="badge badge-danger" key={s}>{s}</span>) : <span className="badge badge-success">None</span>}</div>
      <div className="card"><h3>Skill evidence</h3>{Object.entries(match.skill_evidence || {}).map(([skill, evidence]) => <p key={skill}><b>{skill}:</b> {evidence || 'Detected in parsed skills'}</p>)}</div>
    </div>
  </div>
}
```

- [ ] **Step 2: Add CSS**

Append to `frontend/src/style.css`:

```css
.modal-backdrop{position:fixed;inset:0;background:rgba(15,23,42,.55);display:flex;align-items:center;justify-content:center;z-index:50;padding:24px}
.modal-card{background:var(--surface);border:1px solid var(--border);border-radius:24px;box-shadow:var(--shadow-lg);max-height:90vh;overflow:auto;width:min(980px,100%);padding:24px}
.match-modal .badge{margin:4px 6px 4px 0}
```

- [ ] **Step 3: Wire Applications page**

In `frontend/src/pages/Applications.jsx`, import and state:

```jsx
import MatchDetailModal from '../components/MatchDetailModal'
const [activeMatch,setActiveMatch]=useState(null)
```

Add button in match cell:

```jsx
<button className="btn" onClick={()=>setActiveMatch(match)} disabled={!match}>View Analysis</button>
{activeMatch && <MatchDetailModal match={activeMatch} onClose={()=>setActiveMatch(null)} />}
```

- [ ] **Step 4: Wire Ranking page**

In `frontend/src/pages/Ranking.jsx`, import modal and add state:

```jsx
import MatchDetailModal from '../components/MatchDetailModal'
const [activeMatch,setActiveMatch]=useState(null)
```

Add button per row:

```jsx
<button className="btn" onClick={()=>setActiveMatch(r)}>View Analysis</button>
```

Render modal after table.

- [ ] **Step 5: Build check**

Run:

```powershell
npm run build --prefix frontend
```

Expected: Vite build passes.

- [ ] **Step 6: Commit**

Run:

```powershell
git add frontend/src/components/MatchDetailModal.jsx frontend/src/pages/Applications.jsx frontend/src/pages/Ranking.jsx frontend/src/style.css
git commit -m "Add match detail analysis modal"
```

---

### Task 6: Data Backfill and Compatibility

**Files:**
- Create: `backend/scripts/backfill_match_reports.py`
- Modify: `README.md`

- [ ] **Step 1: Create backfill script**

Create `backend/scripts/backfill_match_reports.py`:

```python
import asyncio
from app.database import db, connect_db
from app.services.matching import compute_match
from app.dependencies import now_utc


async def main():
    await connect_db()
    count = 0
    async for cv in db.cvs.find({}):
        async for job in db.jobs.find({}):
            result = compute_match(cv, job)
            result.update({"job_id": job["_id"], "cv_id": cv["_id"], "recruiter_id": job.get("recruiter_id"), "updated_at": now_utc()})
            await db.matching_results.update_one({"job_id": job["_id"], "cv_id": cv["_id"]}, {"$set": result, "$setOnInsert": {"created_at": now_utc()}}, upsert=True)
            count += 1
    print(f"backfilled={count}")


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 2: Run local compile check**

Run:

```powershell
python -m py_compile backend\scripts\backfill_match_reports.py
```

Expected: passes.

- [ ] **Step 3: Document backfill**

Add to `README.md`:

```markdown
### Backfill explainable match reports

After changing matching logic, run:

`python backend/scripts/backfill_match_reports.py`

Production should run this with `MONGO_URI` set to the Atlas connection string. The script recomputes `matching_results` for existing CVs and jobs.
```

- [ ] **Step 4: Commit**

Run:

```powershell
git add backend/scripts/backfill_match_reports.py README.md
git commit -m "Add match report backfill script"
```

---

### Task 7: Local Verification Gate

**Files:**
- No code changes unless tests fail.

- [ ] **Step 1: Backend test suite**

Run:

```powershell
$env:PYTHONPATH='backend'; pytest backend\tests -q
```

Expected: all tests pass on Python 3.12. If local Python is 3.14 and scikit-learn wheel fails, run this in Docker or GitHub Actions and record that local Python version is incompatible.

- [ ] **Step 2: Frontend build**

Run:

```powershell
npm run build --prefix frontend
```

Expected: build passes.

- [ ] **Step 3: API shape smoke test**

Run against production after deploy or local against `localhost:8000`:

```powershell
$api='https://cv-match-platform-api-tk2.azurewebsites.net'
$login=Invoke-RestMethod -Method Post -Uri "$api/api/auth/login" -ContentType 'application/json' -Body (@{email='candidate@example.com';password='Candidate123!'}|ConvertTo-Json)
$h=@{Authorization="Bearer $($login.access_token)"}
$m=Invoke-RestMethod -Headers $h -Uri "$api/api/matches/my"
$m[0] | ConvertTo-Json -Depth 8
```

Expected fields exist:

```text
required_skill_score
nice_skill_score
skill_evidence
matched_required_skills
missing_required_skills
cv_experience_years
required_experience
```

- [ ] **Step 4: Commit if fixes were needed**

Run:

```powershell
git status --short
```

If dirty, commit focused fixes.

---

### Task 8: Production Deploy Gate

**Files:**
- No code changes.

- [ ] **Step 1: Push feature branch**

Run:

```powershell
git push origin feature/explainable-matching
```

- [ ] **Step 2: Merge to main after local tests pass**

Run:

```powershell
git switch main
git merge --no-ff feature/explainable-matching -m "Merge feature/explainable-matching"
git push origin main
```

- [ ] **Step 3: Deploy backend image**

Run:

```powershell
$sha=(git rev-parse --short HEAD)
$acr='cvmatchacrthaikhang'
$loginServer='cvmatchacrthaikhang.azurecr.io'
$image="cv-match-platform-api:$sha"
$full="$loginServer/$image"
az acr build --registry $acr --image $image backend --no-logs
az webapp config container set --resource-group rg-cv-match-platform --name cv-match-platform-api-tk2 --docker-custom-image-name $full --docker-registry-server-url "https://$loginServer"
az webapp restart --resource-group rg-cv-match-platform --name cv-match-platform-api-tk2
```

Expected Azure image:

```powershell
az webapp config show --resource-group rg-cv-match-platform --name cv-match-platform-api-tk2 --query "linuxFxVersion" -o tsv
```

Outputs tag matching current `$sha`.

- [ ] **Step 4: Deploy frontend**

Run from `frontend/` only:

```powershell
vercel deploy --prod --yes --scope thaikhang113s-projects
```

Expected alias:

```text
https://frontend-sigma-one-yds5b7xjmm.vercel.app
```

- [ ] **Step 5: Confirm CI/CD**

Run:

```powershell
$runs=(Invoke-RestMethod -Uri 'https://api.github.com/repos/thaikhang113/cv_jd_mapping/actions/runs?per_page=4' -Headers @{ 'User-Agent'='codex' }).workflow_runs
$runs | Select-Object name,head_sha,status,conclusion,event,created_at | Format-Table -AutoSize
```

Expected latest `CI` and `Deploy` are `completed success`.

---

### Task 9: Production Browser Verification Gate

**Files:**
- No code changes unless verification fails.

- [ ] **Step 1: Candidate match modal smoke test**

Create temp Playwright script outside repo:

```powershell
$tmp=Join-Path $env:TEMP 'cv-playwright-check'
New-Item -ItemType Directory -Force $tmp | Out-Null
```

Script must:

```javascript
const { chromium } = require('playwright');
const base='https://frontend-sigma-one-yds5b7xjmm.vercel.app';
(async()=>{
  const browser=await chromium.launch({headless:true});
  const page=await browser.newPage();
  await page.goto(base+'/login',{waitUntil:'networkidle'});
  await page.fill('input[placeholder="Email"]','candidate@example.com');
  await page.fill('input[placeholder="Password"]','Candidate123!');
  await page.click('form button:not([type])');
  await page.waitForURL('**/candidate',{timeout:15000});
  await page.goto(base+'/candidate/applications',{waitUntil:'networkidle'});
  await page.getByRole('button',{name:/View Analysis/i}).first().click();
  const text=await page.locator('body').innerText();
  console.log(JSON.stringify({
    hasModal:text.includes('Match Analysis'),
    hasEvidence:text.includes('Skill evidence'),
    hasRequired:text.includes('Required skills'),
    hasExperience:text.includes('CV:') && text.includes('Required:'),
  }));
  await browser.close();
})();
```

Expected JSON booleans all `true`.

- [ ] **Step 2: Recruiter ranking modal smoke test**

Script must login recruiter, go `/recruiter/ranking`, select a job, click `Run Matching`, click first `View Analysis`, assert modal details exist.

Expected:

```json
{"hasModal":true,"hasEvidence":true,"hasScoreBreakdown":true}
```

- [ ] **Step 3: JD create smoke test**

Script must login recruiter and create a job with:

```text
required_skills: python, fastapi
nice_to_have_skills: docker, kubernetes
```

Then open My Jobs/detail and assert both labels render.

- [ ] **Step 4: Final report**

Report:

```text
Backend tests: PASS
Frontend build: PASS
CI: PASS
Deploy: PASS
Candidate modal: PASS
Recruiter modal: PASS
JD required/nice-to-have: PASS
Known limitations: regex parser, not AI; edge cases remain for overlapping date ranges.
```

---

## Self-Review

- Spec coverage:
  - Experience parser: Task 2.
  - Skill evidence: Task 3.
  - JD required/nice-to-have: Task 4.
  - Match detail modal: Task 5.
  - Backfill existing data: Task 6.
  - Repeated testing: Tasks 7-9.
- Placeholder scan: no TBD/TODO/fill-later steps.
- Type consistency:
  - Backend fields: `required_skill_score`, `nice_skill_score`, `skill_evidence`, `matched_required_skills`, `missing_required_skills`.
  - Frontend modal reads same field names.
  - Existing legacy fields remain: `skill_score`, `matched_skills`, `missing_skills`.
- Risk notes:
  - Parser is regex-based, not AI; acceptable for this app constraint.
  - Date range overlap can over-count; if this becomes important, add interval merging in a later task.
  - Vercel deploy must run from `frontend/`, not repo root.
