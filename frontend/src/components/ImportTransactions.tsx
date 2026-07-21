import { useRef, useState } from "react";
import { useImportTransactions, type ImportResultOut } from "../api/hooks";
import { extractErrorMessage } from "../lib/apiError";

/** Upload control for a Fineco "Movimenti Dossier Titoli" xlsx. Reports
 * how many operations were imported / skipped (instruments not in the
 * portfolio) / already present. */
export function ImportTransactions() {
  const importTx = useImportTransactions();
  const inputRef = useRef<HTMLInputElement>(null);
  const [result, setResult] = useState<ImportResultOut | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleFile(file: File) {
    setError(null);
    setResult(null);
    try {
      const res = await importTx.mutateAsync(file);
      setResult(res);
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  }

  return (
    <div className="import-box">
      <div className="import-row">
        <input
          ref={inputRef}
          type="file"
          accept=".xlsx"
          style={{ display: "none" }}
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) handleFile(f);
            e.target.value = "";
          }}
        />
        <button type="button" onClick={() => inputRef.current?.click()} disabled={importTx.isPending}>
          {importTx.isPending ? "Importo…" : "📥 Importa movimenti Fineco (.xlsx)"}
        </button>
      </div>

      {error && <p className="error-banner">Import fallito: {error}</p>}
      {result && (
        <p className="import-result">
          Importate {result.imported} operazioni
          {result.duplicates > 0 ? `, ${result.duplicates} già presenti` : ""}
          {result.skipped.length > 0
            ? `. Ignorati (non in portafoglio): ${result.skipped.map((s) => s.name).join(", ")}`
            : ""}
          .
        </p>
      )}
    </div>
  );
}
