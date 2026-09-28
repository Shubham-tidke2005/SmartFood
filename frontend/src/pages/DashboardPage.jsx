import {
  AlertTriangle,
  ArrowRight,
  BarChart3,
  CheckCircle2,
  Clock3,
  Package,
  RefreshCw,
  Scale,
  Users,
} from "lucide-react";

import { Link } from "react-router-dom";
import { motion } from "motion/react";

import useAuth from "../auth/useAuth";
import {
  useApiResource,
} from "../hooks/useApiResource";

import Button from "../components/ui/Button";
import {
  ErrorMessage,
} from "../components/ui/FeedbackStates";
import LoadingState from "../components/ui/LoadingState";
import StatusBadge from "../components/ui/StatusBadge";


const roleContent = {
  DONOR: {
    title: "Donor dashboard",
    description:
      "Track listings, completed donations and confirmed impact.",
    actionLabel: "Create donation",
    actionPath: "/donor/donations/new",
  },

  RECEIVER: {
    title: "Receiver dashboard",
    description:
      "Track requests, approvals and pending collections.",
    actionLabel: "Browse donations",
    actionPath: "/receiver/donations",
  },

  VOLUNTEER: {
    title: "Volunteer dashboard",
    description:
      "Track accepted tasks, deliveries and task outcomes.",
    actionLabel: "Browse tasks",
    actionPath: "/volunteer/tasks",
  },

  ADMIN: {
    title: "Administration dashboard",
    description:
      "Monitor participation, outcomes and operational performance.",
    actionLabel: "Review participants",
    actionPath: "/admin/verifications",
  },
};


const roleMetrics = {
  DONOR: [
    {
      label: "Listings created",
      key: "listings_created",
      icon: Package,
      color: "blue",
    },
    {
      label: "Completed",
      key: "completed_donations",
      icon: CheckCircle2,
      color: "emerald",
    },
    {
      label: "Cancelled",
      key: "cancelled_donations",
      icon: AlertTriangle,
      color: "red",
    },
    {
      label: "Expired",
      key: "expired_donations",
      icon: Clock3,
      color: "amber",
    },
  ],

  RECEIVER: [
    {
      label: "Requests submitted",
      key: "requests_submitted",
      icon: Package,
      color: "blue",
    },
    {
      label: "Approved donations",
      key: "approved_donations",
      icon: CheckCircle2,
      color: "emerald",
    },
    {
      label: "Received",
      key: "donations_received",
      icon: Scale,
      color: "sky",
    },
    {
      label: "Pending collections",
      key: "pending_collections",
      icon: Clock3,
      color: "amber",
    },
  ],

  VOLUNTEER: [
    {
      label: "Tasks accepted",
      key: "tasks_accepted",
      icon: Package,
      color: "blue",
    },
    {
      label: "Deliveries recorded",
      key: "deliveries_recorded",
      icon: CheckCircle2,
      color: "emerald",
    },
    {
      label: "Failed tasks",
      key: "failed_tasks",
      icon: AlertTriangle,
      color: "red",
    },
    {
      label: "Cancelled tasks",
      key: "cancelled_tasks",
      icon: Clock3,
      color: "amber",
    },
  ],

  ADMIN: [
    {
      label: "Active participants",
      key: "active_participants",
      icon: Users,
      color: "blue",
    },
    {
      label: "Completed donations",
      key: "completed_donations",
      icon: CheckCircle2,
      color: "emerald",
    },
    {
      label: "Average approval",
      key: "average_approval_hours",
      icon: Clock3,
      color: "amber",
      format: "hours",
    },
    {
      label: "Average pickup",
      key: "average_pickup_hours",
      icon: Clock3,
      color: "sky",
      format: "hours",
    },
    {
      label: "Open complaints",
      key: "open_complaints",
      icon: AlertTriangle,
      color: "red",
    },
    {
      label: "Completion rate",
      key: "completion_rate",
      icon: BarChart3,
      color: "emerald",
      format: "percent",
    },
  ],
};


