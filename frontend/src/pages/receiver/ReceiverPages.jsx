import {
  useState,
} from "react";

import {
  useNavigate,
  useParams,
} from "react-router-dom";

import api from "../../lib/api";
import { getApiErrorMessage } from "../../lib/apiError";
import {
  useApiResource,
} from "../../hooks/useApiResource";

import Button from "../../components/ui/Button";
import {
  ErrorMessage,
} from "../../components/ui/FeedbackStates";
import {
  Input,
  Select,
  Textarea,
} from "../../components/ui/FormControls";
import LoadingState from "../../components/ui/LoadingState";
import {
  PageHeader,
  ResourceGrid,
  SubmitBar,
  Surface,
} from "../../components/ui/PageElements";

export function BrowseDonationsPage() {
  const [category, setCategory] =
    useState("");

  const [ordering, setOrdering] =
    useState("pickup_deadline");

  const endpoint =
    `/donations/?status=AVAILABLE` +
    `&ordering=${ordering}` +
    (category
      ? `&category=${category}`
      : "");

  const resource = useApiResource(
    endpoint,
    {
      list: true,
    },
  );

  return (
    <div>
      <PageHeader
        eyebrow="Receiver"
        title="Browse donations"
        description="Find available donations compatible with your organization."
      />

      <Surface className="mb-6">
        <div className="grid gap-4 sm:grid-cols-2">
          <Input
            label="Category"
            value={category}
            onChange={(event) =>
              setCategory(
                event.target.value,
              )
            }
            placeholder="Category code or ID"
          />

          <Select
            label="Sort by"
            value={ordering}
            onChange={(event) =>
              setOrdering(
                event.target.value,
              )
            }
          >
            <option value="pickup_deadline">
              Earliest deadline
            </option>
            <option value="-created_at">
              Newest first
            </option>
            <option value="quantity">
              Lowest quantity
            </option>
            <option value="-quantity">
              Highest quantity
            </option>
          </Select>
        </div>
      </Surface>

      <ResourceGrid
        items={resource.data}
        loading={resource.loading}
        error={resource.error}
        onRetry={resource.reload}
        emptyTitle="No compatible donations"
        emptyDescription="Try changing the filters or check again later."
        getDetailPath={(item) =>
          `/receiver/donations/${item.id}`
        }
      />
    </div>
  );
}

