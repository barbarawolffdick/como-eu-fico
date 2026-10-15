"use client";

import { useEffect, useId, useRef, useState, type ReactNode } from "react";
import { createPortal } from "react-dom";
import { CircleHelp, X } from "lucide-react";
import { Button } from "./button";

export default function HelpDialog({ term, children }: { term: string; children: ReactNode }) {
  const [open, setOpen] = useState(false);
  const trigger = useRef<HTMLButtonElement>(null);
  const dialog = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  useEffect(() => {
    if (!open || !dialog.current) return;
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    dialog.current.showModal();
    const button = trigger.current;
    return () => { document.body.style.overflow = previous; button?.focus(); };
  }, [open]);
  return <span className="term-help">
    <Button ref={trigger} variant="quiet" size="compact" aria-label={"Entender: " + term}
      aria-haspopup="dialog" aria-expanded={open} onClick={() => setOpen(true)}>
      <CircleHelp size={16} aria-hidden="true" />
    </Button>
    {open && createPortal(<dialog ref={dialog} className="help-dialog" aria-labelledby={titleId}
      onClose={() => setOpen(false)} onCancel={() => setOpen(false)}
      onClick={event => {
        if (event.target !== event.currentTarget) return;
        const box = event.currentTarget.getBoundingClientRect();
        if (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom) setOpen(false);
      }}>
      <header className="help-dialog-heading"><h2 id={titleId}>{term}</h2>
        <Button variant="quiet" size="icon" aria-label="Fechar explicação" onClick={() => setOpen(false)}><X size={20} aria-hidden="true" /></Button>
      </header>
      <div className="help-dialog-body">{typeof children === "string" ? <p>{children}</p> : children}</div>
    </dialog>, document.body)}
  </span>;
}
