# Interview Practice v0

React + FastAPI app for authenticated interview preparation with PostgreSQL-backed users.

## Setup

1. From `v_0.1`, activate the existing virtual environment and install the backend packages:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   pip install -r Backend\requirements.txt
   ```

2. Create a local environment file from the safe template:

   ```powershell
   Copy-Item .env.example .env
   ```
   Set `OPENAI_API_KEY`, `DATABASE_URL`, and a long random `JWT_SECRET_KEY` in this file.
   `.env` is ignored by Git and must never be committed.

3. Start FastAPI from the backend directory:

   ```powershell
   cd Backend
   uvicorn main:app --reload
   ```

   The backend creates the `users` table automatically when `DATABASE_URL` is configured.
   Create the first login user from the `v_0.1\Backend` directory:

   ```powershell
   python seed_user.py
   ```

4. Serve the frontend in a second terminal. Any static server works; for example:

   ```powershell
   cd Frontend
   py -m http.server 5173
   ```

   Open http://localhost:5173.

The optional `OPENAI_MODEL` environment variable defaults to `gpt-4o-mini`.

For a public deployment, use the hosting provider's secret/environment-variable stored instead of uploading `.env`. 
The API key stays in FastAPI and is never sent
to the React browser client.

Login and registration endpoints:

- `POST /api/auth/login` accepts `{ "name": "...", "password": "..." }` and returns a bearer token.
- `POST /api/auth/register` accepts `{ "name": "...", "password": "..." }`, creates a hashed-password user, and returns a bearer token.
- `GET /api/auth/me` validates the current bearer token.
- `POST /api/generate` requires `Authorization: Bearer <token>`.

Passwords are stored as Argon2 hashes in the `users.password` column, never as plaintext.
