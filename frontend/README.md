# CareerAI Frontend

Yellow-themed, 3D-inspired React/Vite frontend for the AI Job Recommendation System.

## Run

```bash
cd frontend
npm install
npm run dev
```

The UI uses `VITE_API_URL` for the FastAPI backend. Default: `http://localhost:8000`.

## Current implementation

- Premium yellow/cream landing page
- CSS 3D dashboard hero
- Login/register flow wired to `/auth/register` and `/auth/login`
- Auth token storage and authenticated app shell
- Dashboard wiring for profile, recommendations, application summary and unread notifications
- Responsive layout
- Backend-aware navigation for future page wiring
