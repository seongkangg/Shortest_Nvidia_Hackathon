## AI-Powered Resume Builder (Nemotron-Based)

An AI-powered resume builder that connects to your GitHub and LinkedIn accounts, takes a target job description, and generates a LaTeX resume tailored to that job using `nvidia/nvidia-nemotron-nano-9b-v2`. Users can fully edit and version their resumes afterward.

---

## High-Level Overview

- **Tech focus**: NVIDIA `nvidia/nvidia-nemotron-nano-9b-v2` as the core LLM.
- **Inputs**:
  - GitHub profile & repositories (via OAuth).
  - LinkedIn profile & experiences (via OAuth).
  - Target job description (URL and/or pasted text).
  - Personal info (name, major, age, CGPA, etc.).
  - “Good to have” notes and user preferences.
- **Output**:
  - Compilable LaTeX resume tailored to the job.
  - Editable LaTeX with live preview and PDF export.
  - Multi-version management per user/job.

---

## Functional Requirements

### 1. User Accounts & Authentication

- **FR-1.1.1**: Allow users to register using email and password.
- **FR-1.1.2**: Validate email format and enforce a minimum password strength policy.

- **FR-1.2.1**: Allow users to log in with email and password.
- **FR-1.2.2**: Maintain authenticated sessions using secure cookies or tokens (e.g., JWT).
- **FR-1.2.3**: Provide logout to invalidate the session.

- **FR-1.3.1**: Store basic user profile data (name, email, default settings).
- **FR-1.3.2**: Allow users to view and update their profile.

---

### 2. Third‑Party Integrations

#### 2.1 GitHub Integration

- **FR-2.1.1**: Allow users to connect GitHub via OAuth.
- **FR-2.1.2**: Request minimum GitHub scopes (read-only repos/profile).
- **FR-2.1.3**: Securely store GitHub tokens (encrypted at rest).
- **FR-2.1.4**: Fetch user repositories (public and private if permitted).
- **FR-2.1.5**: Fetch metadata for selected repositories:
  - Name, description, primary language, stars, forks, last updated date.
  - Optionally README content and commit history summaries.
- **FR-2.1.6**: Let users select which repositories/projects to highlight on a resume.
- **FR-2.1.7**: Allow users to disconnect GitHub and revoke token usage.

#### 2.2 LinkedIn Integration

- **FR-2.2.1**: Allow users to connect LinkedIn via OAuth (using LinkedIn APIs or compliant flow).
- **FR-2.2.2**: Request minimal scopes to read profile and experience data.
- **FR-2.2.3**: Securely store LinkedIn tokens (encrypted at rest).
- **FR-2.2.4**: Fetch LinkedIn profile data (subject to API availability):
  - Headline, current and previous positions (titles, companies, dates), education, skills, location.
- **FR-2.2.5**: Allow users to select which experiences and education entries to include.
- **FR-2.2.6**: Allow users to disconnect LinkedIn and revoke token usage.

---

### 3. Job Description Input & Parsing

- **FR-3.1.1**: Provide an input field for a job URL (LinkedIn, company careers page, etc.).
- **FR-3.1.2**: Attempt to fetch and scrape the job description from the given URL.
- **FR-3.1.3**: If scraping fails, allow the user to paste the job description text manually.
- **FR-3.1.4**: Store the raw job description per resume.
- **FR-3.1.5**: Preprocess the job description for the LLM, extracting:
  - Job title, location (if present), responsibilities, required skills, preferred skills, keywords.

---

### 4. User-Provided Resume Inputs

#### 4.1 Personal & Academic Information

- **FR-4.1.1**: Provide fields for:
  - Full name
  - Age (optional)
  - Major / field of study
  - CGPA (optional; support decimals and configurable format)
- **FR-4.1.2**: Allow users to toggle showing/hiding age and CGPA in the final resume.

#### 4.2 “Good to Have” & Preferences

- **FR-4.2.1**: Provide a free‑text field for “good to have” information (e.g., preferred tech stack, dream role details, extra achievements).
- **FR-4.2.2**: Allow multiple “good to have” entries or bullet points.
- **FR-4.2.3**: Allow users to specify additional constraints/preferences:
  - Resume length (e.g., 1 page).
  - Tone (concise, impact‑focused, academic, etc.).
  - Target role(s) and seniority (e.g., SWE intern, ML engineer).

