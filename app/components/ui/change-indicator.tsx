type ChangeIndicatorProps = { value: number | null; variant?: "badge" | "inline" };

export function ChangeIndicator({ value, variant = "badge" }: ChangeIndicatorProps) {
  const direction = value == null ? "unavailable" : value > 0 ? "up" : value < 0 ? "down" : "flat";
  const formatted = value == null ? "" : Math.abs(value).toLocaleString("pt-BR", { maximumFractionDigits: 2 }) + "%";
  const label = value == null ? "Comparação indisponível" : value === 0 ? "Mesmo valor nos dois anos" : `${value > 0 ? "Aumentou" : "Diminuiu"} ${formatted}`;
  return <span className={`change-indicator change-indicator--${variant} change-${direction}`}>
    <span aria-hidden="true">{value == null ? "—" : value > 0 ? "↑" : value < 0 ? "↓" : "="}</span>
    {variant === "badge" ? <strong>{label}</strong> : <><span className="sr-only">{label}: </span><strong>{value == null ? "Indisponível" : `${value > 0 ? "+" : value < 0 ? "−" : ""}${formatted}`}</strong></>}
  </span>;
}
