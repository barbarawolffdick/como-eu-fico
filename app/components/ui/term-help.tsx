"use client";

import { Children, isValidElement, useEffect, useId, useLayoutEffect, useRef, useState, type ReactNode } from "react";
import { createPortal } from "react-dom";
import { Button } from "./button";
import { CircleHelp } from "lucide-react";
import HelpDialog from "./help-dialog";

function tamanho(node: ReactNode): number {
  return Children.toArray(node).reduce<number>((total, child) => total + (typeof child === "string" ? child.length
    : isValidElement<{ children?: ReactNode }>(child) ? tamanho(child.props.children) : 0), 0);
}

export default function TermHelp({ term, children, presentation = "auto" }: { term: string; children: ReactNode; presentation?: "auto" | "tooltip" | "dialog" }) {
  return presentation === "dialog" || (presentation === "auto" && tamanho(children) > 160)
    ? <HelpDialog term={term}>{children}</HelpDialog> : <TooltipHelp term={term}>{children}</TooltipHelp>;
}

function TooltipHelp({ term, children }: { term: string; children: ReactNode }) {
  const id = useId();
  const root = useRef<HTMLSpanElement>(null);
  const bubble = useRef<HTMLSpanElement>(null);
  const leaveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [position, setPosition] = useState({ left: 0, top: 0 });
  const [hovered, setHovered] = useState(false);
  const [focused, setFocused] = useState(false);
  const [pinned, setPinned] = useState(false);
  const [dismissed, setDismissed] = useState(false);
  const open = !dismissed && (hovered || focused || pinned);

  useEffect(() => () => { if (leaveTimer.current) clearTimeout(leaveTimer.current); }, []);

  useLayoutEffect(() => {
    if (!open) return;
    function place() {
      const anchor = root.current?.getBoundingClientRect();
      const box = bubble.current?.getBoundingClientRect();
      if (!anchor || !box) return;
      const gutter = parseFloat(getComputedStyle(bubble.current!).paddingLeft);
      const gap = parseFloat(getComputedStyle(root.current!).columnGap) || 8;
      const left = Math.max(gutter, Math.min(anchor.left, window.innerWidth - box.width - gutter));
      const below = anchor.bottom + gap;
      const top = below + box.height <= window.innerHeight - gutter ? below : Math.max(gutter, anchor.top - box.height - gap);
      setPosition({ left, top });
    }
    place();
    window.addEventListener("resize", place);
    window.addEventListener("scroll", place, true);
    return () => { window.removeEventListener("resize", place); window.removeEventListener("scroll", place, true); };
  }, [open]);

  useEffect(() => {
    if (!open) return;
    function dismiss(event: KeyboardEvent) {
      if (event.key === "Escape") { setDismissed(true); setPinned(false); }
    }
    function outside(event: PointerEvent) {
      if (!root.current?.contains(event.target as Node) && !bubble.current?.contains(event.target as Node)) {
        setPinned(false); setFocused(false); setHovered(false);
      }
    }
    document.addEventListener("keydown", dismiss);
    document.addEventListener("pointerdown", outside);
    return () => {
      document.removeEventListener("keydown", dismiss);
      document.removeEventListener("pointerdown", outside);
    };
  }, [open]);

  return <span className="term-help" ref={root}
    onMouseEnter={() => { if (leaveTimer.current) clearTimeout(leaveTimer.current); setHovered(true); setDismissed(false); }}
    onMouseLeave={() => { leaveTimer.current = setTimeout(() => setHovered(false), parseFloat(getComputedStyle(root.current!).getPropertyValue("--motion-tooltip-close"))); }}>
    <Button variant="quiet" size="compact" aria-label={"Entender: " + term} aria-expanded={open}
      aria-describedby={open ? id : undefined}
      onFocus={() => { setFocused(true); setDismissed(false); }}
      onBlur={() => { setFocused(false); setPinned(false); }}
      onClick={() => {
        if (pinned) { setPinned(false); setDismissed(true); }
        else { setPinned(true); setDismissed(false); }
      }}><CircleHelp size={16} aria-hidden="true" /></Button>
    {open && createPortal(<span className="help-bubble" ref={bubble} id={id} role="tooltip" style={position}>{children}</span>, document.body)}
  </span>;
}
