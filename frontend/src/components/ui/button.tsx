import { ButtonHTMLAttributes, forwardRef } from "react";

import { cn } from "../../lib/utils";

export const Button = forwardRef<HTMLButtonElement, ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "ghost" | "outline" }>(
  ({ className, variant = "primary", ...props }, ref) => (
    <button
      ref={ref}
      className={cn(
        "inline-flex h-10 items-center justify-center gap-2 rounded-md px-3 text-sm font-medium transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary disabled:cursor-not-allowed disabled:opacity-50",
        variant === "primary" && "bg-primary text-white hover:opacity-90",
        variant === "ghost" && "hover:bg-muted",
        variant === "outline" && "border border-border bg-card hover:bg-muted",
        className
      )}
      {...props}
    />
  )
);
Button.displayName = "Button";
