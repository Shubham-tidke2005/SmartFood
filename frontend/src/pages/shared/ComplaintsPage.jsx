import {
  AlertCircle,
  CheckCircle2,
  Clock3,
  FileWarning,
  LoaderCircle,
  Plus,
  RefreshCw,
  Send,
  X,
} from "lucide-react";

import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  useSearchParams,
} from "react-router-dom";

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


function PageMessage({
  message,
  type = "error",
}) {
  if (!message) {
    return null;
  }

  const success =
    type === "success";

  return (
    <div
      role={success ? "status" : "alert"}
      className={`
        flex items-start gap-3 rounded-2xl
        border p-4
        ${
          success
            ? (
                "border-emerald-200 bg-emerald-50 " +
                "text-emerald-800"
              )
            : (
                "border-red-200 bg-red-50 " +
                "text-red-700"
              )
        }
      `}
    >
      {success ? (
        <CheckCircle2
          className="mt-0.5 h-5 w-5 shrink-0"
          aria-hidden="true"
        />
      ) : (
        <AlertCircle
          className="mt-0.5 h-5 w-5 shrink-0"
          aria-hidden="true"
        />
      )}

      <span>{message}</span>
    </div>
  );
}


function ComplaintCard({
  complaint,
}) {
  const donationId =
    complaint.donation_id ||
    complaint.donation;

  const reportedUserId =
    complaint.reported_user_id ||
    complaint.reported_user;

  return (
    <article
      className="
        rounded-2xl border border-slate-200
        bg-white p-5 shadow-sm
      "
    >
      <div
        className="
          flex flex-col gap-3 sm:flex-row
          sm:items-start sm:justify-between
        "
      >
        <div>
          <StatusBadge
            status={complaint.status}
          />

          <p className="mt-3 text-sm text-slate-500">
            Submitted{" "}
            {formatDateTime(
              complaint.created_at,
            )}
          </p>
        </div>

        <FileWarning
          className="h-7 w-7 text-amber-500"
          aria-hidden="true"
        />
      </div>

      <div className="mt-5 space-y-3">
        {donationId ? (
          <div className="rounded-xl bg-slate-50 p-4">
            <p
              className="
                text-xs font-semibold uppercase
                text-slate-500
              "
            >
              Donation
            </p>

            <p
              className="
                mt-1 break-all text-sm font-medium
                text-slate-900
              "
            >
              {donationId}
            </p>
          </div>
        ) : null}

        {reportedUserId ? (
          <div className="rounded-xl bg-slate-50 p-4">
            <p
              className="
                text-xs font-semibold uppercase
                text-slate-500
              "
            >
              Reported participant
            </p>

            <p
              className="
                mt-1 break-all text-sm font-medium
                text-slate-900
              "
            >
              {complaint.reported_user_name ||
                reportedUserId}
            </p>
          </div>
        ) : null}

        <div
          className="
            rounded-xl border border-slate-200
            p-4
          "
        >
          <p
            className="
              text-xs font-semibold uppercase
              text-slate-500
            "
          >
            Description
          </p>

          <p
            className="
              mt-2 whitespace-pre-wrap
              text-sm text-slate-700
            "
          >
            {complaint.description}
          </p>
        </div>

        {complaint.resolution ? (
          <div
            className="
              rounded-xl border
              border-emerald-200 bg-emerald-50
              p-4
            "
          >
            <p
              className="
                text-xs font-semibold uppercase
                text-emerald-700
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

            {complaint.resolved_at ? (
              <p
                className="
                  mt-2 text-xs text-emerald-700
                "
              >
                Resolved{" "}
                {formatDateTime(
                  complaint.resolved_at,
                )}
              </p>
            ) : null}
          </div>
        ) : null}
      </div>
    </article>
  );
}


