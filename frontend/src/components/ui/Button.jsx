import { LoaderCircle } from "lucide-react";
import {
  forwardRef,
} from "react";

import { cn } from "../../lib/cn";

const variants = {
  primary:
    "bg-blue-600 text-white shadow-sm " +
    "hover:bg-blue-700 hover:shadow-lg " +
    "hover:shadow-blue-500/20",

  secondary:
    "border border-slate-200 bg-white text-slate-700 " +
    "hover:border-blue-200 hover:bg-blue-50 " +
    "dark:border-slate-700 dark:bg-slate-800 " +
    "dark:text-slate-100 dark:hover:bg-slate-700",

  danger:
    "bg-red-600 text-white shadow-sm " +
    "hover:bg-red-700",

  ghost:
    "text-slate-600 hover:bg-slate-100 " +
    "hover:text-slate-950 dark:text-slate-300 " +
    "dark:hover:bg-slate-800 dark:hover:text-white",
};

const sizes = {
  sm: "min-h-9 px-3 py-1.5 text-sm",
  md: "min-h-11 px-4 py-2.5 text-sm",
  lg: "min-h-12 px-5 py-3 text-base",
};

const Button = forwardRef(function Button(
  {
    children,
    className,
    variant = "primary",
    size = "md",
    isLoading = false,
    disabled = false,
    type = "button",
    ...props
  },
  ref,
) {
  return (
    <button
      ref={ref}
      type={type}
      disabled={disabled || isLoading}
      className={cn(
        "focus-ring inline-flex items-center justify-center gap-2",
        "rounded-xl font-semibold transition-all duration-200",
        "active:scale-[0.98]",
        "disabled:pointer-events-none disabled:opacity-60",
        variants[variant],
        sizes[size],
        className,
      )}
      {...props}
    >
      {isLoading && (
        <LoaderCircle
          aria-hidden="true"
          className="size-4 animate-spin"
        />
      )}

      {children}
    </button>
  );
});

Button.displayName = "Button";

export default Button;