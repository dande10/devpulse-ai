import { InputHTMLAttributes, forwardRef } from "react";

import { cn } from "../../lib/utils";

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(({ className, ...props }, ref) => (
  <input
    ref={ref}
    className={cn(
      "h-12 w-full rounded-lg border border-border bg-card px-4 text-sm text-foreground shadow-sm outline-none transition-shadow placeholder:text-slate-400 focus-visible:border-primary/50 focus-visible:shadow-glow",
      className
    )}
    {...props}
  />
));
Input.displayName = "Input";
