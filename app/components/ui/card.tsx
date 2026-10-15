import Link from "next/link";
import type { ComponentProps, HTMLAttributes } from "react";

type Tone = "default" | "muted" | "accent" | "warm";
type CardProps = HTMLAttributes<HTMLElement> & { as?: "article" | "section" | "aside" | "div"; tone?: Tone };

export function Card({ as: Element = "article", tone = "default", className = "", ...props }: CardProps) {
  return <Element className={`card card--${tone} ${className}`.trim()} {...props} />;
}

export function CardLink({ tone = "default", className = "", ...props }: ComponentProps<typeof Link> & { tone?: Tone }) {
  return <Link className={`card card--${tone} card--interactive ${className}`.trim()} {...props} />;
}
