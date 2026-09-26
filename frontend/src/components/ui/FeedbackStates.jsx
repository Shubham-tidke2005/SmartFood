import {
  AlertTriangle,
  Inbox,
  RefreshCw,
} from "lucide-react";

import Button from "./Button";

export function ErrorMessage({
  message,
  onRetry,
}) {
  return (
    <div
      role="alert"
      className="rounded-2xl border border-red-200 bg-red-50 p-5 text-red-800 dark:border-red-900/70 dark:bg-red-950/40 dark:text-red-200"
    >
      <div className="flex items-start gap-3">
        <AlertTriangle
          aria-hidden="true"
          className="mt-0.5 size-5 shrink-0"
        />

        <div className="min-w-0 flex-1">
          <h2 className="font-semibold">
            Something went wrong
          </h2>

          <p className="mt-1 text-sm">
            {message}
          </p>

          {onRetry && (
            <Button
              variant="secondary"
              size="sm"
              className="mt-4"
              onClick={onRetry}
            >
              <RefreshCw
                aria-hidden="true"
                className="size-4"
              />

              Try again
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}

export function EmptyState({
  title = "Nothing here yet",
  description,
  action,
  icon: Icon = Inbox,
}) {
  return (
    <div className="rounded-2xl border border-dashed border-slate-300 bg-white px-6 py-12 text-center dark:border-slate-700 dark:bg-slate-800">
      <div className="mx-auto flex size-12 items-center justify-center rounded-2xl bg-blue-50 text-blue-600 dark:bg-blue-950/50 dark:text-blue-300">
        <Icon
          aria-hidden="true"
          className="size-6"
        />
      </div>

      <h2 className="mt-4 text-lg font-bold text-slate-950 dark:text-white">
        {title}
      </h2>

      {description && (
        <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-slate-500 dark:text-slate-400">
          {description}
        </p>
      )}

      {action && (
        <div className="mt-5">
          {action}
        </div>
      )}
    </div>
  );
}