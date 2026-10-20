# LifeTime backend starter

Backend-only starter. No real public facility data, Supabase credentials, or walking-route keys are included.

## Windows PowerShell

If the GitHub repository is empty, initialize main on GitHub with a README first. Then:

```powershell
git clone https://github.com/pyeon-pyeon/LifeTime.git
cd LifeTime
git switch main
git pull origin main
git switch -c feat/backend-db-security
```

Copy the `backend`, `docs` and `.gitignore` files from this starter into the cloned repository root, then:

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/docs`. In a second terminal, run `python -m pytest -q` in `backend` with the virtual environment active.

Do not commit `.env`, API secrets, or `.venv`. Before push, review `git status`, then `git add backend docs .gitignore README.md`, commit, and `git push -u origin feat/backend-db-security`.
