import {
  AlertTriangle,
  BarChart3,
  CheckCircle2,
  PackageCheck,
  RefreshCw,
  Scale,
  TrendingUp,
  Users,
} from "lucide-react";

import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import api from "../../lib/api";


function getErrorMessage(error) {
  const detail =
    error?.response?.data?.detail;

  if (typeof detail === "string") {
    return detail;
  }

  return "Unable to load analytics.";
}


function humanize(value) {
  return String(value)
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/\b\w/g, (letter) =>
      letter.toUpperCase(),
    );
}


function formatMetricValue(key, value) {
  if (key.includes("rate")) {
    return `${Number(value || 0).toFixed(2)}%`;
  }

  return Number(value || 0).toLocaleString(
    "en-IN",
  );
}


function formatGeneratedAt(value) {
  if (!value) {
    return "";
  }

  return new Intl.DateTimeFormat(
    "en-IN",
    {
      dateStyle: "medium",
      timeStyle: "short",
    },
  ).format(new Date(value));
}


function metricIcon(key) {
  if (key.includes("user")) {
    return Users;
  }

  if (
    key.includes("completed")
    || key.includes("received")
  ) {
    return CheckCircle2;
  }

  if (
    key.includes("failed")
    || key.includes("unsuccessful")
    || key.includes("complaint")
  ) {
    return AlertTriangle;
  }

  if (key.includes("rate")) {
    return TrendingUp;
  }

  return PackageCheck;
}


function MetricCard({
  metricKey,
  value,
}) {
  const Icon = metricIcon(metricKey);

  return (
    <article
      className={
        "rounded-2xl border border-slate-200/80 "
        + "bg-white p-5 shadow-sm transition-all "
        + "duration-200 hover:-translate-y-1 "
        + "hover:shadow-xl hover:shadow-blue-500/5 "
        + "dark:border-slate-700/60 "
        + "dark:bg-slate-800"
      }
    >
      <div
        className={
          "flex h-11 w-11 items-center justify-center "
          + "rounded-xl bg-blue-50 text-blue-600 "
          + "dark:bg-blue-500/10 dark:text-blue-300"
        }
      >
        <Icon
          className="h-5 w-5"
          aria-hidden="true"
        />
      </div>

      <p
        className={
          "mt-4 text-2xl font-bold text-slate-900 "
          + "dark:text-white"
        }
      >
        {formatMetricValue(metricKey, value)}
      </p>

      <p
        className={
          "mt-1 text-sm text-slate-500 "
          + "dark:text-slate-400"
        }
      >
        {humanize(metricKey)}
      </p>
    </article>
  );
}


function QuantityCard({
  item,
}) {
  return (
    <div
      className={
        "rounded-2xl border border-emerald-200 "
        + "bg-emerald-50 p-5 "
        + "dark:border-emerald-500/30 "
        + "dark:bg-emerald-500/10"
      }
    >
      <div className="flex items-center gap-3">
        <Scale
          className={
            "h-6 w-6 text-emerald-600 "
            + "dark:text-emerald-300"
          }
        />

        <div>
          <p
            className={
              "text-2xl font-bold text-emerald-800 "
              + "dark:text-emerald-200"
            }
          >
            {Number(
              item.quantity || 0,
            ).toLocaleString("en-IN")}
          </p>

          <p
            className={
              "text-sm font-medium text-emerald-700 "
              + "dark:text-emerald-300"
            }
          >
            {humanize(item.unit)}
          </p>
        </div>
      </div>
    </div>
  );
}


