# GridWise Frontend

This is the premium React frontend for the GridWise Smart Campus Energy Optimization backend.

## Tech Stack
- **Framework:** React 18 + Vite
- **Language:** TypeScript
- **Styling:** Tailwind CSS v4
- **Routing:** React Router v6
- **State Management:** Zustand
- **Icons:** Lucide React
- **Charts:** Recharts

## Setup Instructions

1. **Navigate to the frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Configure Environment Variables:**
   The frontend communicates with the FastAPI backend. By default, it expects the backend to run on `http://localhost:8000`.
   If you need to change this, create a `.env` file in the `frontend/` directory:
   ```
   VITE_API_BASE_URL=http://localhost:8000
   ```
   **Important:** Do NOT place the `GROQ_API_KEY` in the frontend `.env`. The frontend never talks directly to the LLM to preserve the security boundary and guardrail integrity.

4. **Run the Development Server:**
   ```bash
   npm run dev
   ```
   The application will be available at `http://localhost:5173`.

## Production Build

To build the static assets for production:

```bash
cd frontend
npm run build
```

This will output the optimized static bundle to `frontend/dist/`. You can serve these static files using Nginx or FastAPI's `StaticFiles` middleware if desired.

## Backend Integration

The frontend uses the exact Pydantic schema defined in `app/schemas.py`. 
- **API File:** `src/services/api.ts`
- **Types:** `src/types/api.types.ts`

The flow is strictly:
`Frontend (React)` → `FastAPI Backend` → `Groq LLM` → `Guardrails` → `MILP Optimizer` → `Validator` → `Frontend (React)`