---

### 5. Resume Generation Using NVIDIA Nemotron

#### 5.1 Model Integration

- **FR-5.1.1**: Integrate `nvidia/nvidia-nemotron-nano-9b-v2` as the core LLM.
- **FR-5.1.2**: Call the model via NVIDIA API / NIM deployment / local inference endpoint (configurable).
- **FR-5.1.3**: Encapsulate model calls behind a service layer with:
  - Input validation.
  - Error handling and retries.
  - Logging of prompts and responses, with PII-safe redaction as needed.

#### 5.2 Prompt Construction & Data Fusion

- **FR-5.2.1**: Construct prompts that combine:
  - User profile data (name, major, CGPA preferences, etc.).
  - Selected GitHub repositories and metadata.
  - Selected LinkedIn experiences, education, skills.
  - Parsed job description and extracted keywords.
  - “Good to have” notes and user preferences.
- **FR-5.2.2**: Ensure prompts instruct the model to:
  - Tailor the resume to the provided job.
  - Emphasize most relevant projects/experiences.
  - Respect user preferences (e.g., hide age, CGPA; enforce 1-page).
- **FR-5.2.3**: Use structured prompt templates so they can be updated without changing core logic.

#### 5.3 LaTeX Resume Generation

- **FR-5.3.1**: Generate the resume in LaTeX format using the Nemotron output.
- **FR-5.3.2**: Either:
  - Generate valid LaTeX directly from the model, or
  - Generate structured content (JSON/markdown) then render into a predefined LaTeX template.
- **FR-5.3.3**: Validate that the generated LaTeX compiles successfully.
- **FR-5.3.4**: Present LaTeX compilation errors to the user and provide options to:
  - Auto-fix simple issues (e.g., unescaped characters).
  - Let the user edit the LaTeX manually.

#### 5.4 Iteration & Regeneration

- **FR-5.4.1**: Allow users to regenerate the resume with adjusted preferences (e.g., different focus or tone).
- **FR-5.4.2**: Support multiple resume versions per job (e.g., “Version 1”, “ML focus”).
- **FR-5.4.3**: Maintain a history of LaTeX versions per job and user.

---

### 6. Resume Editing & Preview

- **FR-6.1.1**: Display generated LaTeX in an editable text editor (ideally with syntax highlighting).
- **FR-6.1.2**: Allow users to modify any part of the LaTeX.
- **FR-6.1.3**: Provide a preview feature that renders LaTeX into a PDF (or browser-friendly view).
- **FR-6.1.4**: Allow downloads of:
  - PDF resume.
  - LaTeX source.
- **FR-6.1.5**: Do not overwrite manual edits when regenerating unless the user explicitly chooses a full regeneration.
- **FR-6.1.6**: Allow users to mark a resume as “final” and lock it from further automatic model changes (still allow manual LaTeX edits).

---

### 7. Resume Data Model & Management

- **FR-7.1.1**: Represent each resume with:
  - Owner user ID.
  - Associated job (URL + parsed description).
  - Selected GitHub and LinkedIn entries.
  - User configuration/preferences.
  - LaTeX content.
  - Version history.
- **FR-7.1.2**: Allow multiple resumes per user.
- **FR-7.1.3**: Provide a list view of all user resumes with:
  - Resume name.
  - Parsed job title (if available).
  - Created and last modified timestamps.
- **FR-7.1.4**: Allow users to duplicate an existing resume as a starting point.

---

### 8. UI/UX (Functional)

- **FR-8.1.1**: Provide a guided multi-step flow for:
  1. Connecting GitHub & LinkedIn.
  2. Supplying job URL / description.
  3. Confirming/importing personal, academic, “good to have” info.
  4. Reviewing and customizing the generated resume.
- **FR-8.1.2**: Show loading states when:
  - Connecting to third-party APIs.
  - Calling Nemotron.
  - Rendering LaTeX to PDF.
- **FR-8.1.3**: Show clear error messages for:
  - Third-party connection failures.
  - Job scraping issues.
  - Model errors/timeouts.
  - LaTeX compilation problems.
- **FR-8.1.4**: Ensure a responsive layout usable on desktop/laptop (mobile optional but desirable).

