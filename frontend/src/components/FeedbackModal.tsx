import { useState } from "react";

import { submitFeedback } from "../services/api";

export function FeedbackModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [rating, setRating] = useState(0);
  const [message, setMessage] = useState("");
  const [state, setState] = useState<"idle" | "sending" | "sent" | "error">("idle");

  if (!open) return null;

  const submit = async () => {
    const trimmed = message.trim();
    if (!trimmed) return;
    setState("sending");
    try {
      await submitFeedback({
        name: name.trim() || undefined,
        email: email.trim() || undefined,
        rating: rating || undefined,
        message: trimmed,
      });
      setState("sent");
      setMessage("");
      setRating(0);
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
        aria-labelledby="feedback-title"
        onKeyDown={(event) => {
          if (event.key === "Escape") onClose();
        }}
      >
        <div className="sectionline">
          <h2 id="feedback-title">Leave a review</h2>
          <button aria-label="Close" className="outline" onClick={onClose}>
            &times;
          </button>
        </div>
        <p>Tell us what you think of DevPulse &mdash; reviews are moderated before being shared.</p>

        <div className="chips stars" aria-label="Rating">
          {[1, 2, 3, 4, 5].map((value) => (
            <button
              key={value}
              type="button"
              aria-pressed={rating === value}
              aria-label={`${value} star${value === 1 ? "" : "s"}`}
              className={`chip star ${rating >= value ? "filled" : ""}`}
              onClick={() => setRating(value)}
            >
              &#9733;
            </button>
          ))}
        </div>

        <label>
          Name (optional)
          <input value={name} onChange={(event) => setName(event.target.value)} placeholder="Your name" />
        </label>
        <label>
          Email (optional)
          <input type="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="you@example.com" />
        </label>
        <label>
          Your review
          <input
            value={message}
            onChange={(event) => {
              setMessage(event.target.value);
              setState("idle");
            }}
            placeholder="What's working, what's not?"
          />
        </label>
        <button className="primary" disabled={!message.trim() || state === "sending"} onClick={submit}>
          {state === "sending" ? "Sending…" : "Submit review"}
        </button>
        <p aria-live="polite">
          {state === "sent" && "Thanks — your review was submitted."}
          {state === "error" && "Couldn't submit that. Please try again."}
        </p>
      </section>
    </div>
  );
}