const colorClasses = {
  blue:
    "bg-blue-100 text-blue-700 dark:bg-blue-950/50 dark:text-blue-300",

  sky:
    "bg-sky-100 text-sky-700 dark:bg-sky-950/50 dark:text-sky-300",

  emerald:
    "bg-emerald-100 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300",

  amber:
    "bg-amber-100 text-amber-700 dark:bg-amber-950/50 dark:text-amber-300",

  red:
    "bg-red-100 text-red-700 dark:bg-red-950/50 dark:text-red-300",
};


function formatNumber(value) {
  return Number(
    value || 0,
  ).toLocaleString(
    "en-IN",
    {
      maximumFractionDigits: 3,
    },
  );
}


function formatMetric(
  value,
  format,
) {
  if (format === "percent") {
    return `${Number(
      value || 0,
    ).toFixed(1)}%`;
  }

  if (format === "hours") {
    return `${Number(
      value || 0,
    ).toFixed(2)} h`;
  }

  return formatNumber(value);
}


function formatLabel(value) {
  return String(value || "")
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(
      /\b\w/g,
      (letter) =>
        letter.toUpperCase(),
    );
}


function MetricCard({
  definition,
  value,
  index,
}) {
  const Icon = definition.icon;

  return (
    <motion.article
      className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm transition-all duration-200 hover:-translate-y-1 hover:shadow-xl hover:shadow-blue-500/5 dark:border-slate-700/60 dark:bg-slate-800"
      initial={{
        opacity: 0,
        y: 14,
      }}
      animate={{
        opacity: 1,
        y: 0,
      }}
      transition={{
        delay: index * 0.04,
      }}
    >
      <div
        className={`flex size-11 items-center justify-center rounded-2xl ${
          colorClasses[
            definition.color
          ]
        }`}
      >
        <Icon
          aria-hidden="true"
          className="size-5"
        />
      </div>

      <p className="mt-5 text-sm font-semibold text-slate-500 dark:text-slate-400">
        {definition.label}
      </p>

      <p className="mt-1 text-3xl font-black text-slate-950 dark:text-white">
        {formatMetric(
          value,
          definition.format,
        )}
      </p>
    </motion.article>
  );
}


function QuantityImpact({
  values = [],
}) {
  return (
    <section className="mt-6 rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-800">
      <div className="flex items-start gap-3">
        <div className="flex size-11 shrink-0 items-center justify-center rounded-2xl bg-emerald-100 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300">
          <Scale
            aria-hidden="true"
            className="size-5"
          />
        </div>

        <div>
          <h2 className="text-xl font-black text-slate-950 dark:text-white">
            Confirmed redistribution impact
          </h2>

          <p className="mt-1 text-sm leading-6 text-slate-500 dark:text-slate-400">
            Calculated only from receiver-confirmed
            accepted quantities. Units are never added
            together.
          </p>
        </div>
      </div>

      {values.length ? (
        <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {values.map((item) => (
            <article
              key={item.unit}
              className="rounded-2xl border border-emerald-200 bg-emerald-50 p-5 dark:border-emerald-500/30 dark:bg-emerald-500/10"
            >
              <p className="text-2xl font-black text-emerald-800 dark:text-emerald-200">
                {formatNumber(
                  item.quantity,
                )}
              </p>

              <p className="mt-1 text-sm font-bold text-emerald-700 dark:text-emerald-300">
                {formatLabel(
                  item.unit,
                )}
              </p>
            </article>
          ))}
        </div>
      ) : (
        <p className="mt-5 rounded-2xl border border-dashed border-slate-300 p-6 text-center text-sm text-slate-500 dark:border-slate-700 dark:text-slate-400">
          No receiver-confirmed quantities are available
          yet.
        </p>
      )}
    </section>
  );
}


