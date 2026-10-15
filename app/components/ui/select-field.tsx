"use client";

import { useId, type ReactNode, type SelectHTMLAttributes } from "react";

type SelectFieldProps = SelectHTMLAttributes<HTMLSelectElement> & { label: ReactNode; hint?: string; error?: string };

export function SelectField({ label, hint, error, id, className = "", "aria-describedby": describedBy, ...props }: SelectFieldProps) {
  const generatedId = useId();
  const fieldId = id ?? generatedId;
  const descriptions = [describedBy, hint && `${fieldId}-hint`, error && `${fieldId}-error`].filter(Boolean).join(" ") || undefined;
  return <div className="field">
    <label className="field-label" htmlFor={fieldId}>{label}</label>
    <select {...props} id={fieldId} className={`select ${className}`.trim()} aria-describedby={descriptions} aria-invalid={error ? true : props["aria-invalid"]} />
    {hint && <p className="field-hint" id={`${fieldId}-hint`}>{hint}</p>}
    {error && <p className="field-error" id={`${fieldId}-error`} role="alert">{error}</p>}
  </div>;
}
