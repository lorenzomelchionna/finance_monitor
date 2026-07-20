import createClient from "openapi-fetch";
import type { paths } from "./schema";

// Regenerate schema.d.ts after any backend API change: `npm run gen:api`
// (requires the backend running on :8000).
export const api = createClient<paths>({ baseUrl: "http://127.0.0.1:8000" });