---

### 9. Security & Privacy

- **FR-9.1.1**: Never share user data (repos, LinkedIn info, resumes) between users.
- **FR-9.1.2**: Allow users to delete their account and all associated data:
  - Tokens.
  - Resumes and histories.
  - Cached job descriptions.
- **FR-9.1.3**: Avoid logging sensitive information (full tokens, personal identifiers) in plain text.
- **FR-9.1.4**: Support configurable data retention policies (logs, temporary files).

---

### 10. Performance & Reliability

- **FR-10.1.1**: Target first draft generation in < 15 seconds (configurable).
- **FR-10.1.2**: Implement timeouts and fallbacks for:
  - GitHub/LinkedIn API calls.
  - Model inference calls.
- **FR-10.1.3**: Provide user-friendly retry options when calls fail.
- **FR-10.1.4**: Cache non-sensitive GitHub/LinkedIn data per user to reduce API calls where allowed.

---

### 11. Configuration & Environment

- **FR-11.1.1**: Use environment variables for:
  - NVIDIA model endpoint and credentials (`nvidia-nemotron-nano-9b-v2`).
  - GitHub OAuth client ID/secret.
  - LinkedIn OAuth client ID/secret.
  - Backend and frontend base URLs.
- **FR-11.1.2**: Provide a `.env.example` documenting all required variables.

---

### 12. Analytics & Logging (Optional)

- **FR-12.1.1**: Log major events:
  - GitHub/LinkedIn connect/disconnect.
  - Resume generation requests and results.
  - LaTeX compilation successes/failures.
- **FR-12.1.2**: Track basic metrics:
  - Resumes generated per user.
  - Average model latency.
  - Common error types.
- **FR-12.1.3**: Anonymize or pseudonymize analytics data where possible.

---

## Suggested Architecture (High-Level)

- **Frontend**:
  - React/Next.js or similar SPA for the guided flow, LaTeX editor, preview, and downloads.
- **Backend**:
  - REST/GraphQL service for:
    - Auth and user profiles.
    - GitHub/LinkedIn OAuth flows and data fetching.
    - Job description scraping and parsing.
    - Resume entity management and versioning.
    - LaTeX compilation and PDF generation.
    - Calling the Nemotron model service.
- **Model Layer**:
  - Service wrapper around `nvidia/nvidia-nemotron-nano-9b-v2` (NIM, cloud, or on-prem), exposing a single “generate_resume” endpoint with structured input.

---

## Setup & run

- **Prerequisites**: Python 3.10+, pip. Optional: LaTeX (for PDF), GitHub OAuth app, NVIDIA Nemotron endpoint.
- **Backend** (from project root):
  - `cd backend && pip install -r requirements.txt` (if SSL errors, add `--trusted-host pypi.org --trusted-host files.pythonhosted.org`).
  - Copy `.env.example` to `.env` in the project root and set `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`, and optionally `NVIDIA_NEMOTRON_ENDPOINT` / `NVIDIA_NEMOTRON_API_KEY`. Set `API_BASE_URL=http://localhost:8000` and `APP_BASE_URL=http://localhost:3000` for local run.
  - Run: `cd backend && .venv/bin/uvicorn app:app --reload --port 8000` (or `uvicorn app:app --reload --port 8000` from inside `backend/`).
- **Frontend**: Serve the frontend on port 3000 so the app can call the API and GitHub OAuth redirect works:
  - `cd frontend && npx serve -p 3000`  
  - Or: `cd frontend && python3 -m http.server 3000`  
  Then open **http://localhost:3000** in your browser (do **not** open the HTML file directly with `file://` — the app must be served from localhost so it can connect to the backend).
- **Connecting to localhost**: The backend allows CORS from `http://localhost:3000`, `http://127.0.0.1:3000`, and `file://`. The frontend uses `http://localhost:8000` as the API when the page is on localhost or opened as a file. If the backend is running on 8000 and you open the app from **http://localhost:3000**, “Connect GitHub”, “Generate”, and “Save” should work.
- **Features**: Connect GitHub (repos), paste LinkedIn text, name/major/age/CGPA, job URL + fetch or paste description, good-to-have, generate LaTeX (Nemotron or fallback), edit and save resumes, download .tex, list and reopen saved resumes.

