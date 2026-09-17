import { useState } from "react";

import { requestTechnology } from "../services/api";

export function RequestTechnologyModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [name, setName] = useState("");
  const [state, setState] = useState<"idle" | "sending" | "sent" | "error">("idle");

  if (!open) return null;

  const submit = async () => {
    const trimmed = name.trim();
    if (!trimmed) return;
    setState("sending");
    try {
      await requestTechnology(trimmed);
      setState("sent");
    } catch {
      setState("error");
    }
  };

  return (
    <div
      className="modalbackdrop"
      onClick={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <section
        className="panel modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="request-title"
        onKeyDown={(event) => {
          if (event.key === "Escape") onClose();
        }}
      >
        <div className="sectionline">
          <h2 id="request-title">Request a technology</h2>
          <button aria-label="Close" className="outline" onClick={onClose}>
            &times;
          </button>
        </div>
        <p>Tell us what you&rsquo;d like DevPulse to start tracking &mdash; a real person reviews every request.</p>
        <label>
          Technology name
          <input
            autoFocus
            value={name}
            onChange={(event) => {
              setName(event.target.value);
              setState("idle");
            }}
            placeholder="e.g. Spring Boot"
          />
        </label>
        <button className="primary" disabled={!name.trim() || state === "sending"} onClick={submit}>
          {state === "sending" ? "Sending…" : "Send request"}
        </button>
        <p aria-live="polite">
          {state === "sent" && "Request sent. Thanks for the suggestion!"}
          {state === "error" && "Couldn't send that request. Please try again."}
        </p>
      </section>
    </div>
  );
}
