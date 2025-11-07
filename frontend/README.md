# Portalyze Frontend (React + Vite)

The `portfolio-grader` package is the React/Vite interface for Portalyze. It provides the landing page, progress visualisations, batch upload workflow, and detailed results views.

## 🔧 Local Development

```bash
cd portfolio-grader
npm install
npm run dev
```

The dev server runs on `http://localhost:5173` by default. If that port is busy Vite will pick the next available one (e.g. `5174`).

### Environment Variables

Create a `.env` file (or configure in your hosting provider) with:

```bash
VITE_API_BASE_URL=http://localhost:8000
```

For production builds, set this to the public URL of your deployed backend.

> Any `VITE_` prefixed variable is baked into the client bundle at build time—remember to rebuild after changing it.

## 🧱 Available Scripts

| Script           | Description                              |
| ---------------- | ---------------------------------------- |
| `npm run dev`    | Start Vite dev server with HMR           |
| `npm run build`  | Create production build in `dist/`       |
| `npm run preview`| Preview the production build locally     |
| `npm run lint`   | Run ESLint across the codebase           |

## 🧩 Key Components

- `Landing.tsx` – entry point for single analysis with optional “force refresh” toggle.
- `GradingProgress.tsx` – animated progress indicator while the backend works.
- `Result.tsx` – renders the detailed checklist and AI feedback for single portfolios.
- `BatchUpload.tsx` / `BatchResults.tsx` – CSV upload, processing, and results explorer with checklist drill-down.

Styling uses Tailwind classes with a dark UI palette optimised for deployment.

## 🚀 Deployment Tips

1. Run `npm run build` – the distributable assets are generated in `dist/`.
2. Serve the contents of `dist/` via your preferred static host (Vercel, Netlify, Render static site, etc.).
3. Ensure the `VITE_API_BASE_URL` env variable matches your backend URL during the build step.

## ✅ Quality Checklist

- [x] Responsive layout tested on mobile, tablet, desktop breakpoints.
- [x] Dark mode first styling, no reliance on system preference.
- [x] CSV export includes all 27 checklist parameters.
- [x] Force-refresh option wired to backend cache invalidation.
