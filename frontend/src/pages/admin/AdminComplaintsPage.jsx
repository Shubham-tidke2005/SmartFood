import {
  AlertCircle,
  Check,
  CheckCircle2,
  Clock3,
  FileWarning,
  LoaderCircle,
  RefreshCw,
  Search,
  ShieldCheck,
  X,
} from "lucide-react";

import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import api from "../../lib/api";


const STATUS_STYLES = {
  OPEN:
    "border-amber-200 bg-amber-50 text-amber-700",

  UNDER_REVIEW:
    "border-blue-200 bg-blue-50 text-blue-700",

  RESOLVED:
    "border-emerald-200 bg-emerald-50 text-emerald-700",
};


function getResults(data) {
  if (Array.isArray(data)) {
    return data;
  }

  if (Array.isArray(data?.results)) {
    return data.results;
  }

  if (Array.isArray(data?.complaints)) {
    return data.complaints;
  }

  return [];
}


function getErrorMessage(error) {
  const data = error?.response?.data;

  if (!data) {
    return (
      "Could not connect to SmartFood. " +
      "Make sure Django is running."
    );
  }

  if (typeof data === "string") {
    return data;
  }

  if (data.detail) {
    return data.detail;
  }

  const firstField = Object.keys(data)[0];

  if (firstField) {
    const value = data[firstField];

    if (Array.isArray(value)) {
      return `${firstField}: ${value[0]}`;
    }

    return `${firstField}: ${value}`;
  }

  return "The operation could not be completed.";
}


