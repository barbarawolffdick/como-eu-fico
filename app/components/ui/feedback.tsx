import type { HTMLAttributes, ReactNode } from "react";

type FeedbackProps = Omit<HTMLAttributes<HTMLDivElement>, "role"> & {
  kind: "loading" | "error" | "empty" | "notice";
  action?: ReactNode;
};

export function Feedback({ kind, action, children, className = "", ...props }: FeedbackProps) {
  return <div {...props} className={`feedback feedback--${kind} ${className}`.trim()}
    role={kind === "error" ? "alert" : kind === "loading" ? "status" : "note"}
    aria-live={kind === "loading" ? "polite" : undefined}>
    {kind === "loading" && <span className="feedback-spinner" aria-hidden="true" />}
    <div className="feedback-content">{children}{action && <div className="feedback-action">{action}</div>}</div>
  </div>;
}
