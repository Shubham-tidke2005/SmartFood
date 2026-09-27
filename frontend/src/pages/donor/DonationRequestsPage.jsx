import {
  AlertCircle,
  CalendarClock,
  Check,
  CheckCircle2,
  ClipboardCheck,
  Clock3,
  HandHeart,
  LoaderCircle,
  Package,
  RefreshCw,
  Truck,
  UserRoundCheck,
  X,
  XCircle,
} from "lucide-react";

import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  Link,
} from "react-router-dom";

import api from "../../lib/api";


const STATUS_STYLES = {
  PENDING:
    "border-amber-200 bg-amber-50 text-amber-700",

  APPROVED:
    "border-emerald-200 bg-emerald-50 text-emerald-700",

  REJECTED:
    "border-red-200 bg-red-50 text-red-700",

  WITHDRAWN:
    "border-slate-200 bg-slate-100 text-slate-600",

  EXPIRED:
    "border-red-200 bg-red-50 text-red-700",

  CANCELLED:
    "border-slate-200 bg-slate-100 text-slate-600",
};


const TRANSPORT_MODES = {
  RECEIVER_COLLECTION: {
    label: "Receiver collection",
    description:
      "The receiver will collect food from the donor.",
    icon: UserRoundCheck,
  },

  DONOR_DELIVERY: {
    label: "Donor delivery",
    description:
      "The donor will deliver food to the receiver.",
    icon: Truck,
  },

  VOLUNTEER_DELIVERY: {
    label: "Volunteer delivery",
    description:
      "A volunteer transport task will be required.",
    icon: HandHeart,
  },
};


function getResults(data) {
  if (Array.isArray(data)) {
    return data;
  }

  if (Array.isArray(data?.results)) {
    return data.results;
  }

  if (Array.isArray(data?.requests)) {
    return data.requests;
  }

  return [];
}