function formatDateTime(value) {
  if (!value) {
    return "Not available";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("en-IN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}


function formatStatus(status) {
  return (
    status
      ?.replaceAll("_", " ")
      .toLowerCase()
      .replace(/\b\w/g, (letter) =>
        letter.toUpperCase(),
      ) || "Unknown"
  );
}


function StatusBadge({
  status,
}) {
  return (
    <span
      className={`
        inline-flex rounded-full border
        px-3 py-1 text-xs font-bold
        uppercase tracking-wide
        ${
          STATUS_STYLES[status] ||
          (
            "border-slate-200 bg-slate-100 " +
            "text-slate-700"
          )
        }
      `}
    >
      {formatStatus(status)}
    </span>
  );
}


function ResolveDialog({
  complaint,
  submitting,
  error,
  onClose,
  onResolve,
}) {
  const [resolution, setResolution] =
    useState("");

  useEffect(() => {
    setResolution("");
  }, [complaint]);

  if (!complaint) {
    return null;
  }

  function handleSubmit(event) {
    event.preventDefault();

    if (resolution.trim().length < 3) {
      return;
    }

    onResolve(resolution.trim());
  }

  return (
    <div
      className="
        fixed inset-0 z-50 flex items-end
        justify-center bg-slate-950/50
        backdrop-blur-sm
        sm:items-center sm:p-4
      "
      role="presentation"
      onMouseDown={(event) => {
        if (
          event.target === event.currentTarget &&
          !submitting
        ) {
          onClose();
        }
      }}
    >
      <section
        role="dialog"
        aria-modal="true"
        aria-labelledby="resolve-title"
        className="
          w-full rounded-t-3xl bg-white
          shadow-2xl
          sm:max-w-xl sm:rounded-3xl
        "
      >
        <div
          className="
            flex items-start justify-between
            border-b border-slate-200 p-5
          "
        >
          <div>
            <p
              className="
                text-sm font-semibold uppercase
                tracking-wide text-emerald-600
              "
            >
              Complaint resolution
            </p>

            <h2
              id="resolve-title"
              className="
                mt-1 text-xl font-bold
                text-slate-900
              "
            >
              Resolve complaint
            </h2>
          </div>

          <button
            type="button"
            disabled={submitting}
            onClick={onClose}
            aria-label="Close resolution form"
            className="
              rounded-xl p-2 text-slate-500
              hover:bg-slate-100
            "
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <form
          onSubmit={handleSubmit}
          className="space-y-5 p-5"
        >
          <div
            className="
              rounded-xl border border-slate-200
              bg-slate-50 p-4
            "
          >
            <p
              className="
                whitespace-pre-wrap text-sm
                text-slate-700
              "
            >
              {complaint.description}
            </p>
          </div>

          <label className="block">
            <span
              className="
                mb-2 block text-sm font-semibold
                text-slate-900
              "
            >
              Resolution explanation
            </span>

            <textarea
              required
              minLength={3}
              maxLength={8000}
              rows={6}
              value={resolution}
              onChange={(event) =>
                setResolution(
                  event.target.value,
                )
              }
              placeholder={
                "Explain the investigation result and " +
                "the action taken..."
              }
              className="
                w-full resize-none rounded-xl
                border border-slate-300
                px-4 py-3 text-slate-900
                outline-none
                focus:border-blue-500
                focus:ring-2
                focus:ring-blue-500/20
              "
            />
          </label>

          {error ? (
            <div
              role="alert"
              className="
                flex items-start gap-2
                rounded-xl border border-red-200
                bg-red-50 p-3 text-sm text-red-700
              "
            >
              <AlertCircle
                className="
                  mt-0.5 h-5 w-5 shrink-0
                "
              />

              <span>{error}</span>
            </div>
          ) : null}

          <div
            className="
              flex flex-col-reverse gap-3
              sm:flex-row sm:justify-end
            "
          >
            <button
              type="button"
              disabled={submitting}
              onClick={onClose}
              className="
                rounded-xl border
                border-slate-300 px-5 py-3
                font-semibold text-slate-700
                hover:bg-slate-50
              "
            >
              Cancel
            </button>

            <button
              type="submit"
              disabled={
                submitting ||
                resolution.trim().length < 3
              }
              className="
                inline-flex items-center
                justify-center gap-2 rounded-xl
                bg-emerald-600 px-5 py-3
                font-semibold text-white
                transition hover:bg-emerald-700
                disabled:cursor-not-allowed
                disabled:opacity-60
              "
            >
              {submitting ? (
                <LoaderCircle
                  className="
                    h-5 w-5 animate-spin
                  "
                />
              ) : (
                <Check className="h-5 w-5" />
              )}

              Confirm resolution
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}


export default function AdminComplaintsPage() {
  const [complaints, setComplaints] =
    useState([]);

  const [statusFilter, setStatusFilter] =
    useState("OPEN");

  const [search, setSearch] =
    useState("");

  const [loading, setLoading] =
    useState(true);

  const [processingId, setProcessingId] =
    useState(null);

  const [selectedComplaint, setSelectedComplaint] =
    useState(null);

  const [error, setError] =
    useState("");

  const [dialogError, setDialogError] =
    useState("");

  const [success, setSuccess] =
    useState("");

  const loadComplaints =
    useCallback(async () => {
      setLoading(true);
      setError("");

      try {
        const response = await api.get(
          "/complaints/",
        );

        setComplaints(
          getResults(response.data),
        );
      } catch (requestError) {
        setError(
          getErrorMessage(requestError),
        );
      } finally {
        setLoading(false);
      }
    }, []);

  useEffect(() => {
    loadComplaints();
  }, [loadComplaints]);

  const visibleComplaints =
    useMemo(() => {
      const normalizedSearch =
        search.trim().toLowerCase();

      return complaints.filter(
        (complaint) => {
          const matchesStatus =
            statusFilter === "ALL" ||
            complaint.status === statusFilter;

          const matchesSearch =
            !normalizedSearch ||
            [
              complaint.id,
              complaint.description,
              complaint.reporter_name,
              complaint.donation_id,
              complaint.donation,
              complaint.reported_user_id,
            ]
              .filter(Boolean)
              .some((value) =>
                String(value)
                  .toLowerCase()
                  .includes(normalizedSearch),
              );

          return (
            matchesStatus &&
            matchesSearch
          );
        },
      );
    }, [
      complaints,
      statusFilter,
      search,
    ]);

  async function startReview(complaint) {
    setProcessingId(complaint.id);
    setError("");
    setSuccess("");

    try {
      await api.post(
        (
          `/complaints/${complaint.id}/` +
          "start-review/"
        ),
        {},
      );

      setSuccess(
        "Complaint review started successfully.",
      );

      await loadComplaints();
    } catch (requestError) {
      setError(
        getErrorMessage(requestError),
      );
    } finally {
      setProcessingId(null);
    }
  }

  async function resolveComplaint(resolution) {
    if (!selectedComplaint) {
      return;
    }

    setProcessingId(
      selectedComplaint.id,
    );

    setDialogError("");

    try {
      await api.post(
        (
          `/complaints/${selectedComplaint.id}/` +
          "resolve/"
        ),
        {
          resolution,
        },
      );

      setSelectedComplaint(null);

      setSuccess(
        "Complaint resolved successfully.",
      );

      await loadComplaints();
    } catch (requestError) {
      setDialogError(
        getErrorMessage(requestError),
      );
    } finally {
      setProcessingId(null);
    }
  }

  return (
    <main className="space-y-6">
      <header
        className="
          rounded-3xl bg-gradient-to-br
          from-blue-600 to-sky-500
          p-6 text-white shadow-lg
          shadow-blue-500/10 sm:p-8
        "
      >
        <div
          className="
            flex flex-col gap-4 sm:flex-row
            sm:items-center sm:justify-between
          "
        >
          <div>
            <p
              className="
                text-sm font-semibold uppercase
                tracking-widest text-blue-100
              "
            >
              Administration
            </p>

            <h1 className="mt-2 text-3xl font-bold">
              Complaint review
            </h1>

            <p
              className="
                mt-3 max-w-2xl text-blue-50
              "
            >
              Investigate participant reports and
              record transparent resolutions.
            </p>
          </div>

          <button
            type="button"
            onClick={loadComplaints}
            disabled={loading}
            className="
              inline-flex items-center
              justify-center gap-2 rounded-xl
              bg-white/15 px-4 py-3
              font-semibold text-white
              hover:bg-white/25
            "
          >
            <RefreshCw
              className={`
                h-5 w-5
                ${loading ? "animate-spin" : ""}
              `}
            />
            Refresh
          </button>
        </div>
      </header>

      {error ? (
        <div
          role="alert"
          className="
            flex items-start gap-3
            rounded-2xl border border-red-200
            bg-red-50 p-4 text-red-700
          "
        >
          <AlertCircle
            className="
              mt-0.5 h-5 w-5 shrink-0
            "
          />

          <span>{error}</span>
        </div>
      ) : null}

      {success ? (
        <div
          role="status"
          className="
            flex items-start gap-3
            rounded-2xl border
            border-emerald-200 bg-emerald-50
            p-4 text-emerald-800
          "
        >
          <CheckCircle2
            className="
              mt-0.5 h-5 w-5 shrink-0
            "
          />

          <span>{success}</span>
        </div>
      ) : null}

      <section
        className="
          rounded-2xl border border-slate-200
          bg-white p-4 shadow-sm
        "
      >
        <div
          className="
            grid gap-3 sm:grid-cols-2
          "
        >
          <label className="relative">
            <span className="sr-only">
              Search complaints
            </span>

            <Search
              className="
                pointer-events-none absolute
                left-3 top-1/2 h-5 w-5
                -translate-y-1/2 text-slate-400
              "
            />

            <input
              type="search"
              value={search}
              onChange={(event) =>
                setSearch(event.target.value)
              }
              placeholder="Search complaints..."
              className="
                w-full rounded-xl border
                border-slate-300 py-3
                pl-10 pr-4 outline-none
                focus:border-blue-500
                focus:ring-2
                focus:ring-blue-500/20
              "
            />
          </label>

          <select
            value={statusFilter}
            onChange={(event) =>
              setStatusFilter(
                event.target.value,
              )
            }
            className="
              rounded-xl border border-slate-300
              bg-white px-4 py-3 outline-none
              focus:border-blue-500
              focus:ring-2
              focus:ring-blue-500/20
            "
          >
            <option value="ALL">
              All statuses
            </option>

            <option value="OPEN">
              Open
            </option>

            <option value="UNDER_REVIEW">
              Under review
            </option>

            <option value="RESOLVED">
              Resolved
            </option>
          </select>
        </div>
      </section>

      {loading ? (
        <section
          className="
            grid gap-5 lg:grid-cols-2
          "
        >
          {[1, 2, 3, 4].map((item) => (
            <div
              key={item}
              className="
                h-80 animate-pulse rounded-2xl
                bg-slate-200
              "
            />
          ))}
        </section>
      ) : null}

      {!loading &&
      !error &&
      visibleComplaints.length === 0 ? (
        <section
          className="
            rounded-2xl border border-dashed
            border-slate-300 bg-white
            p-10 text-center
          "
        >
          <ShieldCheck
            className="
              mx-auto h-12 w-12
              text-slate-300
            "
          />

          <h2
            className="
              mt-4 text-lg font-bold
              text-slate-900
            "
          >
            No complaints found
          </h2>

          <p
            className="
              mt-2 text-sm text-slate-600
            "
          >
            There are no complaints matching the
            selected filters.
          </p>
        </section>
      ) : null}

      {!loading &&
      visibleComplaints.length > 0 ? (
        <section
          className="
            grid gap-5 lg:grid-cols-2
          "
        >
          {visibleComplaints.map(
            (complaint) => {
              const processing =
                processingId === complaint.id;

              return (
                <article
                  key={complaint.id}
                  className="
                    rounded-2xl border
                    border-slate-200 bg-white
                    p-5 shadow-sm
                  "
                >
                  <div
                    className="
                      flex items-start
                      justify-between gap-4
                    "
                  >
                    <div>
                      <StatusBadge
                        status={complaint.status}
                      />

                      <p
                        className="
                          mt-3 text-sm
                          text-slate-500
                        "
                      >
                        {formatDateTime(
                          complaint.created_at,
                        )}
                      </p>
                    </div>

                    <FileWarning
                      className="
                        h-7 w-7 text-amber-500
                      "
                    />
                  </div>

                  <div
                    className="
                      mt-5 rounded-xl border
                      border-slate-200 p-4
                    "
                  >
                    <p
                      className="
                        whitespace-pre-wrap
                        text-sm text-slate-700
                      "
                    >
                      {complaint.description}
                    </p>
                  </div>

                  <div
                    className="
                      mt-4 grid gap-3
                      sm:grid-cols-2
                    "
                  >
                    <div
                      className="
                        rounded-xl bg-slate-50 p-4
                      "
                    >
                      <p
                        className="
                          text-xs font-semibold
                          text-slate-500
                        "
                      >
                        Reporter
                      </p>

                      <p
                        className="
                          mt-1 break-all text-sm
                          font-medium text-slate-900
                        "
                      >
                        {complaint.reporter_name ||
                          complaint.reporter ||
                          "Participant"}
                      </p>
                    </div>

                    <div
                      className="
                        rounded-xl bg-slate-50 p-4
                      "
                    >
                      <p
                        className="
                          text-xs font-semibold
                          text-slate-500
                        "
                      >
                        Target
                      </p>

                      <p
                        className="
                          mt-1 break-all text-sm
                          font-medium text-slate-900
                        "
                      >
                        {complaint.donation_id ||
                          complaint.donation ||
                          complaint.reported_user_id ||
                          complaint.reported_user ||
                          "Not available"}
                      </p>
                    </div>
                  </div>

                  {complaint.resolution ? (
                    <div
                      className="
                        mt-4 rounded-xl border
                        border-emerald-200
                        bg-emerald-50 p-4
                      "
                    >
                      <p
                        className="
                          text-xs font-semibold
                          uppercase text-emerald-700
                        "
                      >
                        Resolution
                      </p>

                      <p
                        className="
                          mt-2 whitespace-pre-wrap
                          text-sm text-emerald-900
                        "
                      >
                        {complaint.resolution}
                      </p>
                    </div>
                  ) : null}

                  {complaint.status === "OPEN" ? (
                    <button
                      type="button"
                      disabled={processing}
                      onClick={() =>
                        startReview(complaint)
                      }
                      className="
                        mt-5 inline-flex w-full
                        items-center justify-center
                        gap-2 rounded-xl bg-blue-600
                        px-5 py-3 font-semibold
                        text-white hover:bg-blue-700
                        disabled:opacity-60
                      "
                    >
                      {processing ? (
                        <LoaderCircle
                          className="
                            h-5 w-5 animate-spin
                          "
                        />
                      ) : (
                        <Clock3 className="h-5 w-5" />
                      )}

                      Start review
                    </button>
                  ) : null}

                  {complaint.status ===
                  "UNDER_REVIEW" ? (
                    <button
                      type="button"
                      disabled={processing}
                      onClick={() => {
                        setDialogError("");
                        setSelectedComplaint(
                          complaint,
                        );
                      }}
                      className="
                        mt-5 inline-flex w-full
                        items-center justify-center
                        gap-2 rounded-xl
                        bg-emerald-600 px-5 py-3
                        font-semibold text-white
                        hover:bg-emerald-700
                        disabled:opacity-60
                      "
                    >
                      <CheckCircle2
                        className="h-5 w-5"
                      />

                      Resolve complaint
                    </button>
                  ) : null}
                </article>
              );
            },
          )}
        </section>
      ) : null}

      <ResolveDialog
        complaint={selectedComplaint}
        submitting={Boolean(processingId)}
        error={dialogError}
        onClose={() => {
          if (!processingId) {
            setSelectedComplaint(null);
            setDialogError("");
          }
        }}
        onResolve={resolveComplaint}
      />
    </main>
  );
}