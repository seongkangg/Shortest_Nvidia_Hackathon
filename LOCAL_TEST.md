# Localhost test (fix common errors)

## The usual error: `ModuleNotFoundError: No module named 'httpx'` (or `fastapi`, etc.)

That means **dependencies are not installed** for the Python you’re using.

**Fix — use a venv and install once:**

```bash
cd /path/to/Shortest_Nvidia_Hackathon
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Or one command:

```bash
chmod +x run-local.sh
./run-local.sh
```

Then open **http://127.0.0.1:8000** (not `file://`).

---

## Other errors

| Error | Cause | Fix |
|-------|--------|-----|
| `No module named 'httpx'` | No venv / didn’t `pip install` | Steps above |
| `Unable to connect` / refused | Server not running | Start `uvicorn` first; use port **8000** |
| `wrong directory` / import errors | Not in project root | `cd` to folder that contains `app/` and `requirements.txt` |
| Homebrew Python blocks `pip install` | PEP 668 | Use `python3 -m venv .venv` then `.venv/bin/pip install` |

---

## `.env` (optional)

Copy `.env.example` → `.env`. For local testing you can leave NVIDIA keys empty; add **GitHub** keys if you use OAuth. You can also paste a **GitHub Personal Access Token** in the UI without OAuth.
