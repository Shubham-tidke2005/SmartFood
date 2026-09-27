import {
  AlertCircle,
  ArrowLeft,
  Check,
  CheckCircle2,
  ClipboardCheck,
  Clock3,
  Handshake,
  LoaderCircle,
  PackageCheck,
  RefreshCw,
  Truck,
} from "lucide-react";
import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import {
  Link,
  useParams,
} from "react-router-dom";

import useAuth from "../../auth/useAuth";
import api from "../../lib/api";


const DISCREPANCY_TYPES = [
  {
    value: "NONE",
    label: "No discrepancy",
  },
  {
    value: "SHORTAGE",
    label: "Quantity shortage",
  },
  {
    value: "DAMAGE",
    label: "Damaged food or packaging",
  },
  {
    value: "QUALITY",
    label: "Quality concern",
  },
  {
    value: "WRONG_ITEM",
    label: "Wrong food item",
  },
  {
    value: "OTHER",
    label: "Other",
  },
];


const MODE_LABELS = {
  RECEIVER_COLLECTION: "Receiver collection",
  DONOR_DELIVERY: "Donor delivery",
  VOLUNTEER_DELIVERY: "Volunteer delivery",
};


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
  const offset = date.getTimezoneOffset();

  return new Date(
    date.getTime() - offset * 60 * 1000,
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
    return "Not recorded";
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


function getDonation(data) {
  return data?.donation || data || {};
}


function getRequest(data) {
  return (
    data?.approved_request ||
    data?.donation_request ||
    data?.request ||
    data?.allocation ||
    {}
  );
}


function getRevision(data) {
  const donation = getDonation(data);
  const request = getRequest(data);

  return (
    data?.revision ||
    data?.current_revision ||
    donation?.current_revision ||
    request?.requested_revision_details ||
    {}
  );
}


function getHandover(data) {
  return (
    data?.handover ||
    data?.handover_record ||
    null
  );
}


function getDelivery(data) {
  return (
    data?.delivery ||
    data?.delivery_record ||
    null
  );
}


function getReceipt(data) {
  return (
    data?.receipt ||
    data?.receipt_confirmation ||
    null
  );
}


function StatusStep({
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
                  "border-emerald-500 bg-emerald-500 " +
                  "text-white"
                )
              : active
                ? (
                    "border-blue-600 bg-blue-600 " +
                    "text-white"
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


function Information({
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


function ActionForm({
  title,
  description,
  quantityLabel,
  quantity,
  setQuantity,
  dateLabel,
  dateValue,
  setDateValue,
  notes,
  setNotes,
  submitLabel,
  submitting,
  onSubmit,
}) {
  return (
    <section
      className="
        rounded-2xl border border-slate-200 bg-white
        p-5 shadow-sm
      "
    >
      <h2 className="text-xl font-bold text-slate-900">
        {title}
      </h2>

      <p className="mt-2 text-sm text-slate-600">
        {description}
      </p>

      <form
        onSubmit={onSubmit}
        className="mt-6 space-y-5"
      >
        <label className="block">
          <span
            className="
              mb-2 block text-sm font-semibold
              text-slate-800
            "
          >
            {quantityLabel}
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
              w-full rounded-xl border border-slate-300
              px-4 py-3 text-slate-900 outline-none
              transition focus:border-blue-500
              focus:ring-2 focus:ring-blue-500/20
            "
          />
        </label>

        <label className="block">
          <span
            className="
              mb-2 block text-sm font-semibold
              text-slate-800
            "
          >
            {dateLabel}
          </span>

          <input
            type="datetime-local"
            required
            value={dateValue}
            onChange={(event) =>
              setDateValue(event.target.value)
            }
            className="
              w-full rounded-xl border border-slate-300
              px-4 py-3 text-slate-900 outline-none
              transition focus:border-blue-500
              focus:ring-2 focus:ring-blue-500/20
            "
          />
        </label>

        <label className="block">
          <span
            className="
              mb-2 block text-sm font-semibold
              text-slate-800
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
            placeholder="Add collection or delivery notes..."
            className="
              w-full resize-none rounded-xl border
              border-slate-300 px-4 py-3 text-slate-900
              outline-none transition
              focus:border-blue-500 focus:ring-2
              focus:ring-blue-500/20
            "
          />
        </label>

        <button
          type="submit"
          disabled={submitting}
          className="
            inline-flex w-full items-center justify-center
            gap-2 rounded-xl bg-blue-600 px-5 py-3
            font-semibold text-white transition
            hover:bg-blue-700 active:scale-[0.98]
            focus-visible:outline-none focus-visible:ring-2
            focus-visible:ring-blue-500
            focus-visible:ring-offset-2
            disabled:cursor-not-allowed disabled:bg-blue-300
          "
        >
          {submitting ? (
            <>
              <LoaderCircle
                className="h-5 w-5 animate-spin"
                aria-hidden="true"
              />
              Saving...
            </>
          ) : (
            <>
              <Check
                className="h-5 w-5"
                aria-hidden="true"
              />
              {submitLabel}
            </>
          )}
        </button>
      </form>
    </section>
  );
}


function ReceiptForm({
  expectedQuantity,
  unit,
  submitting,
  onSubmit,
}) {
  const [acceptedQuantity, setAcceptedQuantity] =
    useState(expectedQuantity || "");

  const [receivedAt, setReceivedAt] = useState(
    getCurrentLocalDateTime(),
  );

  const [discrepancyType, setDiscrepancyType] =
    useState("NONE");

  const [discrepancyNotes, setDiscrepancyNotes] =
    useState("");

  useEffect(() => {
    if (
      expectedQuantity &&
      !acceptedQuantity
    ) {
      setAcceptedQuantity(expectedQuantity);
    }
  }, [
    expectedQuantity,
    acceptedQuantity,
  ]);

  function handleSubmit(event) {
    event.preventDefault();

    onSubmit({
      accepted_quantity: acceptedQuantity,
      received_at: toISOString(receivedAt),
      discrepancy_type: discrepancyType,
      discrepancy_notes:
        discrepancyType === "NONE"
          ? ""
          : discrepancyNotes.trim(),
    });
  }

  return (
    <section
      className="
        rounded-2xl border border-slate-200 bg-white
        p-5 shadow-sm
      "
    >
      <h2 className="text-xl font-bold text-slate-900">
        Confirm food receipt
      </h2>

      <p className="mt-2 text-sm text-slate-600">
        Record the actual quantity your organization
        accepted.
      </p>

      <form
        onSubmit={handleSubmit}
        className="mt-6 space-y-5"
      >
        <label className="block">
          <span
            className="
              mb-2 block text-sm font-semibold
              text-slate-800
            "
          >
            Accepted quantity ({unit})
          </span>

          <input
            type="number"
            required
            min="0"
            step="0.001"
            value={acceptedQuantity}
            onChange={(event) =>
              setAcceptedQuantity(
                event.target.value,
              )
            }
            className="
              w-full rounded-xl border border-slate-300
              px-4 py-3 text-slate-900 outline-none
              transition focus:border-blue-500
              focus:ring-2 focus:ring-blue-500/20
            "
          />
        </label>

        <label className="block">
          <span
            className="
              mb-2 block text-sm font-semibold
              text-slate-800
            "
          >
            Received at
          </span>

          <input
            type="datetime-local"
            required
            value={receivedAt}
            onChange={(event) =>
              setReceivedAt(event.target.value)
            }
            className="
              w-full rounded-xl border border-slate-300
              px-4 py-3 text-slate-900 outline-none
              transition focus:border-blue-500
              focus:ring-2 focus:ring-blue-500/20
            "
          />
        </label>

        <label className="block">
          <span
            className="
              mb-2 block text-sm font-semibold
              text-slate-800
            "
          >
            Receipt result
          </span>

          <select
            value={discrepancyType}
            onChange={(event) =>
              setDiscrepancyType(
                event.target.value,
              )
            }
            className="
              w-full rounded-xl border border-slate-300
              bg-white px-4 py-3 text-slate-900
              outline-none transition
              focus:border-blue-500 focus:ring-2
              focus:ring-blue-500/20
            "
          >
            {DISCREPANCY_TYPES.map((type) => (
              <option
                key={type.value}
                value={type.value}
              >
                {type.label}
              </option>
            ))}
          </select>
        </label>

        {discrepancyType !== "NONE" ? (
          <label className="block">
            <span
              className="
                mb-2 block text-sm font-semibold
                text-slate-800
              "
            >
              Discrepancy details
            </span>

            <textarea
              required
              minLength={3}
              maxLength={1000}
              rows={4}
              value={discrepancyNotes}
              onChange={(event) =>
                setDiscrepancyNotes(
                  event.target.value,
                )
              }
              placeholder={
                "Describe the quantity, quality, " +
                "damage or delivery problem..."
              }
              className="
                w-full resize-none rounded-xl border
                border-slate-300 px-4 py-3
                text-slate-900 outline-none
                transition focus:border-blue-500
                focus:ring-2 focus:ring-blue-500/20
              "
            />
          </label>
        ) : null}

        <button
          type="submit"
          disabled={submitting}
          className="
            inline-flex w-full items-center justify-center
            gap-2 rounded-xl bg-emerald-600 px-5 py-3
            font-semibold text-white transition
            hover:bg-emerald-700 active:scale-[0.98]
            focus-visible:outline-none focus-visible:ring-2
            focus-visible:ring-emerald-500
            focus-visible:ring-offset-2
            disabled:cursor-not-allowed
            disabled:bg-emerald-300
          "
        >
          {submitting ? (
            <>
              <LoaderCircle
                className="h-5 w-5 animate-spin"
                aria-hidden="true"
              />
              Confirming...
            </>
          ) : (
            <>
              <PackageCheck
                className="h-5 w-5"
                aria-hidden="true"
              />
              Confirm receipt
            </>
          )}
        </button>
      </form>
    </section>
  );
}


export default function DirectFulfilmentPage() {
  const { donationId } = useParams();
  const { user } = useAuth();

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] =
    useState(false);

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [quantity, setQuantity] = useState("");
  const [notes, setNotes] = useState("");
  const [actionDate, setActionDate] = useState(
    getCurrentLocalDateTime(),
  );

  const loadFulfilment = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const response = await api.get(
        `/logistics/donations/${donationId}/`,
      );

      setData(response.data);

      const revision = getRevision(response.data);

      if (revision.quantity) {
        setQuantity(String(revision.quantity));
      }
    } catch (requestError) {
      setError(getErrorMessage(requestError));
    } finally {
      setLoading(false);
    }
  }, [donationId]);

  useEffect(() => {
    loadFulfilment();
  }, [loadFulfilment]);

  const donation = useMemo(
    () => getDonation(data),
    [data],
  );

  const donationRequest = useMemo(
    () => getRequest(data),
    [data],
  );

  const revision = useMemo(
    () => getRevision(data),
    [data],
  );

  const handover = useMemo(
    () => getHandover(data),
    [data],
  );

  const delivery = useMemo(
    () => getDelivery(data),
    [data],
  );

  const receipt = useMemo(
    () => getReceipt(data),
    [data],
  );

  const mode =
    donationRequest.proposed_mode ||
    data?.transport_mode;

  const isDonor = user?.role === "DONOR";
  const isReceiver = user?.role === "RECEIVER";

  const isReceiverCollection =
    mode === "RECEIVER_COLLECTION";

  const isDonorDelivery =
    mode === "DONOR_DELIVERY";

  const expectedQuantity =
    delivery?.actual_quantity ||
    handover?.actual_quantity ||
    revision?.quantity ||
    donationRequest?.quantity ||
    "";

  async function performAction(
    endpoint,
    payload,
    successMessage,
  ) {
    setSubmitting(true);
    setError("");
    setSuccess("");

    try {
      await api.post(endpoint, payload);

      setSuccess(successMessage);
      setNotes("");
      setActionDate(
        getCurrentLocalDateTime(),
      );

      await loadFulfilment();
    } catch (requestError) {
      setError(getErrorMessage(requestError));
    } finally {
      setSubmitting(false);
    }
  }

  function confirmHandover(event) {
    event.preventDefault();

    performAction(
      `/logistics/donations/${donationId}/handover/`,
      {
        actual_quantity: quantity,
        handed_over_at: toISOString(actionDate),
        notes: notes.trim(),
      },
      "Food handover was confirmed successfully.",
    );
  }

  function recordDelivery(event) {
    event.preventDefault();

    performAction(
      `/logistics/donations/${donationId}/delivery/`,
      {
        actual_quantity: quantity,
        delivered_at: toISOString(actionDate),
        notes: notes.trim(),
      },
      "Delivery was recorded successfully.",
    );
  }

  function confirmReceipt(payload) {
    performAction(
      `/logistics/donations/${donationId}/receipt/`,
      payload,
      (
        "Receipt was confirmed successfully. " +
        "The donation is now completed."
      ),
    );
  }

  const receiverCanConfirmReceipt =
    isReceiver &&
    !receipt &&
    (
      (
        isReceiverCollection &&
        Boolean(handover)
      ) ||
      (
        isDonorDelivery &&
        Boolean(delivery)
      )
    );

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
            grid gap-5 lg:grid-cols-[1fr_380px]
          "
        >
          <div
            className="
              h-96 animate-pulse rounded-2xl
              bg-slate-200
            "
          />

          <div
            className="
              h-96 animate-pulse rounded-2xl
              bg-slate-200
            "
          />
        </div>
      </main>
    );
  }

  if (!data) {
    return (
      <main
        className="
          rounded-2xl border border-red-200
          bg-red-50 p-8 text-center
        "
      >
        <AlertCircle
          className="mx-auto h-12 w-12 text-red-500"
        />

        <h1 className="mt-4 text-xl font-bold text-red-900">
          Fulfilment details unavailable
        </h1>

        <p className="mt-2 text-red-700">
          {error}
        </p>

        <button
          type="button"
          onClick={loadFulfilment}
          className="
            mt-5 rounded-xl bg-red-600 px-5 py-3
            font-semibold text-white hover:bg-red-700
          "
        >
          Try again
        </button>
      </main>
    );
  }

  return (
    <main className="space-y-6">
      <header
        className="
          rounded-3xl bg-gradient-to-br from-blue-600
          to-sky-500 p-6 text-white shadow-lg
          shadow-blue-500/10 sm:p-8
        "
      >
        <div
          className="
            flex flex-col gap-5 sm:flex-row
            sm:items-start sm:justify-between
          "
        >
          <div>
            <Link
              to={
                isDonor
                  ? "/donor/requests"
                  : "/receiver/requests"
              }
              className="
                inline-flex items-center gap-2 text-sm
                font-semibold text-blue-100
                hover:text-white
              "
            >
              <ArrowLeft className="h-4 w-4" />
              Back to requests
            </Link>

            <p
              className="
                mt-5 text-sm font-semibold uppercase
                tracking-widest text-blue-100
              "
            >
              Direct fulfilment
            </p>

            <h1 className="mt-2 text-3xl font-bold">
              {revision.food_name ||
                donationRequest.food_name ||
                "Food donation"}
            </h1>

            <p className="mt-3 text-blue-50">
              {MODE_LABELS[mode] ||
                "Collection arrangement"}
            </p>
          </div>

          <button
            type="button"
            onClick={loadFulfilment}
            disabled={loading}
            className="
              inline-flex items-center justify-center
              gap-2 rounded-xl bg-white/15
              px-4 py-3 font-semibold backdrop-blur
              transition hover:bg-white/25
            "
          >
            <RefreshCw className="h-5 w-5" />
            Refresh
          </button>
        </div>
      </header>

      {error ? (
        <div
          role="alert"
          className="
            flex items-start gap-3 rounded-2xl border
            border-red-200 bg-red-50 p-4
            text-red-700
          "
        >
          <AlertCircle
            className="mt-0.5 h-5 w-5 shrink-0"
          />
          <span>{error}</span>
        </div>
      ) : null}

      {success ? (
        <div
          role="status"
          className="
            flex items-start gap-3 rounded-2xl border
            border-emerald-200 bg-emerald-50 p-4
            text-emerald-800
          "
        >
          <CheckCircle2
            className="mt-0.5 h-5 w-5 shrink-0"
          />
          <span>{success}</span>
        </div>
      ) : null}

      <div
        className="
          grid gap-6 lg:grid-cols-[minmax(0,1fr)_380px]
        "
      >
        <div className="space-y-6">
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
              Donation arrangement
            </h2>

            <div
              className="
                mt-5 grid gap-3 sm:grid-cols-2
              "
            >
              <Information
                label="Food"
                value={
                  revision.food_name ||
                  donationRequest.food_name
                }
              />

              <Information
                label="Expected quantity"
                value={
                  `${revision.quantity ||
                    donationRequest.quantity} ${
                    revision.unit ||
                    donationRequest.unit ||
                    ""
                  }`
                }
              />

              <Information
                label="Receiver"
                value={
                  donationRequest.receiver_name
                }
              />

              <Information
                label="Transport mode"
                value={MODE_LABELS[mode]}
              />

              <Information
                label="Pickup deadline"
                value={formatDateTime(
                  revision.pickup_deadline ||
                  donationRequest.pickup_deadline,
                )}
              />

              <Information
                label="Donation status"
                value={donation.status}
              />
            </div>
          </section>

          {isDonor && !handover ? (
            <ActionForm
              title="Confirm food handover"
              description={
                isReceiverCollection
                  ? (
                      "Confirm that the receiver collected " +
                      "the food from you."
                    )
                  : (
                      "Record the quantity leaving the " +
                      "donor location for delivery."
                    )
              }
              quantityLabel={
                `Actual handover quantity ` +
                `(${revision.unit ||
                  donationRequest.unit ||
                  ""})`
              }
              quantity={quantity}
              setQuantity={setQuantity}
              dateLabel="Handover date and time"
              dateValue={actionDate}
              setDateValue={setActionDate}
              notes={notes}
              setNotes={setNotes}
              submitLabel="Confirm handover"
              submitting={submitting}
              onSubmit={confirmHandover}
            />
          ) : null}

          {isDonor &&
          isDonorDelivery &&
          handover &&
          !delivery ? (
            <ActionForm
              title="Record delivery"
              description={
                "Confirm that the donor delivered the " +
                "food to the receiver organization."
              }
              quantityLabel={
                `Delivered quantity ` +
                `(${revision.unit ||
                  donationRequest.unit ||
                  ""})`
              }
              quantity={quantity}
              setQuantity={setQuantity}
              dateLabel="Delivery date and time"
              dateValue={actionDate}
              setDateValue={setActionDate}
              notes={notes}
              setNotes={setNotes}
              submitLabel="Record delivery"
              submitting={submitting}
              onSubmit={recordDelivery}
            />
          ) : null}

          {receiverCanConfirmReceipt ? (
            <ReceiptForm
              expectedQuantity={expectedQuantity}
              unit={
                revision.unit ||
                donationRequest.unit ||
                ""
              }
              submitting={submitting}
              onSubmit={confirmReceipt}
            />
          ) : null}

          {receipt ? (
            <section
              className="
                rounded-2xl border
                border-emerald-200 bg-emerald-50
                p-6
              "
            >
              <div className="flex items-start gap-4">
                <CheckCircle2
                  className="
                    h-10 w-10 shrink-0
                    text-emerald-600
                  "
                />

                <div>
                  <h2
                    className="
                      text-xl font-bold
                      text-emerald-900
                    "
                  >
                    Donation completed
                  </h2>

                  <p
                    className="
                      mt-2 text-sm text-emerald-800
                    "
                  >
                    The receiver accepted{" "}
                    <strong>
                      {receipt.accepted_quantity}{" "}
                      {receipt.unit}
                    </strong>
                    .
                  </p>

                  <p
                    className="
                      mt-1 text-sm text-emerald-700
                    "
                  >
                    Received{" "}
                    {formatDateTime(
                      receipt.received_at,
                    )}
                  </p>

                  {receipt.discrepancy_type !==
                  "NONE" ? (
                    <div
                      className="
                        mt-4 rounded-xl border
                        border-amber-200 bg-amber-50
                        p-4 text-amber-800
                      "
                    >
                      <p className="font-semibold">
                        Discrepancy:{" "}
                        {receipt.discrepancy_type}
                      </p>

                      <p className="mt-1 text-sm">
                        {receipt.discrepancy_notes}
                      </p>
                    </div>
                  ) : null}
                </div>
              </div>
            </section>
          ) : null}
        </div>

        <aside
          className="
            h-fit rounded-2xl border border-slate-200
            bg-white p-5 shadow-sm
          "
        >
          <h2 className="font-bold text-slate-900">
            Fulfilment progress
          </h2>

          <div className="mt-6 space-y-6">
            <StatusStep
              number="1"
              title="Request approved"
              description={
                donationRequest.receiver_name
                  ? (
                      `${donationRequest.receiver_name} ` +
                      "was selected."
                    )
                  : "A receiver was selected."
              }
              completed
            />

            <StatusStep
              number="2"
              title="Food handed over"
              description={
                handover
                  ? (
                      `${handover.actual_quantity} ` +
                      `${handover.unit} handed over.`
                    )
                  : "Waiting for donor confirmation."
              }
              completed={Boolean(handover)}
              active={!handover}
            />

            {isDonorDelivery ? (
              <StatusStep
                number="3"
                title="Food delivered"
                description={
                  delivery
                    ? (
                        `${delivery.actual_quantity} ` +
                        `${delivery.unit} delivered.`
                      )
                    : "Waiting for donor delivery."
                }
                completed={Boolean(delivery)}
                active={
                  Boolean(handover) &&
                  !delivery
                }
              />
            ) : null}

            <StatusStep
              number={isDonorDelivery ? "4" : "3"}
              title="Receipt confirmed"
              description={
                receipt
                  ? "Receiver confirmed the donation."
                  : "Waiting for receiver confirmation."
              }
              completed={Boolean(receipt)}
              active={
                !receipt &&
                (
                  (
                    isReceiverCollection &&
                    Boolean(handover)
                  ) ||
                  (
                    isDonorDelivery &&
                    Boolean(delivery)
                  )
                )
              }
            />
          </div>

          {handover ? (
            <div
              className="
                mt-6 rounded-xl bg-slate-50 p-4
              "
            >
              <div className="flex items-center gap-2">
                <Handshake
                  className="h-5 w-5 text-blue-600"
                />

                <p className="font-semibold text-slate-900">
                  Handover recorded
                </p>
              </div>

              <p className="mt-2 text-sm text-slate-600">
                {formatDateTime(
                  handover.handed_over_at,
                )}
              </p>
            </div>
          ) : null}

          {delivery ? (
            <div
              className="
                mt-3 rounded-xl bg-slate-50 p-4
              "
            >
              <div className="flex items-center gap-2">
                <Truck
                  className="h-5 w-5 text-sky-600"
                />

                <p className="font-semibold text-slate-900">
                  Delivery recorded
                </p>
              </div>

              <p className="mt-2 text-sm text-slate-600">
                {formatDateTime(
                  delivery.delivered_at,
                )}
              </p>
            </div>
          ) : null}

          {!receipt ? (
            <div
              className="
                mt-4 flex items-start gap-2
                rounded-xl border border-amber-200
                bg-amber-50 p-4 text-amber-800
              "
            >
              <Clock3
                className="mt-0.5 h-5 w-5 shrink-0"
              />

              <p className="text-sm">
                The donation is completed only after the
                receiver confirms receipt.
              </p>
            </div>
          ) : null}
        </aside>
      </div>
    </main>
  );
}