import { cn } from "../../lib/cn";

const statusStyles = {
  AVAILABLE:
    "bg-blue-100 text-blue-700 dark:bg-blue-950/60 dark:text-blue-300",

  ACTIVE:
    "bg-emerald-100 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300",

  VERIFIED:
    "bg-emerald-100 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300",

  APPROVED:
    "bg-emerald-100 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300",

  COMPLETED:
    "bg-emerald-100 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300",

  DELIVERED:
    "bg-emerald-100 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300",

  RECEIVED:
    "bg-emerald-100 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300",

  PENDING:
    "bg-amber-100 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300",

  UNDER_REVIEW:
    "bg-amber-100 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300",

  REQUESTED:
    "bg-amber-100 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300",

  ACCEPTED:
    "bg-sky-100 text-sky-700 dark:bg-sky-950/60 dark:text-sky-300",

  CLAIMED:
    "bg-sky-100 text-sky-700 dark:bg-sky-950/60 dark:text-sky-300",

  VOLUNTEER_REQUESTED:
    "bg-sky-100 text-sky-700 dark:bg-sky-950/60 dark:text-sky-300",

  VOLUNTEER_ASSIGNED:
    "bg-blue-100 text-blue-700 dark:bg-blue-950/60 dark:text-blue-300",

  PICKED_UP:
    "bg-indigo-100 text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-300",

  REJECTED:
    "bg-red-100 text-red-700 dark:bg-red-950/60 dark:text-red-300",

  CANCELLED:
    "bg-red-100 text-red-700 dark:bg-red-950/60 dark:text-red-300",

  EXPIRED:
    "bg-red-100 text-red-700 dark:bg-red-950/60 dark:text-red-300",

  FAILED:
    "bg-red-100 text-red-700 dark:bg-red-950/60 dark:text-red-300",

  SUSPENDED:
    "bg-red-100 text-red-700 dark:bg-red-950/60 dark:text-red-300",

  WITHDRAWN:
    "bg-slate-200 text-slate-700 dark:bg-slate-700 dark:text-slate-200",
};

function formatStatus(status) {
  return String(status || "UNKNOWN")
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/\b\w/g, (character) =>
      character.toUpperCase(),
    );
}

export default function StatusBadge({
  status,
  className,
}) {
  const normalizedStatus = String(
    status || "UNKNOWN",
  ).toUpperCase();

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-1",
        "text-xs font-bold tracking-wide",
        statusStyles[normalizedStatus] ||
          "bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-200",
        className,
      )}
    >
      {formatStatus(normalizedStatus)}
    </span>
  );
}