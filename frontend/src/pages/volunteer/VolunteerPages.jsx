import {
  AlertCircle,
  ArrowLeft,
  CalendarClock,
  Check,
  CheckCircle2,
  CircleDot,
  Clock3,
  History,
  LoaderCircle,
  MapPin,
  Navigation,
  Package,
  RefreshCw,
  RotateCcw,
  Truck,
  UserRoundCheck,
  X,
  XCircle,
} from "lucide-react";

import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  Link,
  useNavigate,
  useParams,
} from "react-router-dom";

import api from "../../lib/api";


const TASK_STATUS_STYLES = {
  OPEN:
    "border-sky-200 bg-sky-50 text-sky-700",

  ASSIGNED:
    "border-blue-200 bg-blue-50 text-blue-700",

  ARRIVED_AT_DONOR:
    "border-indigo-200 bg-indigo-50 text-indigo-700",

  PICKED_UP:
    "border-amber-200 bg-amber-50 text-amber-700",

  ARRIVED_AT_RECEIVER:
    "border-purple-200 bg-purple-50 text-purple-700",

  DELIVERED:
    "border-emerald-200 bg-emerald-50 text-emerald-700",

  COMPLETED:
    "border-emerald-200 bg-emerald-50 text-emerald-700",

  CANCELLED:
    "border-slate-200 bg-slate-100 text-slate-600",

  FAILED:
    "border-red-200 bg-red-50 text-red-700",
};


const ACTIVE_STATUSES = [
  "ASSIGNED",
  "ARRIVED_AT_DONOR",
  "PICKED_UP",
  "ARRIVED_AT_RECEIVER",
  "DELIVERED",
];


const HISTORY_STATUSES = [
  "COMPLETED",
  "CANCELLED",
  "FAILED",
];


