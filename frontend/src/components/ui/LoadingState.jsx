import { LoaderCircle } from "lucide-react";

import { cn } from "../../lib/cn";

export function Skeleton({
  className,
}) {
  return (
    <div
      aria-hidden="true"
      className={cn(
        "skeleton-shimmer rounded-xl",
        className,
      )}
    />
  );
}

export function CardSkeleton() {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-700 dark:bg-slate-800">
      <Skeleton className="mb-4 h-5 w-2/3" />
      <Skeleton className="mb-2 h-4 w-full" />
      <Skeleton className="mb-6 h-4 w-4/5" />

      <div className="flex gap-3">
        <Skeleton className="h-10 flex-1" />
        <Skeleton className="h-10 w-24" />
      </div>
    </div>
  );
}

export default function LoadingState({
  message = "Loading...",
  fullScreen = false,
}) {
  return (
    <div
      role="status"
      aria-live="polite"
      className={cn(
        "flex items-center justify-center gap-3 text-slate-600 dark:text-slate-300",
        fullScreen
          ? "min-h-screen bg-slate-50 dark:bg-slate-900"
          : "min-h-40",
      )}
    >
      <LoaderCircle
        aria-hidden="true"
        className="size-6 animate-spin text-blue-600"
      />

      <span className="font-medium">
        {message}
      </span>
    </div>
  );
}