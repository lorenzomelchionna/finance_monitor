/** Extract a human-readable message from a FastAPI error body — either
 * `{detail: "string"}` (simple HTTPException) or `{detail: [{msg, loc,
 * type}, ...]}` (Pydantic validation error, 422). */
export function extractErrorMessage(err: unknown): string {
  if (err && typeof err === "object" && "detail" in err) {
    const detail = (err as { detail: unknown }).detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return detail
        .map((d) => (d && typeof d === "object" && "msg" in d ? String(d.msg) : JSON.stringify(d)))
        .join("; ");
    }
  }
  return "Errore sconosciuto.";
}