function getResults(data) {
  if (Array.isArray(data)) {
    return data;
  }

  if (Array.isArray(data?.results)) {
    return data.results;
  }

  if (Array.isArray(data?.tasks)) {
    return data.tasks;
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


function getCurrentLocalDateTime() {
  const date = new Date();

  const offset =
    date.getTimezoneOffset();

  return new Date(
    date.getTime() -
      offset * 60 * 1000,
  )
    .toISOString()
    .slice(0, 16);
}


function toISOString(value) {
  if (!value) {
    return new Date().toISOString();
  }

  return new Date(value).toISOString();
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
  if (!status) {
    return "Unknown";
  }

  return status
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/\b\w/g, (letter) =>
      letter.toUpperCase(),
    );
}


function getFoodName(task) {
  return (
    task.food_name ||
    task.donation_name ||
    task.donation?.food_name ||
    task.donation?.current_revision?.food_name ||
    "Food donation"
  );
}


function getPickupArea(task) {
  return (
    task.pickup_area ||
    task.pickup_location ||
    task.donor_area ||
    "Pickup location unavailable"
  );
}


function getReceiverArea(task) {
  return (
    task.receiver_area ||
    task.receiver_service_area_name ||
    task.receiver_service_area?.name ||
    task.delivery_area ||
    task.receiver_address ||
    "Receiver location unavailable"
  );
}


function TaskStatusBadge({
  status,
}) {
  return (
    <span
      className={`
        inline-flex rounded-full border
        px-3 py-1 text-xs font-bold
        uppercase tracking-wide
        ${
          TASK_STATUS_STYLES[status] ||
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


function TaskInformation({
  label,
  value,
}) {
  return (
    <div className="rounded-xl bg-slate-50 p-4">
      <p className="text-xs font-medium text-slate-500">
        {label}
      </p>

      <p className="mt-1 font-semibold text-slate-900">
        {value || "Not available"}
      </p>
    </div>
  );
}


function TaskCard({
  task,
  acceptingId,
  onAccept,
}) {
  const accepting =
    acceptingId === task.id;

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
          flex items-start justify-between gap-4
        "
      >
        <div>
          <TaskStatusBadge
            status={task.status}
          />

          <h2
            className="
              mt-3 text-xl font-bold text-slate-900
            "
          >
            {getFoodName(task)}
          </h2>

          <p className="mt-1 text-sm text-slate-600">
            {task.required_quantity} {task.unit}
          </p>
        </div>

        <span
          className="
            flex h-12 w-12 shrink-0 items-center
            justify-center rounded-2xl bg-blue-50
            text-blue-600
          "
        >
          <Truck
            className="h-6 w-6"
            aria-hidden="true"
          />
        </span>
      </div>

      <div className="mt-5 space-y-3">
        <div
          className="
            flex items-start gap-3
            rounded-xl bg-slate-50 p-4
          "
        >
          <MapPin
            className="
              mt-0.5 h-5 w-5 shrink-0
              text-blue-600
            "
            aria-hidden="true"
          />

          <div>
            <p
              className="
                text-xs font-semibold
                uppercase text-slate-500
              "
            >
              Pickup
            </p>

            <p
              className="
                mt-1 text-sm font-medium
                text-slate-900
              "
            >
              {getPickupArea(task)}
            </p>
          </div>
        </div>

        <div
          className="
            flex items-start gap-3
            rounded-xl bg-slate-50 p-4
          "
        >
          <Navigation
            className="
              mt-0.5 h-5 w-5 shrink-0
              text-sky-600
            "
            aria-hidden="true"
          />

          <div>
            <p
              className="
                text-xs font-semibold
                uppercase text-slate-500
              "
            >
              Deliver to
            </p>

            <p
              className="
                mt-1 text-sm font-medium
                text-slate-900
              "
            >
              {getReceiverArea(task)}
            </p>
          </div>
        </div>

        <div
          className="
            flex items-start gap-3
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
                text-xs font-semibold uppercase
                text-amber-700
              "
            >
              Pickup deadline
            </p>

            <p
              className="
                mt-1 text-sm font-medium
                text-amber-900
              "
            >
              {formatDateTime(
                task.pickup_deadline,
              )}
            </p>
          </div>
        </div>
      </div>

      {task.approximate_distance_km ? (
        <p
          className="
            mt-4 text-sm text-slate-500
          "
        >
          Approximate straight-line distance:{" "}
          <strong className="text-slate-700">
            {task.approximate_distance_km} km
          </strong>
        </p>
      ) : null}

      <button
        type="button"
        disabled={accepting}
        onClick={() => onAccept(task)}
        className="
          mt-5 inline-flex w-full items-center
          justify-center gap-2 rounded-xl
          bg-blue-600 px-5 py-3
          font-semibold text-white transition
          hover:bg-blue-700 active:scale-[0.98]
          focus-visible:outline-none
          focus-visible:ring-2
          focus-visible:ring-blue-500
          focus-visible:ring-offset-2
          disabled:cursor-not-allowed
          disabled:bg-blue-300
        "
      >
        {accepting ? (
          <>
            <LoaderCircle
              className="h-5 w-5 animate-spin"
              aria-hidden="true"
            />
            Accepting...
          </>
        ) : (
          <>
            <Check
              className="h-5 w-5"
              aria-hidden="true"
            />
            Accept task
          </>
        )}
      </button>
    </article>
  );
}


function PageMessage({
  type = "error",
  message,
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
                "border-emerald-200 " +
                "bg-emerald-50 text-emerald-800"
              )
            : (
                "border-red-200 " +
                "bg-red-50 text-red-700"
              )
        }
      `}
    >
      {success ? (
        <CheckCircle2
          className="
            mt-0.5 h-5 w-5 shrink-0
          "
          aria-hidden="true"
        />
      ) : (
        <AlertCircle
          className="
            mt-0.5 h-5 w-5 shrink-0
          "
          aria-hidden="true"
        />
      )}

      <span>{message}</span>
    </div>
  );
}


function LoadingCards() {
  return (
    <section
      className="
        grid gap-5 sm:grid-cols-2
        xl:grid-cols-3
      "
    >
      {[1, 2, 3, 4, 5, 6].map((item) => (
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
              h-5 w-1/3 rounded bg-slate-200
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
  );
}


function EmptyState({
  title,
  description,
  icon: Icon = Package,
}) {
  return (
    <section
      className="
        rounded-2xl border border-dashed
        border-slate-300 bg-white
        p-10 text-center
      "
    >
      <Icon
        className="
          mx-auto h-12 w-12 text-slate-300
        "
        aria-hidden="true"
      />

      <h2
        className="
          mt-4 text-lg font-bold text-slate-900
        "
      >
        {title}
      </h2>

      <p className="mt-2 text-sm text-slate-600">
        {description}
      </p>
    </section>
  );
}


export function AvailableTasksPage() {
  const navigate = useNavigate();

  const [tasks, setTasks] =
    useState([]);

  const [loading, setLoading] =
    useState(true);

  const [acceptingId, setAcceptingId] =
    useState(null);

  const [error, setError] =
    useState("");

  const [success, setSuccess] =
    useState("");

  const loadTasks = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const response = await api.get(
        "/logistics/volunteer/tasks/eligible/",
      );

      setTasks(
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
    loadTasks();
  }, [loadTasks]);

  async function acceptTask(task) {
    setAcceptingId(task.id);
    setError("");
    setSuccess("");

    try {
      await api.post(
        (
          "/logistics/volunteer/tasks/" +
          `${task.id}/accept/`
        ),
        {},
      );

      setSuccess(
        "The transport task was assigned to you.",
      );

      navigate(
        `/volunteer/tasks/${task.id}`,
      );
    } catch (requestError) {
      setError(
        getErrorMessage(requestError),
      );

      await loadTasks();
    } finally {
      setAcceptingId(null);
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
              Volunteer transport
            </p>

            <h1
              className="
                mt-2 text-3xl font-bold
              "
            >
              Available pickup tasks
            </h1>

            <p
              className="
                mt-3 max-w-2xl text-blue-50
              "
            >
              Accept an eligible task and help deliver
              food before its pickup deadline.
            </p>
          </div>

          <button
            type="button"
            onClick={loadTasks}
            disabled={loading}
            className="
              inline-flex items-center
              justify-center gap-2 rounded-xl
              bg-white/15 px-4 py-3
              font-semibold text-white
              backdrop-blur transition
              hover:bg-white/25
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

      <PageMessage
        type="error"
        message={error}
      />

      <PageMessage
        type="success"
        message={success}
      />

      {loading ? (
        <LoadingCards />
      ) : null}

      {!loading &&
      !error &&
      tasks.length === 0 ? (
        <EmptyState
          title="No eligible tasks"
          description={
            "There are currently no transport tasks " +
            "matching your availability, service area " +
            "and carrying capacity."
          }
          icon={Truck}
        />
      ) : null}

      {!loading &&
      tasks.length > 0 ? (
        <section
          className="
            grid gap-5 sm:grid-cols-2
            xl:grid-cols-3
          "
        >
          {tasks.map((task) => (
            <TaskCard
              key={task.id}
              task={task}
              acceptingId={acceptingId}
              onAccept={acceptTask}
            />
          ))}
        </section>
      ) : null}
    </main>
  );
}


function ProgressStep({
  number,
  title,
  description,
  completed,
  active,
}) {
  return (
    <div className="flex gap-3">
      <div
        className={`
          flex h-9 w-9 shrink-0 items-center
          justify-center rounded-full border-2
          text-sm font-bold
          ${
            completed
              ? (
                  "border-emerald-500 " +
                  "bg-emerald-500 text-white"
                )
              : active
                ? (
                    "border-blue-600 " +
                    "bg-blue-600 text-white"
                  )
                : (
                    "border-slate-300 bg-white " +
                    "text-slate-400"
                  )
          }
        `}
      >
        {completed ? (
          <Check
            className="h-5 w-5"
            aria-hidden="true"
          />
        ) : (
          number
        )}
      </div>

      <div>
        <p
          className={`
            font-semibold
            ${
              completed || active
                ? "text-slate-900"
                : "text-slate-500"
            }
          `}
        >
          {title}
        </p>

        <p className="mt-1 text-sm text-slate-500">
          {description}
        </p>
      </div>
    </div>
  );
}


function QuantityDialog({
  action,
  task,
  submitting,
  error,
  onClose,
  onConfirm,
}) {
  const [quantity, setQuantity] =
    useState("");

  const [notes, setNotes] =
    useState("");

  const [dateValue, setDateValue] =
    useState(getCurrentLocalDateTime());

  useEffect(() => {
    setQuantity(
      String(task?.required_quantity || ""),
    );

    setNotes("");

    setDateValue(
      getCurrentLocalDateTime(),
    );
  }, [
    task,
    action,
  ]);

  if (!action || !task) {
    return null;
  }

  const pickup =
    action === "pickup";

  function handleSubmit(event) {
    event.preventDefault();

    onConfirm({
      actual_quantity: quantity,
      notes: notes.trim(),
      [pickup
        ? "picked_up_at"
        : "delivered_at"]: toISOString(
        dateValue,
      ),
    });
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
        aria-labelledby="quantity-dialog-title"
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
              className="
                text-sm font-semibold uppercase
                tracking-wide text-blue-600
              "
            >
              {pickup
                ? "Pickup confirmation"
                : "Delivery confirmation"}
            </p>

            <h2
              id="quantity-dialog-title"
              className="
                mt-1 text-xl font-bold text-slate-900
              "
            >
              {getFoodName(task)}
            </h2>
          </div>

          <button
            type="button"
            disabled={submitting}
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
            <X className="h-5 w-5" />
          </button>
        </div>

        <form
          onSubmit={handleSubmit}
          className="space-y-5 p-5"
        >
          <label className="block">
            <span
              className="
                mb-2 block text-sm font-semibold
                text-slate-900
              "
            >
              Actual quantity ({task.unit})
            </span>

            <input
              type="number"
              required
              min="0.001"
              step="0.001"
              value={quantity}
              onChange={(event) =>
                setQuantity(event.target.value)
              }
              className="
                w-full rounded-xl border
                border-slate-300 px-4 py-3
                text-slate-900 outline-none
                transition focus:border-blue-500
                focus:ring-2 focus:ring-blue-500/20
              "
            />
          </label>

          <label className="block">
            <span
              className="
                mb-2 block text-sm font-semibold
                text-slate-900
              "
            >
              {pickup
                ? "Picked up at"
                : "Delivered at"}
            </span>

            <input
              type="datetime-local"
              required
              value={dateValue}
              onChange={(event) =>
                setDateValue(event.target.value)
              }
              className="
                w-full rounded-xl border
                border-slate-300 px-4 py-3
                text-slate-900 outline-none
                transition focus:border-blue-500
                focus:ring-2 focus:ring-blue-500/20
              "
            />
          </label>

          <label className="block">
            <span
              className="
                mb-2 block text-sm font-semibold
                text-slate-900
              "
            >
              Notes
            </span>

            <textarea
              rows={4}
              maxLength={1000}
              value={notes}
              onChange={(event) =>
                setNotes(event.target.value)
              }
              placeholder={
                pickup
                  ? (
                      "Add pickup condition or " +
                      "handover notes..."
                    )
                  : (
                      "Add delivery or receiver " +
                      "handover notes..."
                    )
              }
              className="
                w-full resize-none rounded-xl
                border border-slate-300
                px-4 py-3 text-slate-900
                outline-none transition
                focus:border-blue-500
                focus:ring-2 focus:ring-blue-500/20
              "
            />
          </label>

          <PageMessage
            type="error"
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
                rounded-xl border border-slate-300
                px-5 py-3 font-semibold
                text-slate-700 transition
                hover:bg-slate-50
              "
            >
              Cancel
            </button>

            <button
              type="submit"
              disabled={submitting}
              className="
                inline-flex items-center
                justify-center gap-2 rounded-xl
                bg-blue-600 px-5 py-3
                font-semibold text-white transition
                hover:bg-blue-700
                active:scale-[0.98]
                disabled:cursor-not-allowed
                disabled:bg-blue-300
              "
            >
              {submitting ? (
                <LoaderCircle
                  className="
                    h-5 w-5 animate-spin
                  "
                  aria-hidden="true"
                />
              ) : (
                <Check
                  className="h-5 w-5"
                  aria-hidden="true"
                />
              )}

              {pickup
                ? "Confirm pickup"
                : "Confirm delivery"}
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}


function ReasonDialog({
  action,
  submitting,
  error,
  onClose,
  onConfirm,
}) {
  const [reason, setReason] =
    useState("");

  const [stage, setStage] =
    useState("BEFORE_PICKUP");

  useEffect(() => {
    setReason("");
    setStage("BEFORE_PICKUP");
  }, [action]);

  if (!action) {
    return null;
  }

  const failure =
    action === "failure";

  function handleSubmit(event) {
    event.preventDefault();

    if (reason.trim().length < 3) {
      return;
    }

    if (failure) {
      onConfirm({
        stage,
        reason: reason.trim(),
      });
    } else {
      onConfirm({
        reason: reason.trim(),
      });
    }
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
              className="
                text-sm font-semibold uppercase
                tracking-wide text-red-600
              "
            >
              {failure
                ? "Report transport failure"
                : "Cancel assignment"}
            </p>

            <h2
              className="
                mt-1 text-xl font-bold text-slate-900
              "
            >
              {failure
                ? "What went wrong?"
                : "Release this task?"}
            </h2>
          </div>

          <button
            type="button"
            disabled={submitting}
            onClick={onClose}
            aria-label="Close dialog"
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
          {failure ? (
            <label className="block">
              <span
                className="
                  mb-2 block text-sm font-semibold
                  text-slate-900
                "
              >
                Failure stage
              </span>

              <select
                value={stage}
                onChange={(event) =>
                  setStage(event.target.value)
                }
                className="
                  w-full rounded-xl border
                  border-slate-300 bg-white
                  px-4 py-3 text-slate-900
                  outline-none focus:border-blue-500
                  focus:ring-2
                  focus:ring-blue-500/20
                "
              >
                <option value="BEFORE_PICKUP">
                  Before pickup
                </option>

                <option value="AFTER_PICKUP">
                  After pickup
                </option>
              </select>
            </label>
          ) : null}

          <label className="block">
            <span
              className="
                mb-2 block text-sm font-semibold
                text-slate-900
              "
            >
              Reason
            </span>

            <textarea
              required
              minLength={3}
              maxLength={1000}
              rows={4}
              value={reason}
              onChange={(event) =>
                setReason(event.target.value)
              }
              placeholder={
                failure
                  ? "Describe the transport problem..."
                  : (
                      "Explain why you cannot complete " +
                      "this task..."
                    )
              }
              className="
                w-full resize-none rounded-xl
                border border-slate-300
                px-4 py-3 text-slate-900
                outline-none focus:border-blue-500
                focus:ring-2 focus:ring-blue-500/20
              "
            />
          </label>

          <PageMessage
            type="error"
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
                rounded-xl border border-slate-300
                px-5 py-3 font-semibold
                text-slate-700 hover:bg-slate-50
              "
            >
              Go back
            </button>

            <button
              type="submit"
              disabled={
                submitting ||
                reason.trim().length < 3
              }
              className="
                inline-flex items-center
                justify-center gap-2 rounded-xl
                bg-red-600 px-5 py-3
                font-semibold text-white
                transition hover:bg-red-700
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
                <XCircle className="h-5 w-5" />
              )}

              {failure
                ? "Submit failure report"
                : "Cancel assignment"}
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}


export function ActiveTaskPage() {
  const { taskId } = useParams();

  const navigate = useNavigate();

  const [task, setTask] =
    useState(null);

  const [loading, setLoading] =
    useState(true);

  const [submitting, setSubmitting] =
    useState(false);

  const [error, setError] =
    useState("");

  const [success, setSuccess] =
    useState("");

  const [quantityAction, setQuantityAction] =
    useState(null);

  const [reasonAction, setReasonAction] =
    useState(null);

  const [dialogError, setDialogError] =
    useState("");

  const loadTask = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const response = await api.get(
        "/logistics/volunteer/tasks/mine/",
      );

      const tasks =
        getResults(response.data);

      const selectedTask =
        tasks.find(
          (item) =>
            String(item.id) === String(taskId),
        );

      if (!selectedTask) {
        setTask(null);

        setError(
          "The task was not found or is no longer assigned to you.",
        );

        return;
      }

      setTask(selectedTask);
    } catch (requestError) {
      setError(
        getErrorMessage(requestError),
      );
    } finally {
      setLoading(false);
    }
  }, [taskId]);

  useEffect(() => {
    loadTask();
  }, [loadTask]);

  async function postAction(
    endpoint,
    payload,
    successMessage,
  ) {
    setSubmitting(true);
    setDialogError("");
    setError("");
    setSuccess("");

    try {
      await api.post(
        endpoint,
        payload,
      );

      setSuccess(successMessage);
      setQuantityAction(null);
      setReasonAction(null);

      await loadTask();
    } catch (requestError) {
      const message =
        getErrorMessage(requestError);

      if (
        quantityAction ||
        reasonAction
      ) {
        setDialogError(message);
      } else {
        setError(message);
      }
    } finally {
      setSubmitting(false);
    }
  }

  function markArrivedAtDonor() {
    postAction(
      (
        "/logistics/volunteer/tasks/" +
        `${taskId}/arrive-at-donor/`
      ),
      {},
      "Arrival at the donor was recorded.",
    );
  }

  function markArrivedAtReceiver() {
    postAction(
      (
        "/logistics/volunteer/tasks/" +
        `${taskId}/arrive-at-receiver/`
      ),
      {},
      "Arrival at the receiver was recorded.",
    );
  }

  function confirmQuantity(payload) {
    const pickup =
      quantityAction === "pickup";

    postAction(
      (
        "/logistics/volunteer/tasks/" +
        `${taskId}/` +
        `${pickup ? "pickup" : "delivery"}/`
      ),
      payload,
      pickup
        ? "Food pickup was recorded."
        : "Food delivery was recorded.",
    );
  }

  function confirmReason(payload) {
    const failure =
      reasonAction === "failure";

    postAction(
      (
        "/logistics/volunteer/tasks/" +
        `${taskId}/` +
        `${
          failure
            ? "report-failure"
            : "cancel-assignment"
        }/`
      ),
      payload,
      failure
        ? "The transport failure was reported."
        : "The task assignment was cancelled.",
    );
  }

  const status =
    task?.status;

  const canCancel =
    [
      "ASSIGNED",
      "ARRIVED_AT_DONOR",
    ].includes(status);

  const canReportFailure =
    ACTIVE_STATUSES.includes(status);

  if (loading) {
    return (
      <main className="space-y-5">
        <div
          className="
            h-44 animate-pulse rounded-3xl
            bg-slate-200
          "
        />

        <div
          className="
            h-96 animate-pulse rounded-2xl
            bg-slate-200
          "
        />
      </main>
    );
  }

  if (!task) {
    return (
      <main
        className="
          rounded-2xl border border-red-200
          bg-red-50 p-8 text-center
        "
      >
        <AlertCircle
          className="
            mx-auto h-12 w-12 text-red-500
          "
        />

        <h1
          className="
            mt-4 text-xl font-bold text-red-900
          "
        >
          Task unavailable
        </h1>

        <p className="mt-2 text-red-700">
          {error}
        </p>

        <Link
          to="/volunteer/tasks"
          className="
            mt-5 inline-flex items-center gap-2
            rounded-xl bg-red-600
            px-5 py-3 font-semibold text-white
            hover:bg-red-700
          "
        >
          <ArrowLeft className="h-5 w-5" />
          Back to tasks
        </Link>
      </main>
    );
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
        <Link
          to="/volunteer/tasks"
          className="
            inline-flex items-center gap-2
            text-sm font-semibold text-blue-100
            hover:text-white
          "
        >
          <ArrowLeft className="h-4 w-4" />
          Back to available tasks
        </Link>

        <div
          className="
            mt-5 flex flex-col gap-4
            sm:flex-row sm:items-start
            sm:justify-between
          "
        >
          <div>
            <p
              className="
                text-sm font-semibold uppercase
                tracking-widest text-blue-100
              "
            >
              Active volunteer task
            </p>

            <h1
              className="
                mt-2 text-3xl font-bold
              "
            >
              {getFoodName(task)}
            </h1>

            <p className="mt-2 text-blue-50">
              {task.required_quantity} {task.unit}
            </p>
          </div>

          <TaskStatusBadge
            status={task.status}
          />
        </div>
      </header>

      <PageMessage
        type="error"
        message={error}
      />

      <PageMessage
        type="success"
        message={success}
      />

      <div
        className="
          grid gap-6
          lg:grid-cols-[minmax(0,1fr)_380px]
        "
      >
        <div className="space-y-6">
          <section
            className="
              rounded-2xl border border-slate-200
              bg-white p-5 shadow-sm
            "
          >
            <div
              className="
                flex items-center justify-between
                gap-4
              "
            >
              <h2
                className="
                  text-xl font-bold text-slate-900
                "
              >
                Transport information
              </h2>

              <button
                type="button"
                onClick={loadTask}
                disabled={loading}
                className="
                  rounded-xl p-2 text-slate-500
                  hover:bg-slate-100
                  hover:text-blue-600
                "
                aria-label="Refresh task"
              >
                <RefreshCw
                  className="h-5 w-5"
                />
              </button>
            </div>

            <div
              className="
                mt-5 grid gap-3 sm:grid-cols-2
              "
            >
              <TaskInformation
                label="Pickup location"
                value={getPickupArea(task)}
              />

              <TaskInformation
                label="Receiver location"
                value={getReceiverArea(task)}
              />

              <TaskInformation
                label="Required quantity"
                value={
                  `${task.required_quantity} ` +
                  `${task.unit}`
                }
              />

              <TaskInformation
                label="Pickup deadline"
                value={formatDateTime(
                  task.pickup_deadline,
                )}
              />

              <TaskInformation
                label="Donor"
                value={
                  task.donor_name ||
                  "Donation donor"
                }
              />

              <TaskInformation
                label="Receiver"
                value={
                  task.receiver_name ||
                  "Receiver organization"
                }
              />
            </div>
          </section>

          <section
            className="
              rounded-2xl border border-slate-200
              bg-white p-5 shadow-sm
            "
          >
            <h2
              className="
                text-xl font-bold text-slate-900
              "
            >
              Next action
            </h2>

            <p className="mt-2 text-sm text-slate-600">
              Update the task only after the physical
              transport event has happened.
            </p>

            <div className="mt-5">
              {status === "ASSIGNED" ? (
                <button
                  type="button"
                  disabled={submitting}
                  onClick={markArrivedAtDonor}
                  className="
                    inline-flex w-full items-center
                    justify-center gap-2 rounded-xl
                    bg-blue-600 px-5 py-3
                    font-semibold text-white
                    transition hover:bg-blue-700
                    active:scale-[0.98]
                  "
                >
                  <MapPin className="h-5 w-5" />
                  I arrived at the donor
                </button>
              ) : null}

              {status === "ARRIVED_AT_DONOR" ? (
                <button
                  type="button"
                  onClick={() =>
                    setQuantityAction("pickup")
                  }
                  className="
                    inline-flex w-full items-center
                    justify-center gap-2 rounded-xl
                    bg-blue-600 px-5 py-3
                    font-semibold text-white
                    transition hover:bg-blue-700
                    active:scale-[0.98]
                  "
                >
                  <Package className="h-5 w-5" />
                  Record food pickup
                </button>
              ) : null}

              {status === "PICKED_UP" ? (
                <button
                  type="button"
                  disabled={submitting}
                  onClick={
                    markArrivedAtReceiver
                  }
                  className="
                    inline-flex w-full items-center
                    justify-center gap-2 rounded-xl
                    bg-blue-600 px-5 py-3
                    font-semibold text-white
                    transition hover:bg-blue-700
                    active:scale-[0.98]
                  "
                >
                  <Navigation className="h-5 w-5" />
                  I arrived at the receiver
                </button>
              ) : null}

              {status ===
              "ARRIVED_AT_RECEIVER" ? (
                <button
                  type="button"
                  onClick={() =>
                    setQuantityAction("delivery")
                  }
                  className="
                    inline-flex w-full items-center
                    justify-center gap-2 rounded-xl
                    bg-emerald-600 px-5 py-3
                    font-semibold text-white
                    transition hover:bg-emerald-700
                    active:scale-[0.98]
                  "
                >
                  <Truck className="h-5 w-5" />
                  Record delivery
                </button>
              ) : null}

              {status === "DELIVERED" ? (
                <div
                  className="
                    rounded-xl border
                    border-amber-200 bg-amber-50
                    p-4 text-amber-800
                  "
                >
                  <div className="flex gap-3">
                    <Clock3
                      className="
                        mt-0.5 h-5 w-5 shrink-0
                      "
                    />

                    <div>
                      <p className="font-semibold">
                        Waiting for receiver
                      </p>

                      <p className="mt-1 text-sm">
                        Delivery is recorded. The receiver
                        must confirm receipt before the
                        task and donation become completed.
                      </p>
                    </div>
                  </div>
                </div>
              ) : null}

              {status === "COMPLETED" ? (
                <div
                  className="
                    rounded-xl border
                    border-emerald-200
                    bg-emerald-50 p-4
                    text-emerald-800
                  "
                >
                  <div className="flex gap-3">
                    <CheckCircle2
                      className="
                        mt-0.5 h-5 w-5 shrink-0
                      "
                    />

                    <div>
                      <p className="font-semibold">
                        Task completed
                      </p>

                      <p className="mt-1 text-sm">
                        The receiver confirmed successful
                        receipt of the donation.
                      </p>
                    </div>
                  </div>
                </div>
              ) : null}

              {[
                "CANCELLED",
                "FAILED",
              ].includes(status) ? (
                <div
                  className="
                    rounded-xl border border-red-200
                    bg-red-50 p-4 text-red-700
                  "
                >
                  This task is no longer active.
                </div>
              ) : null}
            </div>

            {canCancel ||
            canReportFailure ? (
              <div
                className="
                  mt-5 flex flex-col gap-3
                  border-t border-slate-200 pt-5
                  sm:flex-row
                "
              >
                {canCancel ? (
                  <button
                    type="button"
                    onClick={() =>
                      setReasonAction("cancel")
                    }
                    className="
                      inline-flex flex-1 items-center
                      justify-center gap-2 rounded-xl
                      border border-slate-300
                      px-4 py-2.5 font-semibold
                      text-slate-700
                      hover:bg-slate-50
                    "
                  >
                    <RotateCcw className="h-5 w-5" />
                    Cancel assignment
                  </button>
                ) : null}

                {canReportFailure ? (
                  <button
                    type="button"
                    onClick={() =>
                      setReasonAction("failure")
                    }
                    className="
                      inline-flex flex-1 items-center
                      justify-center gap-2 rounded-xl
                      border border-red-200
                      px-4 py-2.5 font-semibold
                      text-red-700 hover:bg-red-50
                    "
                  >
                    <AlertCircle className="h-5 w-5" />
                    Report failure
                  </button>
                ) : null}
              </div>
            ) : null}
          </section>
        </div>

        <aside
          className="
            h-fit rounded-2xl border
            border-slate-200 bg-white
            p-5 shadow-sm
          "
        >
          <h2 className="font-bold text-slate-900">
            Task progress
          </h2>

          <div className="mt-6 space-y-6">
            <ProgressStep
              number="1"
              title="Task accepted"
              description={
                task.assigned_at
                  ? formatDateTime(task.assigned_at)
                  : "Assigned to volunteer."
              }
              completed={[
                "ASSIGNED",
                "ARRIVED_AT_DONOR",
                "PICKED_UP",
                "ARRIVED_AT_RECEIVER",
                "DELIVERED",
                "COMPLETED",
              ].includes(status)}
              active={status === "ASSIGNED"}
            />

            <ProgressStep
              number="2"
              title="Arrived at donor"
              description="Volunteer reached pickup location."
              completed={[
                "ARRIVED_AT_DONOR",
                "PICKED_UP",
                "ARRIVED_AT_RECEIVER",
                "DELIVERED",
                "COMPLETED",
              ].includes(status)}
              active={
                status === "ARRIVED_AT_DONOR"
              }
            />

            <ProgressStep
              number="3"
              title="Food picked up"
              description={
                task.picked_up_at
                  ? formatDateTime(task.picked_up_at)
                  : "Waiting for pickup."
              }
              completed={[
                "PICKED_UP",
                "ARRIVED_AT_RECEIVER",
                "DELIVERED",
                "COMPLETED",
              ].includes(status)}
              active={status === "PICKED_UP"}
            />

            <ProgressStep
              number="4"
              title="Arrived at receiver"
              description="Volunteer reached delivery location."
              completed={[
                "ARRIVED_AT_RECEIVER",
                "DELIVERED",
                "COMPLETED",
              ].includes(status)}
              active={
                status ===
                "ARRIVED_AT_RECEIVER"
              }
            />

            <ProgressStep
              number="5"
              title="Food delivered"
              description={
                task.delivered_at
                  ? formatDateTime(task.delivered_at)
                  : "Waiting for delivery."
              }
              completed={[
                "DELIVERED",
                "COMPLETED",
              ].includes(status)}
              active={status === "DELIVERED"}
            />

            <ProgressStep
              number="6"
              title="Receipt confirmed"
              description={
                status === "COMPLETED"
                  ? "Receiver confirmed receipt."
                  : "Waiting for receiver."
              }
              completed={status === "COMPLETED"}
              active={status === "DELIVERED"}
            />
          </div>
        </aside>
      </div>

      <QuantityDialog
        action={quantityAction}
        task={task}
        submitting={submitting}
        error={dialogError}
        onClose={() => {
          if (!submitting) {
            setQuantityAction(null);
            setDialogError("");
          }
        }}
        onConfirm={confirmQuantity}
      />

      <ReasonDialog
        action={reasonAction}
        submitting={submitting}
        error={dialogError}
        onClose={() => {
          if (!submitting) {
            setReasonAction(null);
            setDialogError("");
          }
        }}
        onConfirm={confirmReason}
      />
    </main>
  );
}


function HistoryTaskCard({
  task,
}) {
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
          <TaskStatusBadge
            status={task.status}
          />

          <h2
            className="
              mt-3 text-lg font-bold text-slate-900
            "
          >
            {getFoodName(task)}
          </h2>

          <p className="mt-1 text-sm text-slate-600">
            {task.required_quantity} {task.unit}
          </p>
        </div>

        <History
          className="h-6 w-6 text-slate-400"
        />
      </div>

      <div
        className="
          mt-5 grid gap-3 sm:grid-cols-2
        "
      >
        <TaskInformation
          label="Pickup location"
          value={getPickupArea(task)}
        />

        <TaskInformation
          label="Receiver location"
          value={getReceiverArea(task)}
        />

        <TaskInformation
          label="Assigned"
          value={formatDateTime(
            task.assigned_at,
          )}
        />

        <TaskInformation
          label="Closed"
          value={formatDateTime(
            task.closed_at ||
            task.updated_at,
          )}
        />
      </div>

      {task.status === "COMPLETED" ? (
        <Link
          to={`/volunteer/tasks/${task.id}`}
          className="
            mt-5 inline-flex w-full items-center
            justify-center gap-2 rounded-xl
            border border-slate-300 px-4 py-2.5
            font-semibold text-slate-700
            transition hover:bg-slate-50
          "
        >
          View task
        </Link>
      ) : null}
    </article>
  );
}


