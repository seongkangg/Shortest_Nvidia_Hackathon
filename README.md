# Resume Builder — Functional Requirements

A resume builder that pulls data from GitHub and LinkedIn, accepts job-target and profile fields, uses **NVIDIA/NVIDIA-Nemotron-Nano-9B-V2** to tailor content, and produces an editable LaTeX resume.

---

## 1. Overview

- **Purpose:** Generate a job-tailored LaTeX resume from GitHub repos, LinkedIn profile, job description, and user-provided profile fields; support post-generation editing.
- **AI Model:** `nvidia/NVIDIA-Nemotron-Nano-9B-V2` (Hugging Face / NVIDIA NIM). Used for content tailoring, summarization, and bullet-point generation from raw data and job description.

---

## 2. External Integrations

### 2.1 GitHub

- **FR-GH-1** Connect to user’s GitHub account via OAuth (or personal access token).
- **FR-GH-2** List user’s repositories (with optional filters: language, visibility, starred, etc.).
- **FR-GH-3** For selected repos, fetch metadata: name, description, primary language, topics/tags, star count, fork count, last updated.
- **FR-GH-4** Optionally fetch README or key files (e.g., one file per repo) for context.
- **FR-GH-5** Use repo metadata (and optional file content) as input to the Nemotron model to generate resume bullet points for “Projects” or “Experience” sections.

### 2.2 LinkedIn

- **FR-LI-1** Connect to user’s LinkedIn account (OAuth 2.0 or official API where available).
- **FR-LI-2** Retrieve profile data used for resume: full name, headline, summary/about, work experience (title, company, dates, description), education (school, degree, dates, field), skills, certifications, volunteer experience (if applicable).
- **FR-LI-3** Handle rate limits and consent; store only what the user authorizes and what is needed for the resume.
- **FR-LI-4** Use LinkedIn work/education/skills data as structured input to the Nemotron model for tailoring and bullet generation.

---

## 3. Job-Target and Job Description

- **FR-JOB-1** Provide a field for the **job application link/URL** (e.g., company career page or job board).
- **FR-JOB-2** **Fetch and parse job description** from the given URL (scraping or API where possible); support manual paste as fallback.
- **FR-JOB-3** Extract from job description: role title, company name, required skills, preferred qualifications, responsibilities, “good to have” items.
- **FR-JOB-4** Use job description (and extracted structured data) as context for the Nemotron model to tailor resume content (bullet points, emphasis, keywords).
- **FR-JOB-5** Allow user to **edit or replace** the job description text before resume generation.

---

## 4. User Profile and “Good to Have” Fields

- **FR-PF-1** **Name** (required): full name for the resume.
- **FR-PF-2** **Age** (optional): display or use for context as configured.
- **FR-PF-3** **Major / Field of study** (required for students; optional otherwise): degree and discipline.
- **FR-PF-4** **CGPA** (optional): GPA with scale (e.g., 4.0, 10.0) and optional explanation (e.g., “Major GPA”).
- **FR-PF-5** **Good to have:** free-form field(s) for additional points the user wants emphasized (e.g., “leadership,” “Python,” “published paper”). These must be incorporated into model prompts and, where appropriate, into the generated LaTeX content.
- **FR-PF-6** All profile fields must be available in the UI and stored so they can be used in prompts and in the final LaTeX resume.

---

## 5. AI Model (NVIDIA Nemotron Nano 9B V2)

- **FR-AI-1** Use **`nvidia/NVIDIA-Nemotron-Nano-9B-V2`** for all LLM-based steps (Hugging Face Transformers and/or NVIDIA NIM API).
- **FR-AI-2** Use the model to:
  - Generate or refine **bullet points** from GitHub repo metadata (and optional README/snippet).
  - Generate or refine **experience/education bullets** from LinkedIn data.
  - **Tailor** bullets and wording to the job description (keywords, responsibilities, “good to have”).
  - Optionally **summarize or extract** key requirements from the job description for internal use.
- **FR-AI-3** Support a **reasoning/thinking budget** (e.g., token limit for chain-of-thought) where the API supports it, for better tailoring.
- **FR-AI-4** Keep **prompts and model config** (temperature, max tokens, etc.) configurable and documented.
- **FR-AI-5** Handle API errors, timeouts, and rate limits; allow fallback to non-tailored or cached content when the model is unavailable.

---

## 6. LaTeX Resume Generation

- **FR-LX-1** Produce a **single, valid LaTeX file** that compiles to PDF (e.g., standard `article` or a common resume class like `moderncv`, or a custom template).
- **FR-LX-2** Populate LaTeX with:
  - Header: name, contact (from profile / LinkedIn).
  - Sections: Education (major, CGPA, school, dates), Experience (from LinkedIn + optional GitHub projects), Projects (from GitHub), Skills (from LinkedIn + job keywords), optional “Good to have” or “Highlights” from user fields.
- **FR-LX-3** Ensure **structure is consistent** (sections, ordering) and that special characters (e.g., `&`, `%`, `#`) are escaped for LaTeX.
- **FR-LX-4** Support at least one **template/style** (e.g., one-column, clear section headings); template choice can be extended later.
- **FR-LX-5** Provide **compilation path**: either local `pdflatex`/`xelatex` or a backend service that returns PDF; document the chosen approach.

