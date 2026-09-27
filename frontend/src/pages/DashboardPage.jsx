import {
  ArrowRight,
  BarChart3,
  CheckCircle2,
  Clock3,
  HeartHandshake,
  Package,
  RefreshCw,
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
      "Create donations and coordinate receiver requests.",
    actionLabel: "Create donation",
    actionPath: "/donor/donations/new",
  },

  RECEIVER: {
    title: "Receiver dashboard",
    description:
      "Find compatible food donations for your organization.",
    actionLabel: "Discover donations",
    actionPath: "/receiver/donations",
  },

  VOLUNTEER: {
    title: "Volunteer dashboard",
    description:
      "Find eligible pickup and delivery tasks.",
    actionLabel: "Browse tasks",
    actionPath: "/volunteer/tasks",
  },

  ADMIN: {
    title: "Administration dashboard",
    description:
      "Review participants and monitor platform activity.",
    actionLabel: "Review participants",
    actionPath: "/admin/verifications",
  },
};

const metricStyles = [
  {
    icon: Package,
    color:
      "bg-blue-100 text-blue-700 dark:bg-blue-950/50 dark:text-blue-300",
  },
  {
    icon: Clock3,
    color:
      "bg-amber-100 text-amber-700 dark:bg-amber-950/50 dark:text-amber-300",
  },
  {
    icon: CheckCircle2,
    color:
      "bg-emerald-100 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300",
  },
  {
    icon: BarChart3,
    color:
      "bg-sky-100 text-sky-700 dark:bg-sky-950/50 dark:text-sky-300",
  },
];

function firstValue(summary, keys, fallback = 0) {
  for (const key of keys) {
    const value = summary?.[key];

    if (
      value !== undefined &&
      value !== null
    ) {
      return value;
    }
  }

  return fallback;
}

function percentage(value) {
  return `${Number(value || 0).toFixed(1)}%`;
}

function getMetrics(role, summary) {
  if (role === "DONOR") {
    return [
      {
        label: "Donations created",
        value: firstValue(
          summary,
          ["donations_created"],
        ),
      },
      {
        label: "Active donations",
        value: firstValue(
          summary,
          ["active_donations"],
        ),
      },
      {
        label: "Completed",
        value: firstValue(
          summary,
          ["completed_donations"],
        ),
      },
      {
        label: "Completion rate",
        value: percentage(
          firstValue(
            summary,
            ["completion_rate"],
          ),
        ),
      },
    ];
  }

  if (role === "RECEIVER") {
    return [
      {
        label: "Requests submitted",
        value: firstValue(
          summary,
          ["requests_submitted"],
        ),
      },
      {
        label: "Pending requests",
        value: firstValue(
          summary,
          ["pending_requests"],
        ),
      },
      {
        label: "Donations received",
        value: firstValue(
          summary,
          ["donations_received"],
        ),
      },
      {
        label: "Approval rate",
        value: percentage(
          firstValue(
            summary,
            ["approval_rate"],
          ),
        ),
      },
    ];
  }

  if (role === "VOLUNTEER") {
    return [
      {
        label: "Tasks assigned",
        value: firstValue(
          summary,
          ["tasks_assigned"],
        ),
      },
      {
        label: "Active tasks",
        value: firstValue(
          summary,
          ["active_tasks"],
        ),
      },
      {
        label: "Completed tasks",
        value: firstValue(
          summary,
          ["completed_tasks"],
        ),
      },
      {
        label: "Completion rate",
        value: percentage(
          firstValue(
            summary,
            ["task_completion_rate"],
          ),
        ),
      },
    ];
  }

  return [
    {
      label: "Registered users",
      value: firstValue(
        summary,
        [
          "registered_users",
          "total_registered_users",
          "total_users",
        ],
      ),
    },
    {
      label: "Active users",
      value: firstValue(
        summary,
        ["active_users"],
      ),
    },
    {
      label: "Completed donations",
      value: firstValue(
        summary,
        ["completed_donations"],
      ),
    },
    {
      label: "Completion rate",
      value: percentage(
        firstValue(
          summary,
          ["completion_rate"],
        ),
      ),
    },
  ];
}

function formatUpdatedAt(value) {
  if (!value) {
    return "";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "";
  }

  return date.toLocaleString("en-IN");
}

