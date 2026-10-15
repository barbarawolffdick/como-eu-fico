"use client";

import { useEffect, useState } from "react";

export function useResource<T>(url: string, message: string) {
  const [state, setState] = useState<{ url: string; data: T | null; error: string }>({ url, data: null, error: "" });
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    setState({ url, data: null, error: "" });
    fetch(url, { signal: controller.signal, cache: "no-store" })
      .then(async response => {
        if (!response.ok) throw Error(message);
        return response.json() as Promise<T>;
      })
      .then(data => { if (!controller.signal.aborted) setState({ url, data, error: "" }); })
      .catch(() => { if (!controller.signal.aborted) setState({ url, data: null, error: message }); });
    return () => controller.abort();
  }, [url, message, attempt]);
  return { data: state.url === url ? state.data : null, error: state.url === url ? state.error : "", retry: () => setAttempt(value => value + 1) };
}
