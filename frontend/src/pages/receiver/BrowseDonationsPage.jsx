import {
  ArrowRight,
  CalendarClock,
  CheckCircle2,
  ChevronDown,
  HandHeart,
  LoaderCircle,
  MapPin,
  Package,
  Search,
  Truck,
  UserRoundCheck,
  X,
} from "lucide-react";
import {
  useEffect,
  useMemo,
  useState,
} from "react";
import { Link } from "react-router-dom";

import api from "../../lib/api";


const TRANSPORT_MODES = [
  {
    value: "RECEIVER_COLLECTION",
    label: "Receiver collection",
    description:
      "Your organization will collect the food from the donor.",
    icon: UserRoundCheck,
  },
  {
    value: "DONOR_DELIVERY",
    label: "Donor delivery",
    description:
      "Request the donor to deliver the food to your organization.",
    icon: Truck,
  },
  {
    value: "VOLUNTEER_DELIVERY",
    label: "Volunteer delivery",
    description:
      "Request an available volunteer to transport the donation.",
    icon: HandHeart,
  },
];


function getErrorMessage(error) {
  const data = error?.response?.data;

  if (!data) {
    return (
      "Could not connect to the SmartFood server. " +
      "Check that Django is running."
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

  return "Something went wrong. Please try again.";
}


function getResults(data) {
  if (Array.isArray(data)) {
    return data;
  }

  if (Array.isArray(data?.results)) {
    return data.results;
  }

  if (Array.isArray(data?.donations)) {
    return data.donations;
  }

  return [];
}


function getRevision(donation) {
  return (
    donation.current_revision ||
    donation.revision ||
    donation
  );
}


function getCategoryId(donation) {
  const revision = getRevision(donation);

  return String(
    revision.category?.id ||
    revision.category_id ||
    donation.category?.id ||
    donation.category_id ||
    "",
  );
}


function getCategoryName(donation) {
  const revision = getRevision(donation);

  return (
    revision.category?.name ||
    revision.category_name ||
    donation.category?.name ||
    donation.category_name ||
    "Uncategorized"
  );
}


function getImageUrl(donation) {
  const revision = getRevision(donation);
  const images = revision.images || donation.images || [];

  if (!images.length) {
    return null;
  }

  const firstImage = images[0];

  return (
    firstImage.image_url ||
    firstImage.image ||
    firstImage.url ||
    null
  );
}


function formatDateTime(value) {
  if (!value) {
    return "Not specified";
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


function getTimeRemaining(deadline) {
  if (!deadline) {
    return "Deadline unavailable";
  }

  const remaining =
    new Date(deadline).getTime() - Date.now();

  if (remaining <= 0) {
    return "Expired";
  }

  const hours = Math.floor(
    remaining / (1000 * 60 * 60),
  );

  const minutes = Math.floor(
    (remaining % (1000 * 60 * 60)) /
    (1000 * 60),
  );

  if (hours >= 24) {
    const days = Math.floor(hours / 24);

    return `${days} day${days === 1 ? "" : "s"} remaining`;
  }

  if (hours > 0) {
    return `${hours}h ${minutes}m remaining`;
  }

  return `${minutes} minute${minutes === 1 ? "" : "s"} remaining`;
}


function DonationCard({
  donation,
  requestSubmitted,
  onRequest,
}) {
  const revision = getRevision(donation);

  const imageUrl = getImageUrl(donation);
  const deadline = revision.pickup_deadline;
  const expired =
    deadline &&
    new Date(deadline).getTime() <= Date.now();

  return (
    <article
      className="
        group overflow-hidden rounded-2xl border
        border-slate-200/80 bg-white shadow-sm
        transition-all duration-200 ease-out
        hover:-translate-y-1 hover:shadow-xl
        hover:shadow-blue-500/5
      "
    >
      <div className="relative h-44 bg-slate-100">
        {imageUrl ? (
          <img
            src={imageUrl}
            alt={revision.food_name || "Food donation"}
            className="
              h-full w-full object-cover transition-transform
              duration-300 group-hover:scale-[1.03]
            "
          />
        ) : (
          <div
            className="
              flex h-full items-center justify-center
              bg-gradient-to-br from-blue-50 to-sky-100
            "
          >
            <Package
              className="h-14 w-14 text-blue-300"
              aria-hidden="true"
            />
          </div>
        )}

        <span
          className="
            absolute left-3 top-3 rounded-full bg-white/90
            px-3 py-1 text-xs font-semibold text-blue-700
            shadow-sm backdrop-blur
          "
        >
          {getCategoryName(donation)}
        </span>
      </div>

      <div className="space-y-4 p-5">
        <div>
          <h2
            className="
              line-clamp-1 text-lg font-bold text-slate-900
            "
          >
            {revision.food_name || "Food donation"}
          </h2>

          <p className="mt-1 line-clamp-2 text-sm text-slate-600">
            {revision.description ||
              "Surplus food available for redistribution."}
          </p>
        </div>

        <div className="grid grid-cols-2 gap-3 text-sm">
          <div
            className="
              rounded-xl bg-slate-50 p-3 text-slate-700
            "
          >
            <span className="block text-xs text-slate-500">
              Quantity
            </span>

            <span className="font-semibold">
              {revision.quantity} {revision.unit}
            </span>
          </div>

          <div
            className="
              rounded-xl bg-slate-50 p-3 text-slate-700
            "
          >
            <span className="block text-xs text-slate-500">
              Pickup area
            </span>

            <span className="line-clamp-1 font-semibold">
              {revision.pickup_area || "Not specified"}
            </span>
          </div>
        </div>

        <div className="space-y-2 text-sm text-slate-600">
          <div className="flex items-start gap-2">
            <MapPin
              className="
                mt-0.5 h-4 w-4 shrink-0 text-sky-500
              "
              aria-hidden="true"
            />

            <span className="line-clamp-2">
              {revision.pickup_address ||
                revision.pickup_area ||
                "Pickup location unavailable"}
            </span>
          </div>

          <div className="flex items-start gap-2">
            <CalendarClock
              className={`
                mt-0.5 h-4 w-4 shrink-0
                ${
                  expired
                    ? "text-red-500"
                    : "text-amber-500"
                }
              `}
              aria-hidden="true"
            />

            <div>
              <span className="block">
                {formatDateTime(deadline)}
              </span>

              <span
                className={`
                  text-xs font-semibold
                  ${
                    expired
                      ? "text-red-600"
                      : "text-amber-600"
                  }
                `}
              >
                {getTimeRemaining(deadline)}
              </span>
            </div>
          </div>
        </div>

        <div className="flex gap-2">
          <Link
            to={`/receiver/donations/${donation.id}`}
            className="
              inline-flex flex-1 items-center justify-center
              rounded-xl border border-slate-300 px-4 py-2.5
              text-sm font-semibold text-slate-700
              transition hover:bg-slate-50
              focus-visible:outline-none focus-visible:ring-2
              focus-visible:ring-blue-500
            "
          >
            View details
          </Link>

          <button
            type="button"
            disabled={
              expired ||
              requestSubmitted ||
              donation.status !== "AVAILABLE"
            }
            onClick={() => onRequest(donation)}
            className="
              inline-flex flex-1 items-center justify-center
              gap-2 rounded-xl bg-blue-600 px-4 py-2.5
              text-sm font-semibold text-white
              transition hover:bg-blue-700
              active:scale-[0.98]
              focus-visible:outline-none focus-visible:ring-2
              focus-visible:ring-blue-500
              focus-visible:ring-offset-2
              disabled:cursor-not-allowed disabled:bg-slate-300
            "
          >
            {requestSubmitted ? (
              <>
                <CheckCircle2
                  className="h-4 w-4"
                  aria-hidden="true"
                />
                Requested
              </>
            ) : (
              <>
                Request
                <ArrowRight
                  className="h-4 w-4"
                  aria-hidden="true"
                />
              </>
            )}
          </button>
        </div>
      </div>
    </article>
  );
}


function RequestDialog({
  donation,
  submitting,
  error,
  onClose,
  onSubmit,
}) {
  const [proposedMode, setProposedMode] = useState(
    "RECEIVER_COLLECTION",
  );

  if (!donation) {
    return null;
  }

  const revision = getRevision(donation);

  function handleSubmit(event) {
    event.preventDefault();

    onSubmit({
      proposed_mode: proposedMode,
    });
  }

  return (
    <div
      className="
        fixed inset-0 z-50 flex items-end justify-center
        bg-slate-950/50 p-0 backdrop-blur-sm
        sm:items-center sm:p-4
      "
      role="presentation"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) {
          onClose();
        }
      }}
    >
      <section
        role="dialog"
        aria-modal="true"
        aria-labelledby="request-dialog-title"
        className="
          max-h-[90vh] w-full overflow-y-auto rounded-t-3xl
          bg-white shadow-2xl sm:max-w-xl sm:rounded-3xl
        "
      >
        <div
          className="
            sticky top-0 flex items-start justify-between
            border-b border-slate-200 bg-white/90 p-5
            backdrop-blur
          "
        >
          <div>
            <p
              className="
                text-sm font-semibold uppercase tracking-wide
                text-blue-600
              "
            >
              Donation request
            </p>

            <h2
              id="request-dialog-title"
              className="mt-1 text-xl font-bold text-slate-900"
            >
              {revision.food_name}
            </h2>
          </div>

          <button
            type="button"
            onClick={onClose}
            disabled={submitting}
            aria-label="Close request form"
            className="
              rounded-xl p-2 text-slate-500 transition
              hover:bg-slate-100 hover:text-slate-800
              focus-visible:outline-none focus-visible:ring-2
              focus-visible:ring-blue-500
            "
          >
            <X className="h-5 w-5" aria-hidden="true" />
          </button>
        </div>

        <form
          onSubmit={handleSubmit}
          className="space-y-5 p-5"
        >
          <div
            className="
              rounded-2xl border border-blue-100 bg-blue-50
              p-4
            "
          >
            <p className="text-sm text-blue-900">
              Requesting{" "}
              <strong>
                {revision.quantity} {revision.unit}
              </strong>{" "}
              from{" "}
              <strong>
                {donation.donor_name || "the donor"}
              </strong>
              .
            </p>
          </div>

          <fieldset>
            <legend
              className="
                mb-3 text-sm font-semibold text-slate-900
              "
            >
              How should the donation be transported?
            </legend>

            <div className="space-y-3">
              {TRANSPORT_MODES.map((mode) => {
                const Icon = mode.icon;
                const selected =
                  proposedMode === mode.value;

                return (
                  <label
                    key={mode.value}
                    className={`
                      flex cursor-pointer items-start gap-3
                      rounded-2xl border p-4 transition
                      ${
                        selected
                          ? "border-blue-500 bg-blue-50 ring-1 ring-blue-500"
                          : "border-slate-200 hover:border-blue-300"
                      }
                    `}
                  >
                    <input
                      type="radio"
                      name="proposed_mode"
                      value={mode.value}
                      checked={selected}
                      onChange={(event) => {
                        setProposedMode(
                          event.target.value,
                        );
                      }}
                      className="sr-only"
                    />

                    <span
                      className={`
                        rounded-xl p-2
                        ${
                          selected
                            ? "bg-blue-600 text-white"
                            : "bg-slate-100 text-slate-600"
                        }
                      `}
                    >
                      <Icon
                        className="h-5 w-5"
                        aria-hidden="true"
                      />
                    </span>

                    <span>
                      <span
                        className="
                          block font-semibold text-slate-900
                        "
                      >
                        {mode.label}
                      </span>

                      <span
                        className="
                          mt-1 block text-sm text-slate-600
                        "
                      >
                        {mode.description}
                      </span>
                    </span>
                  </label>
                );
              })}
            </div>
          </fieldset>

          {error ? (
            <div
              role="alert"
              className="
                rounded-xl border border-red-200 bg-red-50
                p-3 text-sm text-red-700
              "
            >
              {error}
            </div>
          ) : null}

          <div
            className="
              flex flex-col-reverse gap-3 sm:flex-row
              sm:justify-end
            "
          >
            <button
              type="button"
              onClick={onClose}
              disabled={submitting}
              className="
                rounded-xl border border-slate-300 px-5 py-3
                font-semibold text-slate-700 transition
                hover:bg-slate-50
              "
            >
              Cancel
            </button>

            <button
              type="submit"
              disabled={submitting}
              className="
                inline-flex items-center justify-center gap-2
                rounded-xl bg-blue-600 px-5 py-3
                font-semibold text-white transition
                hover:bg-blue-700 active:scale-[0.98]
                disabled:cursor-not-allowed disabled:bg-blue-300
              "
            >
              {submitting ? (
                <>
                  <LoaderCircle
                    className="h-5 w-5 animate-spin"
                    aria-hidden="true"
                  />
                  Sending request
                </>
              ) : (
                <>
                  Submit request
                  <ArrowRight
                    className="h-5 w-5"
                    aria-hidden="true"
                  />
                </>
              )}
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}


export default function BrowseDonationsPage() {
  const [donations, setDonations] = useState([]);
  const [categories, setCategories] = useState([]);

  const [search, setSearch] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [area, setArea] = useState("");
  const [ordering, setOrdering] = useState(
    "deadline_ascending",
  );

  const [selectedDonation, setSelectedDonation] =
    useState(null);

  const [requestedIds, setRequestedIds] = useState(
    new Set(),
  );

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  const [loadError, setLoadError] = useState("");
  const [requestError, setRequestError] = useState("");
  const [successMessage, setSuccessMessage] =
    useState("");

  async function loadDonations() {
    setLoading(true);
    setLoadError("");

    try {
      /*
       * Do not send status=AVAILABLE here.
       * The current backend restricts status filtering to
       * the authenticated user's own donation history.
       */
      const [
        donationsResponse,
        categoriesResponse,
      ] = await Promise.all([
        api.get("/donations/"),
        api.get("/donations/food-categories/"),
      ]);

      const availableDonations = getResults(
        donationsResponse.data,
      ).filter((donation) => {
        const revision = getRevision(donation);
        const deadline = revision.pickup_deadline;

        return (
          donation.status === "AVAILABLE" &&
          (!deadline ||
            new Date(deadline).getTime() > Date.now())
        );
      });

      setDonations(availableDonations);
      setCategories(
        getResults(categoriesResponse.data).filter(
          (category) => category.active !== false,
        ),
      );
    } catch (error) {
      setLoadError(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDonations();
  }, []);

  const filteredDonations = useMemo(() => {
    const normalizedSearch = search
      .trim()
      .toLowerCase();

    const normalizedArea = area
      .trim()
      .toLowerCase();

    const result = donations.filter((donation) => {
      const revision = getRevision(donation);

      const matchesSearch =
        !normalizedSearch ||
        [
          revision.food_name,
          revision.description,
          getCategoryName(donation),
          donation.donor_name,
        ]
          .filter(Boolean)
          .some((value) =>
            String(value)
              .toLowerCase()
              .includes(normalizedSearch),
          );

      const matchesCategory =
        !categoryId ||
        getCategoryId(donation) === categoryId;

      const matchesArea =
        !normalizedArea ||
        [
          revision.pickup_area,
          revision.pickup_address,
        ]
          .filter(Boolean)
          .some((value) =>
            String(value)
              .toLowerCase()
              .includes(normalizedArea),
          );

      return (
        matchesSearch &&
        matchesCategory &&
        matchesArea
      );
    });

    return result.sort((first, second) => {
      const firstRevision = getRevision(first);
      const secondRevision = getRevision(second);

      if (ordering === "deadline_descending") {
        return (
          new Date(
            secondRevision.pickup_deadline,
          ).getTime() -
          new Date(
            firstRevision.pickup_deadline,
          ).getTime()
        );
      }

      if (ordering === "quantity_descending") {
        return (
          Number(secondRevision.quantity || 0) -
          Number(firstRevision.quantity || 0)
        );
      }

      return (
        new Date(
          firstRevision.pickup_deadline,
        ).getTime() -
        new Date(
          secondRevision.pickup_deadline,
        ).getTime()
      );
    });
  }, [
    donations,
    search,
    categoryId,
    area,
    ordering,
  ]);

  function openRequestDialog(donation) {
    setRequestError("");
    setSuccessMessage("");
    setSelectedDonation(donation);
  }

  function closeRequestDialog() {
    if (submitting) {
      return;
    }

    setSelectedDonation(null);
    setRequestError("");
  }

  async function submitRequest(payload) {
    if (!selectedDonation) {
      return;
    }

    setSubmitting(true);
    setRequestError("");

    try {
      await api.post(
        `/donations/${selectedDonation.id}/requests/`,
        payload,
      );

      const donationId = selectedDonation.id;

      setRequestedIds((current) => {
        const updated = new Set(current);
        updated.add(donationId);
        return updated;
      });

      setSuccessMessage(
        "Your request was submitted successfully. " +
        "The donor can now review it.",
      );

      setSelectedDonation(null);
    } catch (error) {
      setRequestError(getErrorMessage(error));
    } finally {
      setSubmitting(false);
    }
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
        <p
          className="
            text-sm font-semibold uppercase tracking-widest
            text-blue-100
          "
        >
          Receiver discovery
        </p>

        <h1 className="mt-2 text-3xl font-bold sm:text-4xl">
          Find suitable food donations
        </h1>

        <p className="mt-3 max-w-2xl text-blue-50">
          Browse available donations and request food that
          matches your organization&apos;s current needs.
        </p>
      </header>

      {successMessage ? (
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
            aria-hidden="true"
          />

          <span>{successMessage}</span>
        </div>
      ) : null}

      <section
        aria-label="Donation filters"
        className="
          rounded-2xl border border-slate-200/80 bg-white
          p-4 shadow-sm
        "
      >
        <div
          className="
            grid gap-3 sm:grid-cols-2 lg:grid-cols-4
          "
        >
          <label className="relative">
            <span className="sr-only">
              Search donations
            </span>

            <Search
              className="
                pointer-events-none absolute left-3 top-1/2
                h-5 w-5 -translate-y-1/2 text-slate-400
              "
              aria-hidden="true"
            />

            <input
              type="search"
              value={search}
              onChange={(event) =>
                setSearch(event.target.value)
              }
              placeholder="Search food..."
              className="
                w-full rounded-xl border border-slate-300
                py-3 pl-10 pr-4 text-slate-900
                outline-none transition
                focus:border-blue-500 focus:ring-2
                focus:ring-blue-500/20
              "
            />
          </label>

          <label className="relative">
            <span className="sr-only">
              Filter by category
            </span>

            <select
              value={categoryId}
              onChange={(event) =>
                setCategoryId(event.target.value)
              }
              className="
                w-full appearance-none rounded-xl border
                border-slate-300 bg-white px-4 py-3 pr-10
                text-slate-900 outline-none transition
                focus:border-blue-500 focus:ring-2
                focus:ring-blue-500/20
              "
            >
              <option value="">All categories</option>

              {categories.map((category) => (
                <option
                  key={category.id}
                  value={String(category.id)}
                >
                  {category.name}
                </option>
              ))}
            </select>

            <ChevronDown
              className="
                pointer-events-none absolute right-3 top-1/2
                h-5 w-5 -translate-y-1/2 text-slate-400
              "
              aria-hidden="true"
            />
          </label>

          <label className="relative">
            <span className="sr-only">
              Filter by pickup area
            </span>

            <MapPin
              className="
                pointer-events-none absolute left-3 top-1/2
                h-5 w-5 -translate-y-1/2 text-slate-400
              "
              aria-hidden="true"
            />

            <input
              type="search"
              value={area}
              onChange={(event) =>
                setArea(event.target.value)
              }
              placeholder="Pickup area..."
              className="
                w-full rounded-xl border border-slate-300
                py-3 pl-10 pr-4 text-slate-900
                outline-none transition
                focus:border-blue-500 focus:ring-2
                focus:ring-blue-500/20
              "
            />
          </label>

          <label className="relative">
            <span className="sr-only">
              Sort donations
            </span>

            <select
              value={ordering}
              onChange={(event) =>
                setOrdering(event.target.value)
              }
              className="
                w-full appearance-none rounded-xl border
                border-slate-300 bg-white px-4 py-3 pr-10
                text-slate-900 outline-none transition
                focus:border-blue-500 focus:ring-2
                focus:ring-blue-500/20
              "
            >
              <option value="deadline_ascending">
                Earliest deadline
              </option>

              <option value="deadline_descending">
                Latest deadline
              </option>

              <option value="quantity_descending">
                Highest quantity
              </option>
            </select>

            <ChevronDown
              className="
                pointer-events-none absolute right-3 top-1/2
                h-5 w-5 -translate-y-1/2 text-slate-400
              "
              aria-hidden="true"
            />
          </label>
        </div>
      </section>

      {loading ? (
        <section
          aria-label="Loading donations"
          className="
            grid gap-5 sm:grid-cols-2 xl:grid-cols-3
          "
        >
          {[1, 2, 3, 4, 5, 6].map((item) => (
            <div
              key={item}
              className="
                animate-pulse overflow-hidden rounded-2xl
                border border-slate-200 bg-white
              "
            >
              <div className="h-44 bg-slate-200" />

              <div className="space-y-4 p-5">
                <div className="h-5 w-2/3 rounded bg-slate-200" />
                <div className="h-4 w-full rounded bg-slate-100" />
                <div className="h-20 rounded-xl bg-slate-100" />
              </div>
            </div>
          ))}
        </section>
      ) : null}

      {!loading && loadError ? (
        <section
          className="
            rounded-2xl border border-red-200 bg-red-50
            p-6 text-center
          "
        >
          <p className="font-semibold text-red-800">
            Donations could not be loaded
          </p>

          <p className="mt-2 text-sm text-red-700">
            {loadError}
          </p>

          <button
            type="button"
            onClick={loadDonations}
            className="
              mt-4 rounded-xl bg-red-600 px-5 py-2.5
              font-semibold text-white transition
              hover:bg-red-700
            "
          >
            Try again
          </button>
        </section>
      ) : null}

      {!loading &&
      !loadError &&
      filteredDonations.length === 0 ? (
        <section
          className="
            rounded-2xl border border-dashed
            border-slate-300 bg-white p-10 text-center
          "
        >
          <Package
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
            No suitable donations found
          </h2>

          <p className="mt-2 text-sm text-slate-600">
            Change the filters or check again when donors
            publish new food.
          </p>
        </section>
      ) : null}

      {!loading &&
      !loadError &&
      filteredDonations.length > 0 ? (
        <>
          <div
            className="
              flex items-center justify-between gap-4
            "
          >
            <p className="text-sm text-slate-600">
              <strong className="text-slate-900">
                {filteredDonations.length}
              </strong>{" "}
              available donation
              {filteredDonations.length === 1 ? "" : "s"}
            </p>
          </div>

          <section
            aria-label="Available donations"
            className="
              grid gap-5 sm:grid-cols-2 xl:grid-cols-3
            "
          >
            {filteredDonations.map((donation) => (
              <DonationCard
                key={donation.id}
                donation={donation}
                requestSubmitted={requestedIds.has(
                  donation.id,
                )}
                onRequest={openRequestDialog}
              />
            ))}
          </section>
        </>
      ) : null}

      <RequestDialog
        donation={selectedDonation}
        submitting={submitting}
        error={requestError}
        onClose={closeRequestDialog}
        onSubmit={submitRequest}
      />
    </main>
  );
}