export default function DashboardPage() {
  const { user } = useAuth();

  const {
    data: analytics,
    loading,
    error,
    reload,
  } = useApiResource("/analytics/");

  const role =
    user?.role?.toUpperCase() || "DONOR";

  const content =
    roleContent[role] ||
    roleContent.DONOR;

  const metrics = getMetrics(
    role,
    analytics?.summary || {},
  );

  const accountSuspended =
    user?.is_active === false;

  const verificationStatus =
    user?.verification_status ||
    "PENDING";

  return (
    <div>
      <section className="overflow-hidden rounded-3xl bg-gradient-to-br from-slate-950 via-slate-900 to-blue-950 p-6 text-white shadow-xl sm:p-8">
        <div className="flex flex-col gap-6 md:flex-row md:items-end md:justify-between">
          <div>
            <div className="mb-4 flex flex-wrap items-center gap-3">
              <StatusBadge status={role} />

              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold text-slate-300">
                  Verification:
                </span>

                <StatusBadge
                  status={verificationStatus}
                />
              </div>

              {user?.is_active !== undefined && (
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold text-slate-300">
                    Account:
                  </span>

                  <StatusBadge
                    status={
                      accountSuspended
                        ? "SUSPENDED"
                        : "ACTIVE"
                    }
                  />
                </div>
              )}
            </div>

            <p className="text-sm font-semibold text-sky-300">
              Welcome back
            </p>

            <h1 className="mt-2 text-3xl font-black tracking-tight sm:text-4xl">
              {user?.display_name ||
                user?.name ||
                "SmartFood participant"}
            </h1>

            <h2 className="mt-4 text-lg font-bold">
              {content.title}
            </h2>

            <p className="mt-2 max-w-2xl text-slate-300">
              {content.description}
            </p>

            {analytics?.generated_at && (
              <p className="mt-3 text-xs text-slate-400">
                Updated{" "}
                {formatUpdatedAt(
                  analytics.generated_at,
                )}
              </p>
            )}
          </div>

          <div className="flex flex-col gap-3 sm:flex-row">
            <Link
              to="/analytics"
              className="focus-ring inline-flex min-h-11 items-center justify-center gap-2 rounded-xl border border-white/20 bg-white/10 px-5 py-2.5 font-bold text-white backdrop-blur transition hover:bg-white/20 active:scale-[0.98]"
            >
              <BarChart3
                aria-hidden="true"
                className="size-4"
              />

              View impact
            </Link>

            {accountSuspended ? (
              <span
                aria-disabled="true"
                title="This account is suspended."
                className="inline-flex min-h-11 cursor-not-allowed items-center justify-center gap-2 rounded-xl bg-slate-600 px-5 py-2.5 font-bold text-slate-300 opacity-70"
              >
                {content.actionLabel}

                <ArrowRight
                  aria-hidden="true"
                  className="size-4"
                />
              </span>
            ) : (
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
          Your SmartFood account is suspended. You can
          review existing information, but protected
          operations are unavailable. Contact an
          administrator for assistance.
        </div>
      )}

      {loading && (
        <div className="mt-6">
          <LoadingState message="Loading dashboard analytics..." />
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
        <section
          aria-label="Dashboard metrics"
          className="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4"
        >
          {metrics.map(
            (
              {
                label,
                value,
              },
              index,
            ) => {
              const {
                icon: Icon,
                color,
              } =
                metricStyles[index];

              return (
                <motion.article
                  key={label}
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
                    delay:
                      index * 0.05,
                  }}
                >
                  <div
                    className={`flex size-11 items-center justify-center rounded-2xl ${color}`}
                  >
                    <Icon
                      aria-hidden="true"
                      className="size-5"
                    />
                  </div>

                  <p className="mt-5 text-sm font-semibold text-slate-500 dark:text-slate-400">
                    {label}
                  </p>

                  <p className="mt-1 text-3xl font-black text-slate-950 dark:text-white">
                    {value}
                  </p>
                </motion.article>
              );
            },
          )}
        </section>
      )}

      <section className="mt-6 rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-800">
        <div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-xl font-black text-slate-950 dark:text-white">
              SmartFood impact
            </h2>

            <p className="mt-2 max-w-3xl leading-7 text-slate-600 dark:text-slate-300">
              View donation outcomes, confirmed quantities,
              completion rates and monthly redistribution
              activity.
            </p>
          </div>

          <div className="flex flex-wrap gap-3">
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

            <Link
              to="/analytics"
              className="focus-ring inline-flex min-h-11 items-center justify-center gap-2 rounded-xl bg-blue-600 px-5 py-2.5 font-bold text-white transition hover:bg-blue-700 active:scale-[0.98]"
            >
              <HeartHandshake
                aria-hidden="true"
                className="size-4"
              />

              Open impact dashboard
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}