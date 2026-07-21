/** Small hoverable "ⓘ" that reveals an explanatory tooltip. Pure CSS
 * hover (see .infotip in App.css) — no JS state, works inline next to a
 * label or table header. */
export function InfoTip({ text }: { text: string }) {
  return (
    <span className="infotip" tabIndex={0}>
      <span className="infotip-icon" aria-hidden="true">
        ⓘ
      </span>
      <span className="infotip-bubble" role="tooltip">
        {text}
      </span>
    </span>
  );
}