export function VolunteerTaskHistoryPage() {
  const [tasks, setTasks] =
    useState([]);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  const [filter, setFilter] =
    useState("ALL");

  const loadHistory = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const response = await api.get(
        "/logistics/volunteer/tasks/mine/",
      );

      const allTasks =
        getResults(response.data);

      setTasks(
        allTasks.filter((task) =>
          HISTORY_STATUSES.includes(
            task.status,
          ),
        ),
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
    loadHistory();
  }, [loadHistory]);

  const visibleTasks = useMemo(() => {
    if (filter === "ALL") {
      return tasks;
    }

    return tasks.filter(
      (task) => task.status === filter,
    );
  }, [
    tasks,
    filter,
  ]);

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
              Volunteer history
            </p>

            <h1
              className="
                mt-2 text-3xl font-bold
              "
            >
              Previous transport tasks
            </h1>

            <p className="mt-3 text-blue-50">
              Review your completed, cancelled and
              failed transport tasks.
            </p>
          </div>

          <button
            type="button"
            onClick={loadHistory}
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

      <PageMessage
        type="error"
        message={error}
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
            "COMPLETED",
            "CANCELLED",
            "FAILED",
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
        </div>
      </section>

      {loading ? (
        <LoadingCards />
      ) : null}

      {!loading &&
      !error &&
      visibleTasks.length === 0 ? (
        <EmptyState
          title="No task history"
          description={
            "Completed, cancelled and failed tasks " +
            "will appear here."
          }
          icon={History}
        />
      ) : null}

      {!loading &&
      visibleTasks.length > 0 ? (
        <section
          className="
            grid gap-5 lg:grid-cols-2
          "
        >
          {visibleTasks.map((task) => (
            <HistoryTaskCard
              key={task.id}
              task={task}
            />
          ))}
        </section>
      ) : null}
    </main>
  );
}