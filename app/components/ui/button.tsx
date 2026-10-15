import Link from "next/link";
import type { ComponentProps } from "react";

type ActionVariant = "primary" | "secondary" | "quiet";
type ActionSize = "default" | "compact" | "icon";
type Presentation = { variant?: ActionVariant; size?: ActionSize };

export function Button({ variant = "secondary", size = "default", className = "", type = "button", ...props }: ComponentProps<"button"> & Presentation) {
  return <button type={type} className={`button button--${variant} button--${size} ${className}`.trim()} {...props} />;
}

// Navigation remains a link: no polymorphic button or simulated disabled anchor.
export function ActionLink({ variant = "quiet", size = "default", className = "", ...props }: ComponentProps<typeof Link> & Presentation) {
  return <Link className={`action-link button--${variant} button--${size} ${className}`.trim()} {...props} />;
}