function ComplaintDialog({
  initialDonationId,
  submitting,
  error,
  onClose,
  onSubmit,
}) {
  const [targetType, setTargetType] =
    useState(
      initialDonationId
        ? "DONATION"
        : "DONATION",
    );

  const [donationId, setDonationId] =
    useState(initialDonationId || "");

  const [reportedUserId, setReportedUserId] =
    useState("");

  const [description, setDescription] =
    useState("");

  useEffect(() => {
    setDonationId(
      initialDonationId || "",
    );
  }, [initialDonationId]);

  function handleSubmit(event) {
    event.preventDefault();

    const payload = {
      description: description.trim(),
    };

    if (targetType === "DONATION") {
      payload.donation_id =
        donationId.trim();
    } else {
      payload.reported_user_id =
        reportedUserId.trim();
    }

    onSubmit(payload);
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
        aria-labelledby="complaint-dialog-title"
        className="
          max-h-[90vh] w-full overflow-y-auto
          rounded-t-3xl bg-white shadow-2xl
          sm:max-w-xl sm:rounded-3xl
        "
      >
        <div
          className="
            sticky top-0 flex items-start
            justify-between border-b
            border-slate-200 bg-white/90
            p-5 backdrop-blur
          "
        >
          <div>
            <p
              className="
                text-sm font-semibold uppercase
                tracking-wide text-red-600
              "
            >
              Report a problem
            </p>

            <h2
              id="complaint-dialog-title"
              className="
                mt-1 text-xl font-bold
                text-slate-900
              "
            >
              Submit complaint
            </h2>
          </div>

          <button
            type="button"
            disabled={submitting}
            onClick={onClose}
            aria-label="Close complaint form"
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
          <fieldset>
            <legend
              className="
                mb-3 text-sm font-semibold
                text-slate-900
              "
            >
              What does this complaint concern?
            </legend>

            <div
              className="
                grid gap-3 sm:grid-cols-2
              "
            >
              <label
                className={`
                  cursor-pointer rounded-xl border
                  p-4 transition
                  ${
                    targetType === "DONATION"
                      ? (
                          "border-blue-500 bg-blue-50 " +
                          "ring-1 ring-blue-500"
                        )
                      : (
                          "border-slate-200 " +
                          "hover:border-blue-300"
                        )
                  }
                `}
              >
                <input
                  type="radio"
                  name="target_type"
                  value="DONATION"
                  checked={
                    targetType === "DONATION"
                  }
                  onChange={(event) =>
                    setTargetType(
                      event.target.value,
                    )
                  }
                  className="sr-only"
                />

                <span
                  className="
                    font-semibold text-slate-900
                  "
                >
                  Donation issue
                </span>

                <span
                  className="
                    mt-1 block text-sm
                    text-slate-600
                  "
                >
                  Food, pickup, delivery or quantity
                  problem.
                </span>
              </label>

              <label
                className={`
                  cursor-pointer rounded-xl border
                  p-4 transition
                  ${
                    targetType === "PARTICIPANT"
                      ? (
                          "border-blue-500 bg-blue-50 " +
                          "ring-1 ring-blue-500"
                        )
                      : (
                          "border-slate-200 " +
                          "hover:border-blue-300"
                        )
                  }
                `}
              >
                <input
                  type="radio"
                  name="target_type"
                  value="PARTICIPANT"
                  checked={
                    targetType === "PARTICIPANT"
                  }
                  onChange={(event) =>
                    setTargetType(
                      event.target.value,
                    )
                  }
                  className="sr-only"
                />

                <span
                  className="
                    font-semibold text-slate-900
                  "
                >
                  Participant issue
                </span>

                <span
                  className="
                    mt-1 block text-sm
                    text-slate-600
                  "
                >
                  Report a donor, receiver or
                  volunteer.
                </span>
              </label>
            </div>
          </fieldset>

          {targetType === "DONATION" ? (
            <label className="block">
              <span
                className="
                  mb-2 block text-sm font-semibold
                  text-slate-900
                "
              >
                Donation ID
              </span>

              <input
                type="text"
                required
                value={donationId}
                onChange={(event) =>
                  setDonationId(
                    event.target.value,
                  )
                }
                placeholder="Enter the donation UUID"
                className="
                  w-full rounded-xl border
                  border-slate-300 px-4 py-3
                  text-slate-900 outline-none
                  focus:border-blue-500
                  focus:ring-2
                  focus:ring-blue-500/20
                "
              />
            </label>
          ) : (
            <label className="block">
              <span
                className="
                  mb-2 block text-sm font-semibold
                  text-slate-900
                "
              >
                Participant user ID
              </span>

              <input
                type="text"
                required
                value={reportedUserId}
                onChange={(event) =>
                  setReportedUserId(
                    event.target.value,
                  )
                }
                placeholder="Enter the participant UUID"
                className="
                  w-full rounded-xl border
                  border-slate-300 px-4 py-3
                  text-slate-900 outline-none
                  focus:border-blue-500
                  focus:ring-2
                  focus:ring-blue-500/20
                "
              />
            </label>
          )}

          <label className="block">
            <span
              className="
                mb-2 block text-sm font-semibold
                text-slate-900
              "
            >
              Describe the problem
            </span>

            <textarea
              required
              minLength={10}
              maxLength={8000}
              rows={6}
              value={description}
              onChange={(event) =>
                setDescription(
                  event.target.value,
                )
              }
              placeholder={
                "Explain what happened, when it " +
                "happened and what outcome you expect."
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

            <p className="mt-1 text-xs text-slate-500">
              {description.length}/8000 characters
            </p>
          </label>

          <div
            className="
              rounded-xl border border-amber-200
              bg-amber-50 p-4 text-sm
              text-amber-800
            "
          >
            Submitting a complaint does not
            automatically cancel or complete a
            donation. Administrators review the
            complaint separately.
          </div>

          <PageMessage
            message={error}
          />

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
                description.trim().length < 10 ||
                (
                  targetType === "DONATION" &&
                  !donationId.trim()
                ) ||
                (
                  targetType === "PARTICIPANT" &&
                  !reportedUserId.trim()
                )
              }
              className="
                inline-flex items-center
                justify-center gap-2 rounded-xl
                bg-red-600 px-5 py-3
                font-semibold text-white
                transition hover:bg-red-700
                active:scale-[0.98]
                disabled:cursor-not-allowed
                disabled:opacity-60
              "
            >
              {submitting ? (
                <>
                  <LoaderCircle
                    className="
                      h-5 w-5 animate-spin
                    "
                  />
                  Submitting...
                </>
              ) : (
                <>
                  <Send className="h-5 w-5" />
                  Submit complaint
                </>
              )}
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}


export default function ComplaintsPage() {
  const [searchParams] =
    useSearchParams();

  const initialDonationId =
    searchParams.get("donationId") || "";

  const [complaints, setComplaints] =
    useState([]);

  const [filter, setFilter] =
    useState("ALL");

  const [loading, setLoading] =
    useState(true);

  const [submitting, setSubmitting] =
    useState(false);

  const [showDialog, setShowDialog] =
    useState(Boolean(initialDonationId));

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
      if (filter === "ALL") {
        return complaints;
      }

      return complaints.filter(
        (complaint) =>
          complaint.status === filter,
      );
    }, [
      complaints,
      filter,
    ]);

  async function submitComplaint(payload) {
    setSubmitting(true);
    setDialogError("");
    setSuccess("");

    try {
      await api.post(
        "/complaints/",
        payload,
      );

      setShowDialog(false);

      setSuccess(
        "Your complaint was submitted successfully.",
      );

      await loadComplaints();
    } catch (requestError) {
      setDialogError(
        getErrorMessage(requestError),
      );
    } finally {
      setSubmitting(false);
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
              Help and reporting
            </p>

            <h1 className="mt-2 text-3xl font-bold">
              Complaints and support
            </h1>

            <p
              className="
                mt-3 max-w-2xl text-blue-50
              "
            >
              Report a donation, delivery or
              participant problem and track its
              resolution.
            </p>
          </div>

          <button
            type="button"
            onClick={() => {
              setDialogError("");
              setShowDialog(true);
            }}
            className="
              inline-flex items-center
              justify-center gap-2 rounded-xl
              bg-white px-5 py-3
              font-semibold text-blue-700
              transition hover:bg-blue-50
              active:scale-[0.98]
            "
          >
            <Plus className="h-5 w-5" />
            New complaint
          </button>
        </div>
      </header>

      <PageMessage
        message={error}
      />

      <PageMessage
        type="success"
        message={success}
      />

      <section
        className="
          overflow-x-auto rounded-2xl
          border border-slate-200
          bg-white p-2 shadow-sm
        "
      >
        <div className="flex min-w-max gap-2">
          {[
            "ALL",
            "OPEN",
            "UNDER_REVIEW",
            "RESOLVED",
          ].map((status) => (
            <button
              key={status}
              type="button"
              onClick={() =>
                setFilter(status)
              }
              className={`
                rounded-xl px-4 py-2.5
                text-sm font-semibold transition
                ${
                  filter === status
                    ? "bg-blue-600 text-white"
                    : (
                        "text-slate-600 " +
                        "hover:bg-slate-100"
                      )
                }
              `}
            >
              {formatStatus(status)}
            </button>
          ))}

          <button
            type="button"
            onClick={loadComplaints}
            disabled={loading}
            className="
              ml-auto inline-flex items-center
              gap-2 rounded-xl px-4 py-2.5
              text-sm font-semibold
              text-slate-600 hover:bg-slate-100
            "
          >
            <RefreshCw
              className={`
                h-4 w-4
                ${loading ? "animate-spin" : ""}
              `}
            />
            Refresh
          </button>
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
                h-72 animate-pulse rounded-2xl
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
          <FileWarning
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
            Complaints you submit will appear here.
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
            (complaint) => (
              <ComplaintCard
                key={complaint.id}
                complaint={complaint}
              />
            ),
          )}
        </section>
      ) : null}

      {showDialog ? (
        <ComplaintDialog
          initialDonationId={initialDonationId}
          submitting={submitting}
          error={dialogError}
          onClose={() => {
            if (!submitting) {
              setShowDialog(false);
              setDialogError("");
            }
          }}
          onSubmit={submitComplaint}
        />
      ) : null}
    </main>
  );
}