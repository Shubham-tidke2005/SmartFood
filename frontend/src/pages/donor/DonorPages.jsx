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
import StatusBadge from "../../components/ui/StatusBadge";

export function CreateDonationPage() {
  const navigate = useNavigate();

  const {
    data: categories,
  } = useApiResource(
    "/donations/food-categories/",
    {
      list: true,
    },
  );

  const [form, setForm] = useState({
    food_name: "",
    category: "",
    quantity: "",
    unit: "MEALS",
    description: "",
    prepared_at: "",
    use_by_at: "",
    pickup_deadline: "",
    pickup_area: "",
    storage_condition: "",
    dietary_information: "",
    allergen_information: "",
  });

  const [error, setError] =
    useState("");

  const [isSubmitting, setIsSubmitting] =
    useState(false);

  function updateField(event) {
    const { name, value } = event.target;

    setForm((current) => ({
      ...current,
      [name]: value,
    }));
  }

  async function handleSubmit(event) {
    event.preventDefault();

    setIsSubmitting(true);
    setError("");

    try {
      const payload = {
        ...form,
        quantity: Number(form.quantity),
        category: form.category,
        prepared_at:
          form.prepared_at || null,
        use_by_at:
          form.use_by_at || null,
      };

      const response = await api.post(
        "/donations/",
        payload,
      );

      navigate(
        `/donor/donations/${response.data.id}`,
      );
    } catch (requestError) {
      setError(
        getApiErrorMessage(requestError),
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div>
      <PageHeader
        eyebrow="Donor"
        title="Create donation"
        description="List one surplus food batch with accurate quantity, preparation and pickup information."
      />

      <Surface className="mx-auto max-w-4xl">
        {error && (
          <div className="mb-6">
            <ErrorMessage message={error} />
          </div>
        )}

        <form
          className="space-y-6"
          onSubmit={handleSubmit}
        >
          <div className="grid gap-5 sm:grid-cols-2">
            <Input
              label="Food name"
              name="food_name"
              required
              value={form.food_name}
              onChange={updateField}
              placeholder="Vegetable rice meals"
            />

            <Select
              label="Food category"
              name="category"
              required
              value={form.category}
              onChange={updateField}
            >
              <option value="">
                Select category
              </option>

              {categories.map((category) => (
                <option
                  key={category.id}
                  value={
                    category.id ||
                    category.code
                  }
                >
                  {category.name}
                </option>
              ))}
            </Select>

            <Input
              label="Quantity"
              name="quantity"
              type="number"
              min="0.01"
              step="0.01"
              required
              value={form.quantity}
              onChange={updateField}
            />

            <Select
              label="Unit"
              name="unit"
              required
              value={form.unit}
              onChange={updateField}
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
              <option value="PIECES">
                Pieces
              </option>
            </Select>

            <Input
              label="Prepared at"
              name="prepared_at"
              type="datetime-local"
              value={form.prepared_at}
              onChange={updateField}
            />

            <Input
              label="Use by"
              name="use_by_at"
              type="datetime-local"
              value={form.use_by_at}
              onChange={updateField}
            />

            <Input
              label="Pickup deadline"
              name="pickup_deadline"
              type="datetime-local"
              required
              value={form.pickup_deadline}
              onChange={updateField}
            />

            <Input
              label="Pickup area"
              name="pickup_area"
              required
              value={form.pickup_area}
              onChange={updateField}
              placeholder="College Road, Nashik"
            />
          </div>

          <Textarea
            label="Description"
            name="description"
            required
            value={form.description}
            onChange={updateField}
          />

          <Textarea
            label="Storage condition"
            name="storage_condition"
            value={form.storage_condition}
            onChange={updateField}
          />

          <div className="grid gap-5 sm:grid-cols-2">
            <Textarea
              label="Dietary information"
              name="dietary_information"
              value={form.dietary_information}
              onChange={updateField}
            />

            <Textarea
              label="Allergen information"
              name="allergen_information"
              value={form.allergen_information}
              onChange={updateField}
            />
          </div>

          <SubmitBar
            submitLabel="Publish donation"
            isSubmitting={isSubmitting}
            cancelPath="/donor/history"
          />
        </form>
      </Surface>
    </div>
  );
}

export function DonorDonationDetailPage() {
  const { donationId } = useParams();

  const {
    data,
    loading,
    error,
    reload,
  } = useApiResource(
    `/donations/${donationId}/`,
  );

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
        eyebrow="Donation details"
        title={
          data?.food_name ||
          "Donation"
        }
        description={
          data?.description
        }
        action={
          data?.status && (
            <StatusBadge
              status={data.status}
            />
          )
        }
      />

      <div className="grid gap-5 lg:grid-cols-3">
        <Surface className="lg:col-span-2">
          <h2 className="text-lg font-black">
            Food information
          </h2>

          <dl className="mt-5 grid gap-5 sm:grid-cols-2">
            <Detail
              label="Quantity"
              value={`${data?.quantity ?? "—"} ${data?.unit ?? ""}`}
            />
            <Detail
              label="Pickup area"
              value={data?.pickup_area}
            />
            <Detail
              label="Pickup deadline"
              value={formatDate(
                data?.pickup_deadline,
              )}
            />
            <Detail
              label="Use by"
              value={formatDate(
                data?.use_by_at,
              )}
            />
            <Detail
              label="Storage"
              value={
                data?.storage_condition
              }
            />
            <Detail
              label="Allergens"
              value={
                data?.allergen_information
              }
            />
          </dl>
        </Surface>

        <Surface>
          <h2 className="text-lg font-black">
            Workflow
          </h2>

          <Button
            variant="secondary"
            className="mt-5 w-full"
            onClick={() =>
              reload()
            }
          >
            Refresh status
          </Button>
        </Surface>
      </div>
    </div>
  );
}

export function DonorRequestsPage() {
  const resource = useApiResource(
    "/donation-requests/?scope=donor",
    {
      list: true,
    },
  );

  return (
    <div>
      <PageHeader
        eyebrow="Donor"
        title="Receiver requests"
        description="Review requests submitted for your available donations."
      />

      <ResourceGrid
        items={resource.data}
        loading={resource.loading}
        error={resource.error}
        onRetry={resource.reload}
        emptyTitle="No receiver requests"
        emptyDescription="New requests will appear here."
      />
    </div>
  );
}

export function DonorHistoryPage() {
  const resource = useApiResource(
    "/donations/?scope=mine",
    {
      list: true,
    },
  );

  return (
    <div>
      <PageHeader
        eyebrow="Donor"
        title="Donation history"
        description="Review all your current and previous donations."
      />

      <ResourceGrid
        items={resource.data}
        loading={resource.loading}
        error={resource.error}
        onRetry={resource.reload}
        emptyTitle="No donations yet"
        emptyDescription="Create your first surplus-food listing."
        getDetailPath={(item) =>
          `/donor/donations/${item.id}`
        }
      />
    </div>
  );
}

function Detail({
  label,
  value,
}) {
  return (
    <div>
      <dt className="text-sm font-semibold text-slate-500 dark:text-slate-400">
        {label}
      </dt>
      <dd className="mt-1 text-slate-950 dark:text-white">
        {value || "—"}
      </dd>
    </div>
  );
}

function formatDate(value) {
  return value
    ? new Date(value).toLocaleString()
    : "—";
}