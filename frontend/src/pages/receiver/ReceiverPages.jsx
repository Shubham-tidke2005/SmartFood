import {
  useMemo,
  useState,
} from "react";

import {
  useNavigate,
  useParams,
} from "react-router-dom";

import api from "../../lib/api";

import {
  getApiErrorMessage,
} from "../../lib/apiError";

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

import StatusBadge from "../../components/ui/StatusBadge";


const UNIT_OPTIONS = [
  {
    value: "PORTION",
    label: "Portions / Meals",
  },
  {
    value: "KG",
    label: "Kilograms",
  },
  {
    value: "LITRE",
    label: "Litres",
  },
  {
    value: "PACKAGE",
    label: "Packages",
  },
];


export function BrowseDonationsPage() {
  const [category, setCategory] =
    useState("");

  const [ordering, setOrdering] =
    useState("pickup_deadline");

  const {
    data: categories,
  } = useApiResource(
    "/donations/food-categories/",
    {
      list: true,
    },
  );

  const endpoint = useMemo(() => {
    const parameters =
      new URLSearchParams();

    parameters.set(
      "ordering",
      ordering,
    );

    if (category) {
      parameters.set(
        "category",
        category,
      );
    }

    return (
      `/donations/?${parameters.toString()}`
    );
  }, [
    category,
    ordering,
  ]);

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
        description="Find available food donations compatible with your organization's requirements."
      />

      <Surface className="mb-6">
        <div className="grid gap-4 sm:grid-cols-2">
          <Select
            label="Food category"
            value={category}
            onChange={(event) =>
              setCategory(
                event.target.value,
              )
            }
          >
            <option value="">
              All categories
            </option>

            {(categories || []).map(
              (categoryItem) => (
                <option
                  key={
                    categoryItem.id ||
                    categoryItem.code
                  }
                  value={
                    categoryItem.id ||
                    categoryItem.code
                  }
                >
                  {categoryItem.name}
                </option>
              ),
            )}
          </Select>

          <Select
            label="Sort donations"
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

        <div className="mt-4 flex flex-wrap gap-3">
          <Button
            variant="secondary"
            size="sm"
            onClick={resource.reload}
          >
            Refresh
          </Button>

          {(category ||
            ordering !==
              "pickup_deadline") && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setCategory("");

                setOrdering(
                  "pickup_deadline",
                );
              }}
            >
              Clear filters
            </Button>
          )}
        </div>
      </Surface>

      <ResourceGrid
        items={resource.data}
        loading={resource.loading}
        error={resource.error}
        onRetry={resource.reload}
        emptyTitle="No compatible donations"
        emptyDescription="Try another category or check again later."
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

  const [
    proposedMode,
    setProposedMode,
  ] = useState(
    "RECEIVER_COLLECTION",
  );

  const [submitting, setSubmitting] =
    useState(false);

  const [
    actionError,
    setActionError,
  ] = useState("");

  const [
    successMessage,
    setSuccessMessage,
  ] = useState("");

  async function requestDonation() {
    if (!note.trim()) {
      setActionError(
        "Enter a message explaining your requirement and collection plan.",
      );

      return;
    }

    setSubmitting(true);
    setActionError("");
    setSuccessMessage("");

    try {
      await api.post(
        `/donations/${donationId}/requests/`,
        {
          message: note.trim(),
          proposed_mode:
            proposedMode,
        },
      );

      setNote("");

      setSuccessMessage(
        "Your request was submitted successfully.",
      );

      await reload();
    } catch (requestError) {
      setActionError(
        getApiErrorMessage(
          requestError,
        ),
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

  const revision =
    data?.current_revision ||
    data ||
    {};

  return (
    <div>
      <PageHeader
        eyebrow="Donation details"
        title={
          revision.food_name ||
          "Donation"
        }
        description={
          revision.description
        }
        action={
          data?.status && (
            <StatusBadge
              status={data.status}
            />
          )
        }
      />

      {successMessage && (
        <p
          role="status"
          className="mb-5 rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-emerald-700 dark:border-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-300"
        >
          {successMessage}
        </p>
      )}

      <div className="grid gap-5 lg:grid-cols-3">
        <Surface className="lg:col-span-2">
          <h2 className="text-xl font-black text-slate-950 dark:text-white">
            Food information
          </h2>

          <div className="mt-5 grid gap-5 sm:grid-cols-2">
            <Information
              label="Quantity"
              value={
                `${revision.quantity ?? "—"} ` +
                `${revision.unit ?? ""}`
              }
            />

            <Information
              label="Category"
              value={
                revision.category_name ||
                revision.category?.name ||
                revision.category
              }
            />

            <Information
              label="Pickup area"
              value={
                revision.pickup_area ||
                revision.pickup_location
              }
            />

            <Information
              label="Pickup deadline"
              value={formatDateTime(
                revision.pickup_deadline,
              )}
            />

            <Information
              label="Prepared at"
              value={formatDateTime(
                revision.prepared_at,
              )}
            />

            <Information
              label="Use by"
              value={formatDateTime(
                revision.use_by_at,
              )}
            />

            <Information
              label="Storage condition"
              value={
                revision.storage_condition
              }
            />

            <Information
              label="Dietary information"
              value={
                revision.dietary_information
              }
            />

            <Information
              label="Allergen information"
              value={
                revision.allergen_information
              }
            />

            <Information
              label="Approximate distance"
              value={
                data
                  ?.approximate_distance_km
                  ? (
                    `${data.approximate_distance_km} ` +
                    "km straight-line distance"
                  )
                  : "—"
              }
            />
          </div>
        </Surface>

        <Surface>
          <h2 className="text-lg font-black text-slate-950 dark:text-white">
            Request this donation
          </h2>

          <p className="mt-2 text-sm leading-6 text-slate-500 dark:text-slate-400">
            The donor must approve one receiver before
            collection can begin.
          </p>

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
            required
            rows={5}
            value={note}
            disabled={submitting}
            onChange={(event) => {
              setNote(
                event.target.value,
              );

              setActionError("");
              setSuccessMessage("");
            }}
            placeholder="Explain your requirement and collection plan."
          />

          <Select
            className="mt-4"
            label="Preferred transport"
            value={proposedMode}
            disabled={submitting}
            onChange={(event) =>
              setProposedMode(
                event.target.value,
              )
            }
          >
            <option value="RECEIVER_COLLECTION">
              Receiver collection
            </option>

            <option value="DONOR_DELIVERY">
              Donor delivery
            </option>

            <option value="VOLUNTEER_DELIVERY">
              Volunteer delivery
            </option>
          </Select>

          <Button
            className="mt-4 w-full"
            isLoading={submitting}
            disabled={
              submitting ||
              data?.status !==
                "AVAILABLE"
            }
            onClick={
              requestDonation
            }
          >
            Submit request
          </Button>

          {data?.status !==
            "AVAILABLE" && (
            <p className="mt-3 text-sm text-amber-700 dark:text-amber-300">
              This donation is no longer accepting
              requests.
            </p>
          )}
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

  const {
    data: categories,
  } = useApiResource(
    "/donations/food-categories/",
    {
      list: true,
    },
  );

  const [form, setForm] =
    useState({
      category: "",
      quantity_needed: "",
      unit: "PORTION",
      needed_until: "",
    });

  const [
    submitError,
    setSubmitError,
  ] = useState("");

  const [
    successMessage,
    setSuccessMessage,
  ] = useState("");

  const [submitting, setSubmitting] =
    useState(false);

  function updateField(event) {
    const {
      name,
      value,
    } = event.target;

    setForm((current) => ({
      ...current,
      [name]: value,
    }));

    setSubmitError("");
    setSuccessMessage("");
  }

  async function submitRequirement(
    event,
  ) {
    event.preventDefault();

    const quantity =
      Number(
        form.quantity_needed,
      );

    if (
      !form.category ||
      !Number.isFinite(quantity) ||
      quantity <= 0 ||
      !form.needed_until
    ) {
      setSubmitError(
        "Select a category, enter a positive quantity and provide a deadline.",
      );

      return;
    }

    setSubmitting(true);
    setSubmitError("");
    setSuccessMessage("");

    try {
      await api.post(
        "/receivers/requirements/",
        {
          category_id:
            form.category,
          quantity_needed:
            quantity,
          unit: form.unit,
          needed_until:
            form.needed_until,
        },
      );

      setForm({
        category: "",
        quantity_needed: "",
        unit: "PORTION",
        needed_until: "",
      });

      setSuccessMessage(
        "Requirement saved successfully.",
      );

      await reload();
    } catch (requestError) {
      setSubmitError(
        getApiErrorMessage(
          requestError,
        ),
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div>
      <PageHeader
        eyebrow="Receiver"
        title="Food requirements"
        description="Maintain your organization's current food requirements."
      />

      <div className="grid gap-6 xl:grid-cols-[24rem_1fr]">
        <Surface>
          <h2 className="text-xl font-black text-slate-950 dark:text-white">
            Add requirement
          </h2>

          {successMessage && (
            <p
              role="status"
              className="mt-4 rounded-xl bg-emerald-50 p-3 text-sm text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300"
            >
              {successMessage}
            </p>
          )}

          {submitError && (
            <div className="mt-4">
              <ErrorMessage
                message={
                  submitError
                }
              />
            </div>
          )}

          <form
            className="mt-5 space-y-4"
            onSubmit={
              submitRequirement
            }
          >
            <Select
              label="Food category"
              name="category"
              required
              value={form.category}
              disabled={submitting}
              onChange={updateField}
            >
              <option value="">
                Select category
              </option>

              {(categories || []).map(
                (categoryItem) => (
                  <option
                    key={
                      categoryItem.id ||
                      categoryItem.code
                    }
                    value={
                      categoryItem.id ||
                      categoryItem.code
                    }
                  >
                    {
                      categoryItem.name
                    }
                  </option>
                ),
              )}
            </Select>

            <Input
              label="Quantity needed"
              name="quantity_needed"
              type="number"
              min="0.001"
              step="0.001"
              required
              value={
                form.quantity_needed
              }
              disabled={submitting}
              onChange={updateField}
            />

            <Select
              label="Unit"
              name="unit"
              required
              value={form.unit}
              disabled={submitting}
              onChange={updateField}
            >
              {UNIT_OPTIONS.map(
                (unitOption) => (
                  <option
                    key={
                      unitOption.value
                    }
                    value={
                      unitOption.value
                    }
                  >
                    {
                      unitOption.label
                    }
                  </option>
                ),
              )}
            </Select>

            <Input
              label="Needed until"
              name="needed_until"
              type="date"
              required
              value={
                form.needed_until
              }
              disabled={submitting}
              onChange={updateField}
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

        <div>
          <h2 className="mb-4 text-xl font-black text-slate-950 dark:text-white">
            Active requirements
          </h2>

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
    </div>
  );
}


export function ReceiverRequestsPage() {
  const resource =
    useApiResource(
      "/donations/requests/",
      {
        list: true,
      },
    );

  return (
    <div>
      <PageHeader
        eyebrow="Receiver"
        title="My requests"
        description="Track pending, approved, rejected, withdrawn and completed requests."
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
  const { donationId } =
    useParams();

  const navigate =
    useNavigate();

  const [form, setForm] =
    useState({
      accepted_quantity: "",
      unit: "PORTION",
      discrepancy_type:
        "NONE",
      discrepancy_notes: "",
      received_at:
        toLocalDateTimeValue(
          new Date(),
        ),
    });

  const [error, setError] =
    useState("");

  const [submitting, setSubmitting] =
    useState(false);

  function updateField(event) {
    const {
      name,
      value,
    } = event.target;

    setForm((current) => ({
      ...current,
      [name]: value,
    }));

    setError("");
  }

  async function handleSubmit(
    event,
  ) {
    event.preventDefault();

    const acceptedQuantity =
      Number(
        form.accepted_quantity,
      );

    if (
      !Number.isFinite(
        acceptedQuantity,
      ) ||
      acceptedQuantity < 0
    ) {
      setError(
        "Enter a valid accepted quantity.",
      );

      return;
    }

    if (
      form.discrepancy_type !==
        "NONE" &&
      !form.discrepancy_notes.trim()
    ) {
      setError(
        "Enter discrepancy notes.",
      );

      return;
    }

    setSubmitting(true);
    setError("");

    try {
      await api.post(
        `/logistics/donations/${donationId}/receipt/`,
        {
          accepted_quantity:
            acceptedQuantity,

          unit:
            form.unit,

          discrepancy_type:
            form.discrepancy_type,

          discrepancy_notes:
            form.discrepancy_notes.trim(),

          received_at:
            new Date(
              form.received_at,
            ).toISOString(),
        },
      );

      navigate(
        "/receiver/requests",
        {
          replace: true,
        },
      );
    } catch (requestError) {
      setError(
        getApiErrorMessage(
          requestError,
        ),
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
        description="Record the actual quantity accepted by your organization."
      />

      <Surface className="mx-auto max-w-2xl">
        {error && (
          <div className="mb-5">
            <ErrorMessage
              message={error}
            />
          </div>
        )}

        <form
          className="space-y-5"
          onSubmit={handleSubmit}
        >
          <div className="grid gap-5 sm:grid-cols-2">
            <Input
              label="Accepted quantity"
              name="accepted_quantity"
              type="number"
              min="0"
              step="0.001"
              required
              value={
                form.accepted_quantity
              }
              disabled={submitting}
              onChange={updateField}
            />

            <Select
              label="Unit"
              name="unit"
              required
              value={form.unit}
              disabled={submitting}
              onChange={updateField}
            >
              {UNIT_OPTIONS.map(
                (unitOption) => (
                  <option
                    key={
                      unitOption.value
                    }
                    value={
                      unitOption.value
                    }
                  >
                    {
                      unitOption.label
                    }
                  </option>
                ),
              )}
            </Select>
          </div>

          <Input
            label="Received at"
            name="received_at"
            type="datetime-local"
            required
            value={
              form.received_at
            }
            disabled={submitting}
            onChange={updateField}
          />

          <Select
            label="Discrepancy"
            name="discrepancy_type"
            value={
              form.discrepancy_type
            }
            disabled={submitting}
            onChange={updateField}
          >
            <option value="NONE">
              No discrepancy
            </option>

            <option value="SHORTAGE">
              Quantity shortage
            </option>

            <option value="DAMAGE">
              Damaged food or packaging
            </option>

            <option value="QUALITY">
              Quality concern
            </option>

            <option value="WRONG_ITEM">
              Wrong food item
            </option>

            <option value="OTHER">
              Other
            </option>
          </Select>

          <Textarea
            label="Discrepancy notes"
            name="discrepancy_notes"
            rows={5}
            required={
              form.discrepancy_type !==
              "NONE"
            }
            value={
              form.discrepancy_notes
            }
            disabled={submitting}
            onChange={updateField}
            placeholder="Explain any difference in quantity, condition or food item."
          />

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

      <p className="mt-1 break-words text-slate-950 dark:text-white">
        {value || "—"}
      </p>
    </div>
  );
}


function formatDateTime(value) {
  if (!value) {
    return "—";
  }

  const date =
    new Date(value);

  return Number.isNaN(
    date.getTime(),
  )
    ? "—"
    : date.toLocaleString();
}


function toLocalDateTimeValue(
  date,
) {
  const timezoneOffset =
    date.getTimezoneOffset() *
    60000;

  return new Date(
    date.getTime() -
      timezoneOffset,
  )
    .toISOString()
    .slice(0, 16);
}