function getErrorMessage(error) {
  const data = error?.response?.data;

  if (!data) {
    return (
      "Could not connect to the SmartFood server. " +
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


function formatTransportMode(value) {
  return (
    TRANSPORT_MODES[value]?.label ||
    value?.replaceAll("_", " ") ||
    "Not selected"
  );
}


function StatusBadge({
  status,
}) {
  return (
    <span
      className={`
        inline-flex rounded-full border px-3 py-1
        text-xs font-bold uppercase tracking-wide
        ${
          STATUS_STYLES[status] ||
          "border-slate-200 bg-slate-100 text-slate-700"
        }
      `}
    >
      {status?.replaceAll("_", " ") || "Unknown"}
    </span>
  );
}


function RequestCard({
  request,
  processingId,
  onApprove,
  onReject,
}) {
  const mode =
    TRANSPORT_MODES[request.proposed_mode];

  const ModeIcon = mode?.icon || Truck;

  const processing =
    processingId === request.id;

  const pending =
    request.status === "PENDING";

  const approved =
    request.status === "APPROVED";

  const usesDirectFulfilment =
    request.proposed_mode ===
      "RECEIVER_COLLECTION" ||
    request.proposed_mode ===
      "DONOR_DELIVERY";

  const usesVolunteer =
    request.proposed_mode ===
    "VOLUNTEER_DELIVERY";

  return (
    <article
      className="
        rounded-2xl border border-slate-200/80
        bg-white p-5 shadow-sm
        transition-all duration-200
        hover:-translate-y-1 hover:shadow-xl
        hover:shadow-blue-500/5
      "
    >
      <div
        className="
          flex flex-col gap-4 sm:flex-row
          sm:items-start sm:justify-between
        "
      >
        <div className="min-w-0">
          <div
            className="
              flex flex-wrap items-center gap-2
            "
          >
            <StatusBadge
              status={request.status}
            />

            <span className="text-xs text-slate-500">
              Requested{" "}
              {formatDateTime(request.created_at)}
            </span>
          </div>

          <h2
            className="
              mt-3 text-xl font-bold text-slate-900
            "
          >
            {request.food_name || "Food donation"}
          </h2>

          <p className="mt-1 text-sm text-slate-600">
            Requested by{" "}
            <strong className="text-slate-900">
              {request.receiver_name ||
                "Receiver organization"}
            </strong>
          </p>

          {request.receiver_email ? (
            <p className="mt-1 text-sm text-slate-500">
              {request.receiver_email}
            </p>
          ) : null}
        </div>

        <div
          className="
            flex h-12 w-12 shrink-0 items-center
            justify-center rounded-2xl bg-blue-50
            text-blue-600
          "
        >
          <Package
            className="h-6 w-6"
            aria-hidden="true"
          />
        </div>
      </div>

      <div
        className="
          mt-5 grid gap-3 sm:grid-cols-2
        "
      >
        <div className="rounded-xl bg-slate-50 p-4">
          <p
            className="
              text-xs font-medium text-slate-500
            "
          >
            Requested quantity
          </p>

          <p className="mt-1 font-bold text-slate-900">
            {request.quantity} {request.unit}
          </p>
        </div>

        <div className="rounded-xl bg-slate-50 p-4">
          <p
            className="
              text-xs font-medium text-slate-500
            "
          >
            Food category
          </p>

          <p className="mt-1 font-bold text-slate-900">
            {request.category_name ||
              "Not specified"}
          </p>
        </div>
      </div>

      <div
        className="
          mt-3 rounded-xl border
          border-slate-200 p-4
        "
      >
        <div className="flex items-start gap-3">
          <span
            className="
              rounded-xl bg-sky-50 p-2
              text-sky-600
            "
          >
            <ModeIcon
              className="h-5 w-5"
              aria-hidden="true"
            />
          </span>

          <div>
            <p className="font-semibold text-slate-900">
              {formatTransportMode(
                request.proposed_mode,
              )}
            </p>

            <p className="mt-1 text-sm text-slate-600">
              {mode?.description ||
                (
                  "Transport arrangement selected " +
                  "by the receiver."
                )}
            </p>
          </div>
        </div>
      </div>

      <div
        className="
          mt-3 flex items-start gap-3
          rounded-xl border border-amber-100
          bg-amber-50 p-4
        "
      >
        <CalendarClock
          className="
            mt-0.5 h-5 w-5 shrink-0
            text-amber-600
          "
          aria-hidden="true"
        />

        <div>
          <p
            className="
              text-sm font-semibold text-amber-900
            "
          >
            Pickup deadline
          </p>

          <p className="mt-1 text-sm text-amber-800">
            {formatDateTime(
              request.pickup_deadline,
            )}
          </p>
        </div>
      </div>

      {request.reason ? (
        <div
          className="
            mt-3 rounded-xl border
            border-slate-200 bg-slate-50 p-4
          "
        >
          <p
            className="
              text-xs font-semibold text-slate-500
            "
          >
            Decision reason
          </p>

          <p className="mt-1 text-sm text-slate-700">
            {request.reason}
          </p>
        </div>
      ) : null}

      {pending ? (
        <div
          className="
            mt-5 flex flex-col-reverse gap-3
            sm:flex-row sm:justify-end
          "
        >
          <button
            type="button"
            disabled={processing}
            onClick={() => onReject(request)}
            className="
              inline-flex items-center justify-center
              gap-2 rounded-xl border
              border-red-200 px-5 py-2.5
              font-semibold text-red-700 transition
              hover:bg-red-50 active:scale-[0.98]
              focus-visible:outline-none
              focus-visible:ring-2
              focus-visible:ring-red-500
              disabled:cursor-not-allowed
              disabled:opacity-60
            "
          >
            <XCircle
              className="h-5 w-5"
              aria-hidden="true"
            />

            Reject
          </button>

          <button
            type="button"
            disabled={processing}
            onClick={() => onApprove(request)}
            className="
              inline-flex items-center justify-center
              gap-2 rounded-xl bg-blue-600
              px-5 py-2.5 font-semibold text-white
              transition hover:bg-blue-700
              active:scale-[0.98]
              focus-visible:outline-none
              focus-visible:ring-2
              focus-visible:ring-blue-500
              focus-visible:ring-offset-2
              disabled:cursor-not-allowed
              disabled:bg-blue-300
            "
          >
            {processing ? (
              <LoaderCircle
                className="h-5 w-5 animate-spin"
                aria-hidden="true"
              />
            ) : (
              <Check
                className="h-5 w-5"
                aria-hidden="true"
              />
            )}

            Approve request
          </button>
        </div>
      ) : null}

      {approved && usesDirectFulfilment ? (
        <div className="mt-5">
          <Link
            to={`/fulfilment/${request.donation}`}
            className="
              inline-flex w-full items-center
              justify-center gap-2 rounded-xl
              bg-blue-600 px-5 py-3
              font-semibold text-white transition
              hover:bg-blue-700
              active:scale-[0.98]
              focus-visible:outline-none
              focus-visible:ring-2
              focus-visible:ring-blue-500
              focus-visible:ring-offset-2
            "
          >
            <ClipboardCheck
              className="h-5 w-5"
              aria-hidden="true"
            />

            Manage fulfilment
          </Link>

          <p
            className="
              mt-2 text-center text-xs
              text-slate-500
            "
          >
            Record handover, delivery and receipt
            confirmation.
          </p>
        </div>
      ) : null}

      {approved && usesVolunteer ? (
        <div
          className="
            mt-5 flex items-start gap-3
            rounded-xl border border-blue-200
            bg-blue-50 p-4 text-blue-800
          "
        >
          <HandHeart
            className="
              mt-0.5 h-5 w-5 shrink-0
            "
            aria-hidden="true"
          />

          <div>
            <p className="font-semibold">
              Volunteer transport required
            </p>

            <p className="mt-1 text-sm">
              A volunteer task will be used for pickup
              and delivery.
            </p>
          </div>
        </div>
      ) : null}
    </article>
  );
}


function DecisionDialog({
  decision,
  processing,
  error,
  onClose,
  onConfirm,
}) {
  const [reason, setReason] = useState("");

  useEffect(() => {
    setReason("");
  }, [decision]);

  if (!decision) {
    return null;
  }

  const approving =
    decision.type === "approve";

  const request =
    decision.request;

  function handleSubmit(event) {
    event.preventDefault();

    if (
      !approving &&
      reason.trim().length < 3
    ) {
      return;
    }

    onConfirm(reason.trim());
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
          !processing
        ) {
          onClose();
        }
      }}
    >
      <section
        role="dialog"
        aria-modal="true"
        aria-labelledby="decision-dialog-title"
        className="
          w-full rounded-t-3xl bg-white
          shadow-2xl
          sm:max-w-lg sm:rounded-3xl
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
              className={`
                text-sm font-semibold uppercase
                tracking-wide
                ${
                  approving
                    ? "text-blue-600"
                    : "text-red-600"
                }
              `}
            >
              {approving
                ? "Approve request"
                : "Reject request"}
            </p>

            <h2
              id="decision-dialog-title"
              className="
                mt-1 text-xl font-bold
                text-slate-900
              "
            >
              {request.food_name}
            </h2>
          </div>

          <button
            type="button"
            disabled={processing}
            onClick={onClose}
            aria-label="Close dialog"
            className="
              rounded-xl p-2 text-slate-500
              transition hover:bg-slate-100
              focus-visible:outline-none
              focus-visible:ring-2
              focus-visible:ring-blue-500
            "
          >
            <X
              className="h-5 w-5"
              aria-hidden="true"
            />
          </button>
        </div>

        <form
          onSubmit={handleSubmit}
          className="space-y-5 p-5"
        >
          <div
            className={`
              rounded-2xl border p-4
              ${
                approving
                  ? "border-blue-100 bg-blue-50"
                  : "border-red-100 bg-red-50"
              }
            `}
          >
            <p
              className={`
                text-sm
                ${
                  approving
                    ? "text-blue-900"
                    : "text-red-900"
                }
              `}
            >
              {approving ? (
                <>
                  Approve{" "}
                  <strong>
                    {request.receiver_name}
                  </strong>{" "}
                  for {request.quantity}{" "}
                  {request.unit}. Other pending
                  requests for this donation will be
                  closed automatically.
                </>
              ) : (
                <>
                  Reject the request submitted by{" "}
                  <strong>
                    {request.receiver_name}
                  </strong>
                  .
                </>
              )}
            </p>
          </div>

          <label className="block">
            <span
              className="
                mb-2 block text-sm font-semibold
                text-slate-900
              "
            >
              {approving
                ? "Decision note (optional)"
                : "Rejection reason"}
            </span>

            <textarea
              value={reason}
              onChange={(event) =>
                setReason(event.target.value)
              }
              required={!approving}
              minLength={
                approving ? undefined : 3
              }
              maxLength={1000}
              rows={4}
              placeholder={
                approving
                  ? (
                      "Add pickup or coordination " +
                      "instructions..."
                    )
                  : (
                      "Explain why this request was " +
                      "rejected..."
                    )
              }
              className="
                w-full resize-none rounded-xl
                border border-slate-300
                px-4 py-3 text-slate-900
                outline-none transition
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
                bg-red-50 p-3 text-sm
                text-red-700
              "
            >
              <AlertCircle
                className="
                  mt-0.5 h-5 w-5 shrink-0
                "
                aria-hidden="true"
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
              disabled={processing}
              onClick={onClose}
              className="
                rounded-xl border
                border-slate-300 px-5 py-3
                font-semibold text-slate-700
                transition hover:bg-slate-50
                disabled:cursor-not-allowed
                disabled:opacity-60
              "
            >
              Go back
            </button>

            <button
              type="submit"
              disabled={
                processing ||
                (
                  !approving &&
                  reason.trim().length < 3
                )
              }
              className={`
                inline-flex items-center
                justify-center gap-2 rounded-xl
                px-5 py-3 font-semibold
                text-white transition
                active:scale-[0.98]
                disabled:cursor-not-allowed
                disabled:opacity-60
                ${
                  approving
                    ? (
                        "bg-blue-600 " +
                        "hover:bg-blue-700"
                      )
                    : (
                        "bg-red-600 " +
                        "hover:bg-red-700"
                      )
                }
              `}
            >
              {processing ? (
                <LoaderCircle
                  className="
                    h-5 w-5 animate-spin
                  "
                  aria-hidden="true"
                />
              ) : approving ? (
                <Check
                  className="h-5 w-5"
                  aria-hidden="true"
                />
              ) : (
                <XCircle
                  className="h-5 w-5"
                  aria-hidden="true"
                />
              )}

              {processing
                ? "Processing..."
                : approving
                  ? "Confirm approval"
                  : "Confirm rejection"}
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}


export default function DonationRequestsPage() {
  const [requests, setRequests] =
    useState([]);

  const [activeStatus, setActiveStatus] =
    useState("PENDING");

  const [decision, setDecision] =
    useState(null);

  const [processingId, setProcessingId] =
    useState(null);

  const [loading, setLoading] =
    useState(true);

  const [loadError, setLoadError] =
    useState("");

  const [decisionError, setDecisionError] =
    useState("");

  const [successMessage, setSuccessMessage] =
    useState("");

  async function loadRequests() {
    setLoading(true);
    setLoadError("");

    try {
      /*
       * Django determines whether the authenticated
       * participant is the donor or receiver.
       */
      const response = await api.get(
        "/donations/requests/",
      );

      setRequests(
        getResults(response.data),
      );
    } catch (error) {
      setLoadError(
        getErrorMessage(error),
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadRequests();
  }, []);

  const counts = useMemo(() => {
    return requests.reduce(
      (result, request) => {
        result.ALL += 1;

        if (
          result[request.status] !== undefined
        ) {
          result[request.status] += 1;
        }

        return result;
      },
      {
        ALL: 0,
        PENDING: 0,
        APPROVED: 0,
        REJECTED: 0,
      },
    );
  }, [requests]);

  const visibleRequests = useMemo(() => {
    if (activeStatus === "ALL") {
      return requests;
    }

    return requests.filter(
      (request) =>
        request.status === activeStatus,
    );
  }, [
    requests,
    activeStatus,
  ]);

  function openDecision(
    type,
    request,
  ) {
    setDecisionError("");
    setSuccessMessage("");

    setDecision({
      type,
      request,
    });
  }

  function closeDecision() {
    if (processingId) {
      return;
    }

    setDecision(null);
    setDecisionError("");
  }

  async function confirmDecision(reason) {
    if (!decision) {
      return;
    }

    const requestId =
      decision.request.id;

    const approving =
      decision.type === "approve";

    setProcessingId(requestId);
    setDecisionError("");

    try {
      const endpoint = approving
        ? (
            `/donations/requests/` +
            `${requestId}/approve/`
          )
        : (
            `/donations/requests/` +
            `${requestId}/reject/`
          );

      await api.post(endpoint, {
        reason,
      });

      setDecision(null);

      setSuccessMessage(
        approving
          ? (
              "The request was approved successfully. " +
              "Other pending requests for this " +
              "donation were closed."
            )
          : (
              "The request was rejected " +
              "successfully."
            ),
      );

      await loadRequests();
    } catch (error) {
      setDecisionError(
        getErrorMessage(error),
      );
    } finally {
      setProcessingId(null);
    }
  }

  const tabs = [
    {
      value: "PENDING",
      label: "Pending",
      count: counts.PENDING,
    },
    {
      value: "APPROVED",
      label: "Approved",
      count: counts.APPROVED,
    },
    {
      value: "REJECTED",
      label: "Rejected",
      count: counts.REJECTED,
    },
    {
      value: "ALL",
      label: "All",
      count: counts.ALL,
    },
  ];

  const emptyTitle =
    activeStatus === "ALL"
      ? "No requests found"
      : (
          `No ${activeStatus.toLowerCase()} ` +
          "requests"
        );

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
              Donation requests
            </p>

            <h1
              className="
                mt-2 text-3xl font-bold
              "
            >
              Review receiver requests
            </h1>

            <p
              className="
                mt-3 max-w-2xl text-blue-50
              "
            >
              Select one suitable receiver and confirm
              the transport arrangement.
            </p>
          </div>

          <button
            type="button"
            onClick={loadRequests}
            disabled={loading}
            className="
              inline-flex items-center
              justify-center gap-2 rounded-xl
              bg-white/15 px-4 py-3
              font-semibold text-white
              backdrop-blur transition
              hover:bg-white/25
              disabled:cursor-not-allowed
              disabled:opacity-60
            "
          >
            <RefreshCw
              className={`
                h-5 w-5
                ${loading ? "animate-spin" : ""}
              `}
              aria-hidden="true"
            />

            Refresh
          </button>
        </div>
      </header>

      {successMessage ? (
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
            aria-hidden="true"
          />

          <span>{successMessage}</span>
        </div>
      ) : null}

      <section
        className="
          overflow-x-auto rounded-2xl
          border border-slate-200
          bg-white p-2 shadow-sm
        "
      >
        <div
          className="flex min-w-max gap-2"
          role="tablist"
          aria-label="Request status"
        >
          {tabs.map((tab) => (
            <button
              key={tab.value}
              type="button"
              role="tab"
              aria-selected={
                activeStatus === tab.value
              }
              onClick={() =>
                setActiveStatus(tab.value)
              }
              className={`
                inline-flex items-center gap-2
                rounded-xl px-4 py-2.5
                text-sm font-semibold transition
                ${
                  activeStatus === tab.value
                    ? "bg-blue-600 text-white"
                    : (
                        "text-slate-600 " +
                        "hover:bg-slate-100"
                      )
                }
              `}
            >
              {tab.label}

              <span
                className={`
                  rounded-full px-2 py-0.5
                  text-xs
                  ${
                    activeStatus === tab.value
                      ? "bg-white/20 text-white"
                      : (
                          "bg-slate-100 " +
                          "text-slate-600"
                        )
                  }
                `}
              >
                {tab.count}
              </span>
            </button>
          ))}
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
                animate-pulse rounded-2xl
                border border-slate-200
                bg-white p-5
              "
            >
              <div
                className="
                  h-5 w-1/3 rounded
                  bg-slate-200
                "
              />

              <div
                className="
                  mt-4 h-7 w-2/3 rounded
                  bg-slate-200
                "
              />

              <div
                className="
                  mt-5 h-24 rounded-xl
                  bg-slate-100
                "
              />

              <div
                className="
                  mt-3 h-20 rounded-xl
                  bg-slate-100
                "
              />
            </div>
          ))}
        </section>
      ) : null}

      {!loading && loadError ? (
        <section
          className="
            rounded-2xl border border-red-200
            bg-red-50 p-6 text-center
          "
        >
          <AlertCircle
            className="
              mx-auto h-10 w-10 text-red-500
            "
            aria-hidden="true"
          />

          <h2
            className="
              mt-3 font-bold text-red-900
            "
          >
            Requests could not be loaded
          </h2>

          <p className="mt-2 text-sm text-red-700">
            {loadError}
          </p>

          <button
            type="button"
            onClick={loadRequests}
            className="
              mt-4 rounded-xl bg-red-600
              px-5 py-2.5 font-semibold
              text-white transition
              hover:bg-red-700
            "
          >
            Try again
          </button>
        </section>
      ) : null}

      {!loading &&
      !loadError &&
      visibleRequests.length === 0 ? (
        <section
          className="
            rounded-2xl border border-dashed
            border-slate-300 bg-white
            p-10 text-center
          "
        >
          <Clock3
            className="
              mx-auto h-12 w-12
              text-slate-300
            "
            aria-hidden="true"
          />

          <h2
            className="
              mt-4 text-lg font-bold
              text-slate-900
            "
          >
            {emptyTitle}
          </h2>

          <p className="mt-2 text-sm text-slate-600">
            Requests submitted by receivers will
            appear here.
          </p>
        </section>
      ) : null}

      {!loading &&
      !loadError &&
      visibleRequests.length > 0 ? (
        <section
          className="
            grid gap-5 lg:grid-cols-2
          "
        >
          {visibleRequests.map((request) => (
            <RequestCard
              key={request.id}
              request={request}
              processingId={processingId}
              onApprove={(item) =>
                openDecision("approve", item)
              }
              onReject={(item) =>
                openDecision("reject", item)
              }
            />
          ))}
        </section>
      ) : null}

      <DecisionDialog
        decision={decision}
        processing={Boolean(processingId)}
        error={decisionError}
        onClose={closeDecision}
        onConfirm={confirmDecision}
      />
    </main>
  );
}