## Vercel deploy – step by step

### Step 1: Push your code to GitHub
- Commit and push this repo to GitHub (if you haven’t already).
- You’ll connect that repo to Vercel in the next step.

### Step 2: Create a Vercel project from the repo
1. Go to **[vercel.com](https://vercel.com)** and sign in (GitHub is easiest).
2. Click **“Add New…”** → **“Project”**.
3. Under **“Import Git Repository”**, select your **Shortest_Nvidia_Hackathon** repo (or the one you pushed).
4. Click **“Import”**.
5. On the **Configure Project** screen:
   - **Framework Preset**: leave as “Other” (or “No framework”).
   - **Root Directory**: leave **default** (project root).
   - **Build Command**: leave as-is (the repo’s `vercel.json` uses `echo 'No build'`).
   - **Output Directory**: leave as-is (`vercel.json` sets it to `frontend`).
6. **Do not** add any environment variables yet. Click **“Deploy”**.
7. Wait for the deploy to finish. You’ll get a URL like `https://your-project.vercel.app`. Open it to confirm the resume builder UI loads (it will show an error when calling the API until you set the backend and `API_URL`).

### Step 3: Add the backend URL in Vercel
1. In Vercel, open your **project** (the one you just deployed).
2. Go to the **“Settings”** tab.
3. In the left sidebar, click **“Environment Variables”**.
4. Add one variable:
   - **Key:** `API_URL`  
   - **Value:** your backend URL, e.g. `https://your-backend.railway.app` (no trailing slash).  
   - **Environment:** leave all three checked (Production, Preview, Development) or at least **Production**.
5. Click **“Save”**.
6. Go to the **“Deployments”** tab, open the **⋮** menu on the latest deployment, and click **“Redeploy”** so the new `API_URL` is used.

### Step 4: Deploy the backend (if not done yet)
The frontend needs a live backend. Deploy the **backend** (FastAPI app in `/backend`) to any host, for example:
- **Railway**: [railway.app](https://railway.app) → New Project → Deploy from GitHub (select this repo, set root to `backend` or run `uvicorn app:app --host 0.0.0.0 --port $PORT`), add env vars from your `.env`.
- **Render**: [render.com](https://render.com) → New → Web Service → connect repo, set build to `pip install -r backend/requirements.txt` and start to `uvicorn app:app --host 0.0.0.0 --port $PORT`, set root to `backend` or adjust paths, add env vars.

Then set the backend’s env:
- `API_BASE_URL` = your backend’s public URL (e.g. `https://your-app.railway.app`).
- `APP_BASE_URL` = your Vercel URL (e.g. `https://your-project.vercel.app`).

Use that **backend URL** as `API_URL` in Vercel (Step 3).

### Step 5: GitHub OAuth (for “Connect GitHub”)
1. In [GitHub → Settings → Developer settings → OAuth Apps](https://github.com/settings/developers), open your OAuth app (or create one).
2. Set **Authorization callback URL** to:  
   `https://<your-backend-url>/auth/github/callback`  
   Example: `https://your-app.railway.app/auth/github/callback`.
3. Save. Now “Connect GitHub” in the resume builder will work once the backend is deployed and env vars are set.

### Step 6: Check that everything works
- Open your Vercel URL (e.g. `https://your-project.vercel.app`).
- Fill in name, optional job description, and click **Generate LaTeX resume**. You should get a resume (or a fallback template if Nemotron isn’t configured).
- If you set up the backend and GitHub OAuth, try **Connect GitHub** and **Fetch description** to confirm end-to-end.

## Deploy / verify

- **Backend** was verified locally: `GET /health`, `POST /job/fetch`, `POST /generate-resume`, `GET /resumes`, `GET /auth/github` all respond correctly. With no Nemotron endpoint, generation returns a fallback LaTeX template and still creates a saved resume.
- **Frontend**: Run the backend and a static server (see above), then open http://localhost:3000 to use the full flow (GitHub connect, job fetch, generate, edit, save, download .tex).
- For **production**: deploy backend (Railway, Render, Fly.io), then deploy frontend to Vercel and set `API_URL` to the backend URL. Update GitHub OAuth callback to your backend’s `/auth/github/callback`.


