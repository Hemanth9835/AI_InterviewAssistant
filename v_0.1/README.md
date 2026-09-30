# Interview Practice v0

Minimal React + FastAPI app for generating one interview prompt at a time.

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

   Open `.env` and replace `your-openai-api-key` with your key. The backend loads
   this file at startup. `.env` is ignored by Git and must never be committed.

3. Start FastAPI:

   ```powershell
   uvicorn Backend.main:app --reload
   ```

4. Serve the frontend in a second terminal. Any static server works; for example:

   ```powershell
   cd Frontend
   py -m http.server 5173
   ```

   Open http://localhost:5173.

The optional `OPENAI_MODEL` environment variable defaults to `gpt-4o-mini`.

For a public deployment, use the hosting provider's secret/environment-variable
store instead of uploading `.env`. The API key stays in FastAPI and is never sent
to the React browser client.
