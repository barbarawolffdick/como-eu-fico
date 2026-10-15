import type { HTMLAttributes } from "react";

type DataBarProps = Omit<HTMLAttributes<HTMLDivElement>, "children"> & { value: number; max?: number; label?: string };

export function DataBar({ value, max = 100, label, className = "", ...props }: DataBarProps) {
  const width = Number.isFinite(value) && Number.isFinite(max) && max > 0 ? Math.min(100, Math.max(0, value / max * 100)) : 0;
  return <div {...props} className={`data-bar ${className}`.trim()} role={label ? "img" : undefined} aria-label={label} aria-hidden={label ? undefined : true}>
    <span style={{ width: `${width}%` }} />
  </div>;
}