function OutcomeBreakdown({
  values = [],
}) {
  if (!values.length) {
    return null;
  }

  return (
    <section className="mt-6 rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-800">
      <h2 className="text-xl font-black text-slate-950 dark:text-white">
        Outcome breakdown
      </h2>

      <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {values.map((item) => (
          <div
            key={item.status}
            className="flex items-center justify-between rounded-xl bg-slate-50 p-4 dark:bg-slate-900/50"
          >
            <span className="text-sm font-semibold text-slate-600 dark:text-slate-300">
              {formatLabel(
                item.status,
              )}
            </span>

            <span className="text-lg font-black text-slate-950 dark:text-white">
              {formatNumber(
                item.count,
              )}
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}


export default function DashboardPage() {
  const { user } = useAuth();

  const {
    data: analytics,
    loading,
    error,
    reload,
  } = useApiResource(
    "/analytics/",
  );

  const role =
    user?.role?.toUpperCase()
    || "DONOR";

  const content =
    roleContent[role]
    || roleContent.DONOR;

  const definitions =
    roleMetrics[role]
    || roleMetrics.DONOR;

  const summary =
    analytics?.summary
    || {};

  const accountSuspended =
    user?.is_active === false;

  return (
    <div>
      <section className="overflow-hidden rounded-3xl bg-gradient-to-br from-slate-950 via-slate-900 to-blue-950 p-6 text-white shadow-xl sm:p-8">
        <div className="flex flex-col gap-6 md:flex-row md:items-end md:justify-between">
          <div>
            <div className="mb-4 flex flex-wrap gap-2">
              <StatusBadge
                status={role}
              />

              <StatusBadge
                status={
                  user?.verification_status
                  || "PENDING"
                }
              />

              <StatusBadge
                status={
                  accountSuspended
                    ? "SUSPENDED"
                    : "ACTIVE"
                }
              />
            </div>

            <p className="text-sm font-semibold text-sky-300">
              Welcome back
            </p>

            <h1 className="mt-2 text-3xl font-black tracking-tight sm:text-4xl">
              {user?.display_name
                || user?.name
                || "SmartFood participant"}
            </h1>

            <h2 className="mt-4 text-lg font-bold">
              {content.title}
            </h2>

            <p className="mt-2 max-w-2xl text-slate-300">
              {content.description}
            </p>
          </div>

          <div className="flex flex-col gap-3 sm:flex-row">
            <Button
              variant="secondary"
              onClick={reload}
            >
              <RefreshCw
                aria-hidden="true"
                className="size-4"
              />

              Refresh
            </Button>

            {!accountSuspended && (
              <Link
                to={content.actionPath}
                className="focus-ring inline-flex min-h-11 items-center justify-center gap-2 rounded-xl bg-blue-600 px-5 py-2.5 font-bold text-white transition hover:-translate-y-0.5 hover:bg-blue-700 active:scale-[0.98]"
              >
                {content.actionLabel}

                <ArrowRight
                  aria-hidden="true"
                  className="size-4"
                />
              </Link>
            )}
          </div>
        </div>
      </section>

      {accountSuspended && (
        <div
          role="alert"
          className="mt-5 rounded-2xl border border-red-200 bg-red-50 p-4 text-red-700 dark:border-red-900 dark:bg-red-950/40 dark:text-red-300"
        >
          Your account is suspended. Existing records
          remain visible, but protected operations are
          unavailable.
        </div>
      )}

      {loading && (
        <div className="mt-6">
          <LoadingState
            message={
              "Loading dashboard analytics..."
            }
          />
        </div>
      )}

      {!loading && error && (
        <div className="mt-6">
          <ErrorMessage
            message={error}
            onRetry={reload}
          />
        </div>
      )}

      {!loading && !error && (
        <>
          <section
            aria-label="Dashboard metrics"
            className="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4"
          >
            {definitions.map(
              (
                definition,
                index,
              ) => (
                <MetricCard
                  key={definition.key}
                  definition={definition}
                  value={
                    summary[
                      definition.key
                    ]
                  }
                  index={index}
                />
              ),
            )}
          </section>

          <QuantityImpact
            values={
              analytics
                ?.quantity_redistributed
              || []
            }
          />

          <OutcomeBreakdown
            values={
              analytics
                ?.status_breakdown
              || []
            }
          />
        </>
      )}
    </div>
  );
}