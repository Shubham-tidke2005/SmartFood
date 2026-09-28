import {
  Link,
  useParams,
} from "react-router-dom";

import {
  useApiResource,
} from "../../hooks/useApiResource";

import Button from "../../components/ui/Button";

import {
  ErrorMessage,
} from "../../components/ui/FeedbackStates";

import LoadingState from "../../components/ui/LoadingState";

import {
  PageHeader,
  ResourceGrid,
  Surface,
} from "../../components/ui/PageElements";

import StatusBadge from "../../components/ui/StatusBadge";


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

  const revision =
    data?.current_revision ||
    data ||
    {};

  const category =
    revision.category?.name ||
    revision.category_name ||
    revision.category;

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
          data?.status ? (
            <StatusBadge
              status={data.status}
            />
          ) : null
        }
      />

      <div className="grid gap-5 lg:grid-cols-3">
        <Surface className="lg:col-span-2">
          <h2 className="text-lg font-black text-slate-950 dark:text-white">
            Food information
          </h2>

          <dl className="mt-5 grid gap-5 sm:grid-cols-2">
            <Detail
              label="Quantity"
              value={
                `${revision.quantity ?? "—"} ` +
                `${revision.unit ?? ""}`
              }
            />

            <Detail
              label="Category"
              value={category}
            />

            <Detail
              label="Pickup area"
              value={
                revision.pickup_area
              }
            />

            <Detail
              label="Pickup address"
              value={
                revision.pickup_address
              }
            />

            <Detail
              label="Pickup starts"
              value={formatDate(
                revision.pickup_starts_at,
              )}
            />

            <Detail
              label="Pickup deadline"
              value={formatDate(
                revision.pickup_deadline,
              )}
            />

            <Detail
              label="Prepared at"
              value={formatDate(
                revision.prepared_at,
              )}
            />

            <Detail
              label="Use by"
              value={formatDate(
                revision.use_by_at,
              )}
            />

            <Detail
              label="Storage"
              value={
                revision.storage_condition
              }
            />

            <Detail
              label="Allergens"
              value={
                revision.allergen_information
              }
            />
          </dl>
        </Surface>

        <Surface>
          <h2 className="text-lg font-black text-slate-950 dark:text-white">
            Workflow
          </h2>

          <div className="mt-5 space-y-3">
            <Button
              variant="secondary"
              className="w-full"
              onClick={reload}
            >
              Refresh status
            </Button>

            <Link
              to={
                `/donor/donations/` +
                `${donationId}/recommendations`
              }
              className="focus-ring flex min-h-11 items-center justify-center rounded-xl bg-blue-600 px-4 py-2.5 font-bold text-white transition hover:bg-blue-700 active:scale-[0.98]"
            >
              Receiver recommendations
            </Link>

            <Link
              to="/donor/requests"
              className="focus-ring flex min-h-11 items-center justify-center rounded-xl border border-slate-300 px-4 py-2.5 font-bold text-slate-700 transition hover:bg-slate-50 dark:border-slate-600 dark:text-slate-200 dark:hover:bg-slate-700"
            >
              Review requests
            </Link>

            {data?.status &&
              data.status !==
                "AVAILABLE" && (
                <Link
                  to={
                    `/fulfilment/` +
                    `${donationId}`
                  }
                  className="focus-ring flex min-h-11 items-center justify-center rounded-xl border border-slate-300 px-4 py-2.5 font-bold text-slate-700 transition hover:bg-slate-50 dark:border-slate-600 dark:text-slate-200 dark:hover:bg-slate-700"
                >
                  Open fulfilment
                </Link>
              )}
          </div>
        </Surface>
      </div>
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

      <dd className="mt-1 break-words text-slate-950 dark:text-white">
        {value || "—"}
      </dd>
    </div>
  );
}


function formatDate(value) {
  if (!value) {
    return "—";
  }

  const date = new Date(value);

  return Number.isNaN(
    date.getTime(),
  )
    ? "—"
    : date.toLocaleString();
}