export function ReceiverDonationDetailPage() {
  const { donationId } = useParams();

  const {
    data,
    loading,
    error,
    reload,
  } = useApiResource(
    `/donations/${donationId}/`,
  );

  const [note, setNote] =
    useState("");

  const [submitting, setSubmitting] =
    useState(false);

  const [actionError, setActionError] =
    useState("");

  async function requestDonation() {
    setSubmitting(true);
    setActionError("");

    try {
      await api.post(
        `/donations/${donationId}/requests/`,
        {
          message: note,
        },
      );

      await reload();
    } catch (requestError) {
      setActionError(
        getApiErrorMessage(requestError),
      );
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return (
      <LoadingState message="Loading donation..." />
    );
  }

  if (error) {
    return (
      <ErrorMessage
        message={error}
        onRetry={reload}
      />
    );
  }

  return (
    <div>
      <PageHeader
        eyebrow="Available donation"
        title={
          data?.food_name ||
          "Donation"
        }
        description={
          data?.description
        }
      />

      <div className="grid gap-5 lg:grid-cols-3">
        <Surface className="lg:col-span-2">
          <h2 className="text-xl font-black">
            Donation information
          </h2>

          <div className="mt-5 grid gap-4 sm:grid-cols-2">
            <Information
              label="Quantity"
              value={`${data?.quantity ?? "—"} ${data?.unit ?? ""}`}
            />
            <Information
              label="Pickup area"
              value={data?.pickup_area}
            />
            <Information
              label="Deadline"
              value={
                data?.pickup_deadline
                  ? new Date(
                      data.pickup_deadline,
                    ).toLocaleString()
                  : "—"
              }
            />
            <Information
              label="Storage"
              value={
                data?.storage_condition
              }
            />
          </div>
        </Surface>

        <Surface>
          <h2 className="text-lg font-black">
            Request this donation
          </h2>

          {actionError && (
            <div className="mt-4">
              <ErrorMessage
                message={actionError}
              />
            </div>
          )}

          <Textarea
            className="mt-4"
            label="Message to donor"
            value={note}
            onChange={(event) =>
              setNote(event.target.value)
            }
            placeholder="Explain your requirement and collection plan."
          />

          <Button
            className="mt-4 w-full"
            isLoading={submitting}
            disabled={
              data?.status !== "AVAILABLE"
            }
            onClick={requestDonation}
          >
            Submit request
          </Button>
        </Surface>
      </div>
    </div>
  );
}

export function ReceiverRequirementsPage() {
  const {
    data,
    loading,
    error,
    reload,
  } = useApiResource(
    "/receivers/requirements/",
    {
      list: true,
    },
  );

  const [form, setForm] = useState({
    category: "",
    quantity_needed: "",
    unit: "MEALS",
    needed_until: "",
  });

  const [submitting, setSubmitting] =
    useState(false);

  async function submitRequirement(event) {
    event.preventDefault();
    setSubmitting(true);

    try {
      await api.post(
        "/receivers/requirements/",
        {
          ...form,
          quantity_needed: Number(
            form.quantity_needed,
          ),
        },
      );

      setForm({
        category: "",
        quantity_needed: "",
        unit: "MEALS",
        needed_until: "",
      });

      await reload();
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div>
      <PageHeader
        eyebrow="Receiver"
        title="Food requirements"
        description="Maintain your current category needs and receiving capacity."
      />

      <div className="grid gap-6 xl:grid-cols-[24rem_1fr]">
        <Surface>
          <h2 className="text-xl font-black">
            Add requirement
          </h2>

          <form
            className="mt-5 space-y-4"
            onSubmit={submitRequirement}
          >
            <Input
              label="Category ID"
              required
              value={form.category}
              onChange={(event) =>
                setForm({
                  ...form,
                  category:
                    event.target.value,
                })
              }
            />

            <Input
              label="Quantity needed"
              type="number"
              min="0.01"
              step="0.01"
              required
              value={
                form.quantity_needed
              }
              onChange={(event) =>
                setForm({
                  ...form,
                  quantity_needed:
                    event.target.value,
                })
              }
            />

            <Select
              label="Unit"
              value={form.unit}
              onChange={(event) =>
                setForm({
                  ...form,
                  unit:
                    event.target.value,
                })
              }
            >
              <option value="MEALS">
                Meals
              </option>
              <option value="KG">
                Kilograms
              </option>
              <option value="LITRES">
                Litres
              </option>
              <option value="PACKETS">
                Packets
              </option>
            </Select>

            <Input
              label="Needed until"
              type="datetime-local"
              required
              value={form.needed_until}
              onChange={(event) =>
                setForm({
                  ...form,
                  needed_until:
                    event.target.value,
                })
              }
            />

            <Button
              type="submit"
              className="w-full"
              isLoading={submitting}
            >
              Save requirement
            </Button>
          </form>
        </Surface>

        <ResourceGrid
          items={data}
          loading={loading}
          error={error}
          onRetry={reload}
          emptyTitle="No active requirements"
          emptyDescription="Add your organization's current food needs."
        />
      </div>
    </div>
  );
}

export function ReceiverRequestsPage() {
  const resource = useApiResource(
    "/donation-requests/?scope=receiver",
    {
      list: true,
    },
  );

  return (
    <div>
      <PageHeader
        eyebrow="Receiver"
        title="My requests"
        description="Track pending, approved, rejected and completed requests."
      />

      <ResourceGrid
        items={resource.data}
        loading={resource.loading}
        error={resource.error}
        onRetry={resource.reload}
        emptyTitle="No donation requests"
        emptyDescription="Browse available donations and submit a request."
      />
    </div>
  );
}

export function ReceiptConfirmationPage() {
  const { donationId } = useParams();
  const navigate = useNavigate();

  const [form, setForm] = useState({
    accepted_quantity: "",
    notes: "",
    discrepancy: false,
  });

  const [error, setError] =
    useState("");

  const [submitting, setSubmitting] =
    useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setSubmitting(true);
    setError("");

    try {
      await api.post(
        `/donations/${donationId}/confirm-receipt/`,
        {
          accepted_quantity: Number(
            form.accepted_quantity,
          ),
          notes: form.notes,
          discrepancy: form.discrepancy,
        },
      );

      navigate(
        "/receiver/requests",
      );
    } catch (requestError) {
      setError(
        getApiErrorMessage(requestError),
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div>
      <PageHeader
        eyebrow="Receiver"
        title="Confirm receipt"
        description="Record the actual accepted quantity after delivery."
      />

      <Surface className="mx-auto max-w-2xl">
        {error && (
          <div className="mb-5">
            <ErrorMessage message={error} />
          </div>
        )}

        <form
          className="space-y-5"
          onSubmit={handleSubmit}
        >
          <Input
            label="Accepted quantity"
            type="number"
            min="0"
            step="0.01"
            required
            value={form.accepted_quantity}
            onChange={(event) =>
              setForm({
                ...form,
                accepted_quantity:
                  event.target.value,
              })
            }
          />

          <Textarea
            label="Receipt notes"
            value={form.notes}
            onChange={(event) =>
              setForm({
                ...form,
                notes:
                  event.target.value,
              })
            }
          />

          <label className="flex min-h-11 items-center gap-3 rounded-xl border border-slate-200 p-3 dark:border-slate-700">
            <input
              type="checkbox"
              checked={form.discrepancy}
              onChange={(event) =>
                setForm({
                  ...form,
                  discrepancy:
                    event.target.checked,
                })
              }
              className="size-4 accent-blue-600"
            />

            <span className="font-semibold">
              Report a quantity or delivery discrepancy
            </span>
          </label>

          <SubmitBar
            submitLabel="Confirm receipt"
            isSubmitting={submitting}
            cancelPath="/receiver/requests"
          />
        </form>
      </Surface>
    </div>
  );
}

function Information({
  label,
  value,
}) {
  return (
    <div>
      <p className="text-sm font-semibold text-slate-500 dark:text-slate-400">
        {label}
      </p>
      <p className="mt-1 text-slate-950 dark:text-white">
        {value || "—"}
      </p>
    </div>
  );
}