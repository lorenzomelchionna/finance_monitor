import createClient from "openapi-fetch";
import type { paths } from "./schema";

// Regenerate schema.d.ts after any backend API change: `npm run gen:api`
// (requires the backend running on :8000).
//
// Deployed, this bundle and the API are served by the same process, so
// the base URL is empty and calls go same-origin — which also lets the
// browser replay its Basic Auth credentials automatically. In dev, Vite
// serves the UI on :5173 while the API listens on :8000, hence the
// explicit origin there. VITE_API_BASE_URL overrides both.
const DEV_API_ORIGIN = "http://127.0.0.1:8000";

export const api = createClient<paths>({
  baseUrl: import.meta.env.VITE_API_BASE_URL ?? (import.meta.env.DEV ? DEV_API_ORIGIN : ""),
});
