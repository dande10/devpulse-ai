import { ButtonHTMLAttributes, forwardRef } from "react";

import { cn } from "../../lib/utils";

export const Button = forwardRef<HTMLButtonElement, ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "ghost" | "outline" }>(
  ({ className, variant = "primary", ...props }, ref) => (
    <button
      ref={ref}
      className={cn(
        "inline-flex h-10 items-center justify-center gap-2 rounded-lg px-4 text-sm font-medium transition-all duration-150 active:scale-[0.97] focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary disabled:pointer-events-none disabled:opacity-50",
        variant === "primary" &&
          "bg-gradient-to-br from-primary to-primary-strong text-white shadow-sm hover:shadow-md hover:brightness-110",
        variant === "ghost" && "text-slate-600 hover:bg-muted hover:text-foreground dark:text-slate-300",
        variant === "outline" && "border border-border bg-card hover:border-primary/40 hover:bg-muted",
        className
      )}
      {...props}
    />
  )
);
Button.displayName = "Button";
