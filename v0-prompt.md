# Copy everything below this line and paste it into v0.dev

---

Build a modern single-page **Resume Builder** UI (React + Tailwind, or Next.js + Tailwind). The app talks to an existing FastAPI backend. Match the following structure and API contract exactly so the backend keeps working.

## Page layout (sections)

1. **Header**  
   Title: "Resume Builder". Subtitle: "GitHub + LinkedIn + Job Description → LaTeX resume".

2. **Profile card**  
   Form fields (same names/ids or same state keys so API payload matches):
   - Name * (required)
   - Age (number)
   - Major
   - CGPA
   - Email
   - Phone
   - Location
   - LinkedIn URL
   - GitHub URL
   - Good to have (comma-separated, placeholder: "leadership, python, machine learning")

3. **Integrations card**  
   - Session ID (text input; pre-fill from localStorage key `resume_builder_session`, or generate once like `sess_` + random string and save to localStorage)
   - GitHub token (optional)
   - LinkedIn profile URL (placeholder: "https://www.linkedin.com/in/your-handle")
   - Button: "Load GitHub Repos" → calls API below
   - Button: "Scrape LinkedIn Profile" → calls API below
   - Small area to show result of last integration call (e.g. "Integration info")

4. **Job card** (can be same card as Integrations or below)
   - Job URL (placeholder: "https://...")
   - Job Description (textarea, optional; backend fetches from URL if empty)

5. **Generate & Edit card**  
   - Button: "Generate Resume LaTeX"
   - Button: "Compile PDF"
   - Large editable textarea for LaTeX source
   - Status area (warnings / success / error messages)

6. **PDF Preview**  
   - Iframe or embed that shows the PDF when compile returns success (base64 PDF).

## API contract (use these exactly)

**Base URL:** assume same origin (e.g. `/api/...`) or allow env variable like `NEXT_PUBLIC_API_URL` for `http://localhost:8000`.

1. **GET /api/github/repos**  
   Query params: `session_id` (required), `include_readme` ("true" or "false"), optional `token` (GitHub token).  
   Response: JSON array of repo objects.

2. **GET /api/linkedin/profile**  
   Query params: `session_id`, and either `profile_url` (LinkedIn public profile URL) or nothing.  
   Response: JSON object (LinkedIn profile with full_name, headline, experiences, etc.).

3. **POST /api/generate**  
   Body (JSON):
   ```json
   {
     "session_id": "string",
     "profile": {
       "name": "string",
       "age": null or number,
       "major": null or "string",
       "cgpa": null or "string",
       "email": null or "string",
       "phone": null or "string",
       "location": null or "string",
       "linkedin_url": null or "string",
       "github_url": null or "string",
       "good_to_have": ["string", "string"]
     },
     "job_url": null or "string",
     "job_description": null or "string",
     "github_token": null or "string",
     "linkedin_profile_url": null or "string",
     "include_readme": false,
     "selected_repo_names": []
   }
   ```
   Response: `{ "latex": "string", "parsed_job": {}, "github_repos": [], "linkedin_profile": {}, "warnings": [] }`.  
   On success: put `data.latex` into the LaTeX textarea and show `data.warnings` in the status area.

4. **POST /api/compile**  
   Body: `{ "latex": "string" }`  
   Response: `{ "success": true/false, "message": "string", "pdf_base64": "string" or null }`.  
   On success: set iframe src to `data:application/pdf;base64,${data.pdf_base64}`.

## Behavior to preserve

- Session ID: on load, if no `resume_builder_session` in localStorage, set it to `sess_` + random string (e.g. `Math.random().toString(36).slice(2)`), then show in Session ID field.
- Good to have: split by comma, trim, filter empty → array of strings.
- Profile: age is integer or null; all other optional fields string or null.
- Generate: send the exact JSON shape above; show errors in status if response not ok.
- Compile: only update PDF if `data.success && data.pdf_base64`.

Make the UI clean, modern, and responsive (cards for each section, clear labels, good spacing). Use Tailwind. Keep the same field names and payload structure so the existing FastAPI backend works without changes.