function StatusBreakdown({
  values,
}) {
  const maximumCount = Math.max(
    1,
    ...values.map((item) => item.count),
  );

  return (
    <section
      className={
        "rounded-2xl border border-slate-200 "
        + "bg-white p-5 shadow-sm "
        + "dark:border-slate-700 dark:bg-slate-800"
      }
    >
      <h2
        className={
          "flex items-center gap-2 text-lg "
          + "font-semibold text-slate-900 "
          + "dark:text-white"
        }
      >
        <BarChart3 className="h-5 w-5 text-blue-600" />
        Status breakdown
      </h2>

      {values.length === 0 ? (
        <p className="mt-6 text-sm text-slate-500">
          No status information is available yet.
        </p>
      ) : (
        <div className="mt-6 space-y-5">
          {values.map((item) => {
            const width = (
              item.count / maximumCount
            ) * 100;

            return (
              <div key={item.status}>
                <div
                  className={
                    "mb-2 flex items-center "
                    + "justify-between text-sm"
                  }
                >
                  <span
                    className={
                      "font-medium text-slate-700 "
                      + "dark:text-slate-200"
                    }
                  >
                    {humanize(item.status)}
                  </span>

                  <span className="text-slate-500">
                    {item.count}
                  </span>
                </div>

                <div
                  className={
                    "h-2.5 overflow-hidden rounded-full "
                    + "bg-slate-100 dark:bg-slate-700"
                  }
                >
                  <div
                    className={
                      "h-full rounded-full bg-blue-600 "
                      + "transition-all duration-500"
                    }
                    style={{
                      width: `${width}%`,
                    }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}


function MonthlyTrend({
  values,
}) {
  const maximumValue = Math.max(
    1,
    ...values.flatMap((item) => [
      item.created,
      item.completed,
    ]),
  );

  return (
    <section
      className={
        "rounded-2xl border border-slate-200 "
        + "bg-white p-5 shadow-sm "
        + "dark:border-slate-700 dark:bg-slate-800"
      }
    >
      <h2
        className={
          "flex items-center gap-2 text-lg "
          + "font-semibold text-slate-900 "
          + "dark:text-white"
        }
      >
        <TrendingUp className="h-5 w-5 text-sky-500" />
        Six-month donation trend
      </h2>

      {values.length === 0 ? (
        <p className="mt-6 text-sm text-slate-500">
          Monthly trend information is not available for
          this role yet.
        </p>
      ) : (
        <>
          <div
            className={
              "mt-5 flex items-center gap-5 text-xs "
              + "text-slate-500"
            }
          >
            <span className="flex items-center gap-2">
              <span
                className={
                  "h-3 w-3 rounded-full bg-blue-600"
                }
              />
              Created
            </span>

            <span className="flex items-center gap-2">
              <span
                className={
                  "h-3 w-3 rounded-full bg-emerald-500"
                }
              />
              Completed
            </span>
          </div>

          <div
            className={
              "mt-6 grid min-h-56 grid-cols-6 "
              + "items-end gap-3 overflow-x-auto"
            }
          >
            {values.map((item) => (
              <div
                key={item.month}
                className={
                  "flex min-w-14 flex-col items-center"
                }
              >
                <div
                  className={
                    "flex h-40 items-end gap-1"
                  }
                >
                  <div
                    title={`${item.created} created`}
                    className={
                      "w-4 rounded-t bg-blue-600 "
                      + "transition-all duration-500"
                    }
                    style={{
                      height:
                        `${
                          Math.max(
                            4,
                            (
                              item.created
                              / maximumValue
                            ) * 100,
                          )
                        }%`,
                    }}
                  />

                  <div
                    title={`${item.completed} completed`}
                    className={
                      "w-4 rounded-t bg-emerald-500 "
                      + "transition-all duration-500"
                    }
                    style={{
                      height:
                        `${
                          Math.max(
                            4,
                            (
                              item.completed
                              / maximumValue
                            ) * 100,
                          )
                        }%`,
                    }}
                  />
                </div>

                <p
                  className={
                    "mt-3 whitespace-nowrap text-xs "
                    + "text-slate-500"
                  }
                >
                  {item.label}
                </p>
              </div>
            ))}
          </div>
        </>
      )}
    </section>
  );
}


function UserBreakdown({
  values,
}) {
  if (!values?.length) {
    return null;
  }

  return (
    <section
      className={
        "rounded-2xl border border-slate-200 "
        + "bg-white p-5 shadow-sm "
        + "dark:border-slate-700 dark:bg-slate-800"
      }
    >
      <h2
        className={
          "flex items-center gap-2 text-lg "
          + "font-semibold text-slate-900 "
          + "dark:text-white"
        }
      >
        <Users className="h-5 w-5 text-blue-600" />
        Users by role
      </h2>

      <div
        className={
          "mt-5 grid gap-3 sm:grid-cols-2"
        }
      >
        {values.map((item) => (
          <div
            key={item.role}
            className={
              "flex items-center justify-between "
              + "rounded-xl bg-slate-50 p-4 "
              + "dark:bg-slate-900/50"
            }
          >
            <span
              className={
                "font-medium text-slate-700 "
                + "dark:text-slate-200"
              }
            >
              {humanize(item.role)}
            </span>

            <span
              className={
                "text-lg font-bold text-slate-900 "
                + "dark:text-white"
              }
            >
              {item.count}
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}


function LoadingAnalytics() {
  return (
    <div className="space-y-6">
      <div
        className={
          "h-40 animate-pulse rounded-3xl "
          + "bg-slate-200 dark:bg-slate-700"
        }
      />

      <div
        className={
          "grid gap-4 sm:grid-cols-2 "
          + "xl:grid-cols-4"
        }
      >
        {[1, 2, 3, 4].map((item) => (
          <div
            key={item}
            className={
              "h-36 animate-pulse rounded-2xl "
              + "bg-slate-200 dark:bg-slate-700"
            }
          />
        ))}
      </div>
    </div>
  );
}


export default function AnalyticsPage() {
  const [analytics, setAnalytics] =
    useState(null);

  const [loading, setLoading] =
    useState(true);

  const [refreshing, setRefreshing] =
    useState(false);

  const [error, setError] =
    useState("");

  const summaryEntries = useMemo(
    () =>
      Object.entries(
        analytics?.summary || {},
      ),
    [analytics],
  );

  const loadAnalytics = useCallback(
    async (refresh = false) => {
      if (refresh) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }

      setError("");

      try {
        const response = await api.get(
          "/analytics/",
        );

        setAnalytics(response.data);
      } catch (requestError) {
        setError(
          getErrorMessage(requestError),
        );
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [],
  );

  useEffect(() => {
    loadAnalytics();
  }, [loadAnalytics]);

  if (loading) {
    return <LoadingAnalytics />;
  }

  return (
    <main className="space-y-6">
      <section
        className={
          "rounded-3xl bg-gradient-to-br "
          + "from-blue-600 to-sky-500 p-6 "
          + "text-white shadow-lg shadow-blue-500/10 "
          + "sm:p-8"
        }
      >
        <div
          className={
            "flex flex-col gap-5 sm:flex-row "
            + "sm:items-center sm:justify-between"
          }
        >
          <div>
            <div
              className={
                "mb-3 inline-flex items-center gap-2 "
                + "rounded-full bg-white/15 px-3 py-1 "
                + "text-sm backdrop-blur"
              }
            >
              <BarChart3 className="h-4 w-4" />
              {humanize(
                analytics?.role || "user",
              )} analytics
            </div>

            <h1 className="text-2xl font-bold sm:text-3xl">
              Impact dashboard
            </h1>

            <p className="mt-2 max-w-2xl text-blue-50">
              Track verified redistribution outcomes and
              operational activity.
            </p>

            {analytics?.generated_at && (
              <p className="mt-3 text-xs text-blue-100">
                Updated{" "}
                {formatGeneratedAt(
                  analytics.generated_at,
                )}
              </p>
            )}
          </div>

          <button
            type="button"
            onClick={() =>
              loadAnalytics(true)
            }
            disabled={refreshing}
            className={
              "inline-flex min-h-11 items-center "
              + "justify-center gap-2 rounded-xl "
              + "bg-white px-5 py-3 font-semibold "
              + "text-blue-700 transition hover:bg-blue-50 "
              + "active:scale-[0.98] "
              + "focus-visible:outline-none "
              + "focus-visible:ring-2 "
              + "focus-visible:ring-white "
              + "disabled:opacity-60"
            }
          >
            <RefreshCw
              className={
                `h-5 w-5 ${
                  refreshing
                    ? "animate-spin"
                    : ""
                }`
              }
            />
            Refresh
          </button>
        </div>
      </section>

      {error && (
        <div
          role="alert"
          className={
            "rounded-2xl border border-red-200 "
            + "bg-red-50 p-4 text-red-700 "
            + "dark:border-red-500/30 "
            + "dark:bg-red-500/10 "
            + "dark:text-red-200"
          }
        >
          {error}
        </div>
      )}

      {!error && analytics && (
        <>
          <section
            aria-label="Summary metrics"
            className={
              "grid gap-4 sm:grid-cols-2 "
              + "xl:grid-cols-4"
            }
          >
            {summaryEntries.map(
              ([metricKey, value]) => (
                <MetricCard
                  key={metricKey}
                  metricKey={metricKey}
                  value={value}
                />
              ),
            )}
          </section>

          <section>
            <h2
              className={
                "mb-4 text-lg font-semibold "
                + "text-slate-900 dark:text-white"
              }
            >
              Confirmed quantity redistributed
            </h2>

            {analytics.quantity_redistributed
              ?.length ? (
              <div
                className={
                  "grid gap-4 sm:grid-cols-2 "
                  + "lg:grid-cols-4"
                }
              >
                {analytics.quantity_redistributed.map(
                  (item) => (
                    <QuantityCard
                      key={item.unit}
                      item={item}
                    />
                  ),
                )}
              </div>
            ) : (
              <div
                className={
                  "rounded-2xl border border-dashed "
                  + "border-slate-300 bg-white p-8 "
                  + "text-center text-sm text-slate-500 "
                  + "dark:border-slate-700 "
                  + "dark:bg-slate-800"
                }
              >
                No completed receipt-confirmed quantities yet.
              </div>
            )}
          </section>

          <div
            className={
              "grid gap-6 lg:grid-cols-2"
            }
          >
            <StatusBreakdown
              values={
                analytics.status_breakdown || []
              }
            />

            <MonthlyTrend
              values={
                analytics.monthly_trend || []
              }
            />
          </div>

          <UserBreakdown
            values={
              analytics.user_breakdown || []
            }
          />

          <div
            className={
              "rounded-2xl border border-sky-200 "
              + "bg-sky-50 p-4 text-sm text-sky-800 "
              + "dark:border-sky-500/30 "
              + "dark:bg-sky-500/10 "
              + "dark:text-sky-200"
            }
          >
            Quantity metrics are calculated from receiver-confirmed
            receipt records. Environmental savings are not shown
            until documented conversion factors are configured.
          </div>
        </>
      )}
    </main>
  );
}