import {
  ArrowRight,
  BarChart3,
  Clock3,
  HeartHandshake,
  Package,
} from "lucide-react";

import { Link } from "react-router-dom";
import { motion } from "motion/react";

import { useAuth } from "../auth/AuthProvider";
import StatusBadge from "../components/ui/StatusBadge";

const roleContent = {
  DONOR: {
    title: "Donor dashboard",
    description:
      "Create donations and coordinate receiver requests.",
    actionLabel: "Create donation",
    actionPath: "/donations",
  },

  RECEIVER: {
    title: "Receiver dashboard",
    description:
      "Find compatible food donations for your organization.",
    actionLabel: "Discover donations",
    actionPath: "/discover",
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
    actionPath: "/admin/participants",
  },
};

const metricCards = [
  {
    label: "Active items",
    value: "—",
    icon: Package,
    color:
      "bg-blue-100 text-blue-700 dark:bg-blue-950/50 dark:text-blue-300",
  },
  {
    label: "Pending actions",
    value: "—",
    icon: Clock3,
    color:
      "bg-amber-100 text-amber-700 dark:bg-amber-950/50 dark:text-amber-300",
  },
  {
    label: "Completed",
    value: "—",
    icon: HeartHandshake,
    color:
      "bg-emerald-100 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300",
  },
  {
    label: "Impact",
    value: "—",
    icon: BarChart3,
    color:
      "bg-sky-100 text-sky-700 dark:bg-sky-950/50 dark:text-sky-300",
  },
];

export default function DashboardPage() {
  const { user } = useAuth();

  const role =
    user?.role?.toUpperCase() || "DONOR";

  const content =
    roleContent[role] || roleContent.DONOR;

  return (
    <div>
      <section className="overflow-hidden rounded-3xl bg-gradient-to-br from-slate-950 via-slate-900 to-blue-950 p-6 text-white shadow-xl sm:p-8">
        <div className="flex flex-col gap-6 md:flex-row md:items-end md:justify-between">
          <div>
            <div className="mb-4 flex flex-wrap gap-2">
              <StatusBadge status={role} />

              <StatusBadge
                status={
                  user?.verification_status ||
                  "PENDING"
                }
              />
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
          </div>

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
        </div>
      </section>

      <section
        aria-label="Dashboard metrics"
        className="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4"
      >
        {metricCards.map(
          (
            {
              label,
              value,
              icon: Icon,
              color,
            },
            index,
          ) => (
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
                delay: index * 0.05,
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
          ),
        )}
      </section>

      <section className="mt-6 rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-800">
        <h2 className="text-xl font-black text-slate-950 dark:text-white">
          Shared frontend foundation ready
        </h2>

        <p className="mt-2 max-w-3xl leading-7 text-slate-600 dark:text-slate-300">
          Routing, authentication state, API handling,
          role-based navigation, forms, feedback states,
          dialogs and responsive layouts are now available.
          Feature-specific dashboard data will be connected
          in the next frontend steps.
        </p>
      </section>
    </div>
  );
}