---

## 7. Post-Generation Editing

- **FR-ED-1** After generation, present the resume in an **editable form**: raw **LaTeX source** in an editor (with syntax highlighting preferred).
- **FR-ED-2** Allow **recompile** (e.g., “Preview” or “Export PDF”) from the edited LaTeX without re-running the full pipeline.
- **FR-ED-3** Optional: **versioning or history** (e.g., save snapshots of LaTeX so the user can revert).
- **FR-ED-4** Optional: **re-run generation** with the same or updated inputs (job URL, profile, “good to have”) to get a new LaTeX draft, then continue editing.

---

## 8. Data and Security

- **FR-DS-1** **Secrets:** Store GitHub token, LinkedIn tokens, and any NVIDIA API key in environment variables or a secure config; never commit them.
- **FR-DS-2** **Data minimization:** Request only the OAuth scopes and LinkedIn/API fields needed for the resume.
- **FR-DS-3** **User data:** Define retention for cached profile/job data; allow user to disconnect accounts and delete cached data.
- **FR-DS-4** **Job URL scraping:** Comply with robots.txt and terms of use; prefer official job APIs where available.

---

## 9. User Flows (Summary)

1. **Connect:** User connects GitHub and LinkedIn; grants permissions.
2. **Profile:** User fills name, age, major, CGPA, and “good to have” fields.
3. **Job:** User enters job application URL; system fetches (or user pastes) job description; user can edit it.
4. **Generate:** User triggers generation; system fetches GitHub repos (and optional content) and LinkedIn profile, then uses Nemotron to tailor content and produce LaTeX.
5. **Edit:** User edits LaTeX in the app, recompiles to PDF, and can export or save.
6. **Optional:** User updates job URL or profile and regenerates for a new draft.

---

## 10. Non-Functional Considerations

- **NFR-1** Resume generation (including model calls) should complete within a reasonable time (e.g., &lt; 2 minutes for typical inputs).
- **NFR-2** UI should work on desktop; mobile-friendly is optional for v1.
- **NFR-3** Document how to run the app locally (env vars, API keys, LaTeX installation if needed).

---

## 11. Tech Stack Hints (for Cursor / Implementation)

- **Frontend:** Form for profile + job URL; OAuth buttons for GitHub/LinkedIn; LaTeX editor + PDF preview.
- **Backend:** Auth and token storage; GitHub/LinkedIn API clients; job URL fetcher/parser; Nemotron integration (Hugging Face or NVIDIA NIM); LaTeX generation service; optional PDF compilation.
- **Model:** `nvidia/NVIDIA-Nemotron-Nano-9B-V2` via Hugging Face `transformers`/`inference API` or [NVIDIA NIM](https://build.nvidia.com/nvidia/nvidia-nemotron-nano-9b-v2/modelcard).
- **LaTeX:** Escape user content; use a single template; support `pdflatex` or `xelatex` for PDF output.

---

## 12. Acceptance Criteria (High Level)

- [ ] User can connect GitHub and LinkedIn and see relevant data (repos, profile summary).
- [ ] User can enter job URL and see (or paste) job description used for tailoring.
- [ ] User can set name, major, age, CGPA, and “good to have” and these appear in prompts and resume.
- [ ] Generated resume is valid LaTeX and compiles to PDF.
- [ ] Resume content is tailored to the job description using Nemotron Nano 9B V2.
- [ ] User can edit the LaTeX and recompile to PDF.
- [ ] No secrets in source code; integration points documented.

---

*This README is intended as the single source of functional requirements for the resume builder project and can be parsed by Cursor or other tools for implementation guidance.*

---

## 13. Current Implementation (MVP)

Implemented in this repository:

- FastAPI backend with endpoints for:
  - GitHub repo fetch (`/api/github/repos`)
  - LinkedIn profile fetch (`/api/linkedin/profile`)
  - Resume generation (`/api/generate`)
  - LaTeX compile to PDF (`/api/compile`)
- OAuth URL and callback routes for GitHub and LinkedIn:
  - `/api/auth/github/url`, `/api/auth/github/callback`
  - `/api/auth/linkedin/url`, `/api/auth/linkedin/callback`
- Job URL fetch and text parsing for job description extraction.
- Nemotron integration through NVIDIA NIM/OpenAI-compatible chat completions:
  - Model default: `nvidia/nvidia-nemotron-nano-9b-v2`
  - Falls back to deterministic generation if model API is unavailable.
- LaTeX resume generation with character escaping and compile flow.
- Browser UI at `/` with:
  - Profile and “good to have” fields
  - Job URL + manual JD input
  - Token inputs for GitHub and LinkedIn
  - Editable LaTeX textarea + PDF preview iframe

### Run Locally

1. Create and activate virtualenv.
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Configure environment:
   - Copy `.env.example` -> `.env`
   - Fill API keys/client IDs as needed.
4. Start server:
   - `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
5. Open:
   - `http://localhost:8000`

### Notes

- For fastest testing, paste GitHub and LinkedIn tokens directly in UI fields.
- OAuth callback routes are present, but require valid provider app setup and matching redirect URIs.
- PDF compile requires `pdflatex` installed and available on PATH.
