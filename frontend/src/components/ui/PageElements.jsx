import {
  ArrowRight,
  CalendarClock,
  MapPin,
  Package,
  Scale,
} from "lucide-react";

import {
  Link,
} from "react-router-dom";

import {
  motion,
} from "motion/react";

import {
  cn,
} from "../../lib/cn";

import Button from "./Button";

import {
  EmptyState,
  ErrorMessage,
} from "./FeedbackStates";

import {
  CardSkeleton,
} from "./LoadingState";

import StatusBadge from "./StatusBadge";


function getRevision(item) {
  return (
    item?.current_revision ||
    item?.revision ||
    item ||
    {}
  );
}


function itemTitle(item) {
  const revision =
    getRevision(item);

  return (
    revision.food_name ||
    item?.category_name ||
    item?.category?.name ||
    (
      typeof item?.category ===
      "string"
        ? item.category
        : null
    ) ||
    item?.title ||
    item?.organization_name ||
    item?.display_name ||
    item?.name ||
    item?.task_number ||
    item?.email ||
    "SmartFood record"
  );
}


function itemDescription(item) {
  const revision =
    getRevision(item);

  return (
    revision.description ||
    item?.message ||
    item?.reason ||
    item?.email ||
    revision.pickup_area ||
    "No additional description"
  );
}


function formatDate(value) {
  if (!value) {
    return "";
  }

  const date = new Date(value);

  return Number.isNaN(
    date.getTime(),
  )
    ? ""
    : date.toLocaleString();
}


export function PageHeader({
  eyebrow,
  title,
  description,
  action,
}) {
  return (
    <header className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div>
        {eyebrow && (
          <p className="text-sm font-bold uppercase tracking-wider text-blue-600 dark:text-blue-400">
            {eyebrow}
          </p>
        )}

        <h1 className="mt-1 text-3xl font-black tracking-tight text-slate-950 dark:text-white">
          {title}
        </h1>

        {description && (
          <p className="mt-2 max-w-3xl leading-7 text-slate-500 dark:text-slate-400">
            {description}
          </p>
        )}
      </div>

      {action}
    </header>
  );
}


export function Surface({
  children,
  className,
}) {
  return (
    <section
      className={cn(
        "rounded-2xl border border-slate-200/80",
        "bg-white p-5 shadow-sm",
        "dark:border-slate-700/60 dark:bg-slate-800",
        className,
      )}
    >
      {children}
    </section>
  );
}


export function MetricCard({
  label,
  value,
  icon: Icon = Package,
  color = "blue",
}) {
  const colors = {
    blue:
      "bg-blue-100 text-blue-700 dark:bg-blue-950/50 dark:text-blue-300",

    emerald:
      "bg-emerald-100 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300",

    amber:
      "bg-amber-100 text-amber-700 dark:bg-amber-950/50 dark:text-amber-300",

    red:
      "bg-red-100 text-red-700 dark:bg-red-950/50 dark:text-red-300",
  };

  return (
    <Surface className="transition-all duration-200 hover:-translate-y-1 hover:shadow-xl hover:shadow-blue-500/5">
      <div
        className={cn(
          "flex size-11 items-center justify-center rounded-2xl",
          colors[color] ||
            colors.blue,
        )}
      >
        <Icon
          aria-hidden="true"
          className="size-5"
        />
      </div>

      <p className="mt-4 text-sm font-semibold text-slate-500 dark:text-slate-400">
        {label}
      </p>

      <p className="mt-1 text-3xl font-black text-slate-950 dark:text-white">
        {value ?? 0}
      </p>
    </Surface>
  );
}


export function ResourceCard({
  item,
  detailPath,
  actions,
}) {
  const revision =
    getRevision(item);

  const status =
    item?.status ||
    item?.verification_status ||
    item?.task_status ||
    (
      typeof item?.active ===
      "boolean"
        ? item.active
          ? "ACTIVE"
          : "INACTIVE"
        : null
    );

  const deadline =
    revision.pickup_deadline ||
    item?.needed_until ||
    item?.created_at;

  const location =
    revision.pickup_area ||
    revision.pickup_location ||
    item?.location ||
    item?.address;

  const quantity =
    revision.quantity ??
    item?.remaining_quantity ??
    item?.quantity_remaining ??
    item?.quantity_needed;

  const unit =
    revision.unit ||
    item?.unit ||
    "";

  const formattedDeadline =
    formatDate(deadline);

  const content = (
    <motion.article
      whileHover={{
        y: -4,
      }}
      transition={{
        duration: 0.18,
      }}
      className="h-full rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm transition-shadow hover:shadow-xl hover:shadow-blue-500/5 dark:border-slate-700/60 dark:bg-slate-800"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex size-11 shrink-0 items-center justify-center rounded-2xl bg-blue-100 text-blue-700 dark:bg-blue-950/50 dark:text-blue-300">
          <Package
            aria-hidden="true"
            className="size-5"
          />
        </div>

        {status && (
          <StatusBadge
            status={status}
          />
        )}
      </div>

      <h2 className="mt-4 line-clamp-2 text-lg font-black text-slate-950 dark:text-white">
        {itemTitle(item)}
      </h2>

      <p className="mt-2 line-clamp-2 text-sm leading-6 text-slate-500 dark:text-slate-400">
        {itemDescription(item)}
      </p>

      <div className="mt-4 space-y-2 text-sm text-slate-600 dark:text-slate-300">
        {quantity != null && (
          <p className="flex items-center gap-2 font-semibold">
            <Scale
              aria-hidden="true"
              className="size-4 text-emerald-500"
            />

            {quantity} {unit}
          </p>
        )}

        {location && (
          <p className="flex items-center gap-2">
            <MapPin
              aria-hidden="true"
              className="size-4 text-sky-500"
            />

            <span className="line-clamp-1">
              {location}
            </span>
          </p>
        )}

        {formattedDeadline && (
          <p className="flex items-center gap-2">
            <CalendarClock
              aria-hidden="true"
              className="size-4 text-amber-500"
            />

            {formattedDeadline}
          </p>
        )}
      </div>

      {actions && (
        <div
          className="mt-5"
          onClick={(event) =>
            event.preventDefault()
          }
        >
          {actions}
        </div>
      )}

      {detailPath && (
        <div className="mt-5 flex items-center gap-2 text-sm font-bold text-blue-600 dark:text-blue-400">
          View details

          <ArrowRight
            aria-hidden="true"
            className="size-4"
          />
        </div>
      )}
    </motion.article>
  );

  if (!detailPath) {
    return content;
  }

  return (
    <Link
      to={detailPath}
      className="focus-ring block rounded-2xl"
    >
      {content}
    </Link>
  );
}


export function ResourceGrid({
  items,
  loading,
  error,
  onRetry,
  emptyTitle,
  emptyDescription,
  getDetailPath,
  renderActions,
}) {
  if (loading) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {Array.from({
          length: 6,
        }).map((_, index) => (
          <CardSkeleton
            key={index}
          />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <ErrorMessage
        message={error}
        onRetry={onRetry}
      />
    );
  }

  const safeItems =
    Array.isArray(items)
      ? items
      : [];

  if (!safeItems.length) {
    return (
      <EmptyState
        title={emptyTitle}
        description={
          emptyDescription
        }
      />
    );
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
      {safeItems.map(
        (item, index) => (
          <ResourceCard
            key={
              item.id ||
              item.uuid ||
              index
            }
            item={item}
            detailPath={
              getDetailPath
                ? getDetailPath(item)
                : null
            }
            actions={
              renderActions
                ? renderActions(item)
                : null
            }
          />
        ),
      )}
    </div>
  );
}


export function SubmitBar({
  submitLabel,
  isSubmitting,
  cancelPath,
}) {
  return (
    <div className="flex flex-col-reverse gap-3 border-t border-slate-200 pt-5 dark:border-slate-700 sm:flex-row sm:justify-end">
      {cancelPath && (
        <Link
          to={cancelPath}
          className="focus-ring inline-flex min-h-11 items-center justify-center rounded-xl border border-slate-300 px-4 py-2.5 font-semibold text-slate-700 hover:bg-slate-50 dark:border-slate-600 dark:text-slate-200 dark:hover:bg-slate-700"
        >
          Cancel
        </Link>
      )}

      <Button
        type="submit"
        isLoading={isSubmitting}
      >
        {submitLabel}
      </Button>
    </div>
  );
}