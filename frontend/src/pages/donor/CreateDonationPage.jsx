import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  AlertCircle,
  ImagePlus,
  LoaderCircle,
  PackagePlus,
  Trash2,
} from "lucide-react";

import {
  useNavigate,
} from "react-router-dom";

import useAuth from "../../auth/useAuth";

import api from "../../lib/api";

import {
  getApiErrorMessage,
} from "../../lib/apiError";

import {
  normalizeList,
} from "../../hooks/useApiResource";

const UNIT_OPTIONS = [
  {
    value: "KG",
    label: "Kilogram (kg)",
  },
  {
    value: "LITRE",
    label: "Litre",
  },
  {
    value: "PORTION",
    label: "Portion",
  },
  {
    value: "PACKAGE",
    label: "Package",
  },
];

const INITIAL_FORM = {
  food_name: "",
  category_id: "",
  quantity: "",
  unit: "KG",
  description: "",
  prepared_at: "",
  use_by_at: "",
  storage_condition: "",
  pickup_area: "",
  pickup_address: "",
  pickup_starts_at: "",
  pickup_deadline: "",
};

const inputClasses =
  "min-h-12 w-full rounded-xl border border-slate-300 " +
  "bg-white px-4 py-3 text-slate-900 outline-none transition " +
  "placeholder:text-slate-400 focus:border-blue-500 " +
  "focus:ring-2 focus:ring-blue-500/20 disabled:cursor-not-allowed " +
  "disabled:bg-slate-100 dark:border-slate-600 dark:bg-slate-900 " +
  "dark:text-white dark:disabled:bg-slate-950";

function localDateTimeValue(date) {
  const offset =
    date.getTimezoneOffset() *
    60000;

  return new Date(
    date.getTime() - offset,
  )
    .toISOString()
    .slice(0, 16);
}

function toIsoString(value) {
  if (!value) {
    return "";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "";
  }

  return date.toISOString();
}

function firstFieldMessage(value) {
  if (typeof value === "string") {
    return value;
  }

  if (Array.isArray(value)) {
    return value
      .map(firstFieldMessage)
      .filter(Boolean)
      .join(" ");
  }

  if (
    value &&
    typeof value === "object"
  ) {
    return Object.values(value)
      .map(firstFieldMessage)
      .filter(Boolean)
      .join(" ");
  }

  return "";
}

function getBackendFieldErrors(error) {
  const data =
    error?.response?.data;

  if (
    !data ||
    typeof data !== "object" ||
    Array.isArray(data)
  ) {
    return {};
  }

  const ignoredFields = [
    "detail",
    "message",
    "error",
  ];

  const errors =
    Object.entries(data)
      .filter(
        ([field]) =>
          !ignoredFields.includes(
            field,
          ),
      )
      .reduce(
        (
          result,
          [field, value],
        ) => {
          result[field] =
            firstFieldMessage(value);

          return result;
        },
        {},
      );

  if (
    errors.category &&
    !errors.category_id
  ) {
    errors.category_id =
      errors.category;
  }

  return errors;
}

function FieldLabel({
  children,
  htmlFor,
  required = false,
}) {
  return (
    <label
      htmlFor={htmlFor}
      className="mb-2 block text-sm font-medium text-slate-700 dark:text-slate-200"
    >
      {children}

      {required && (
        <span
          aria-hidden="true"
          className="ml-1 text-red-500"
        >
          *
        </span>
      )}
    </label>
  );
}

function FieldError({
  message,
}) {
  if (!message) {
    return null;
  }

  return (
    <p
      role="alert"
      className="mt-1.5 text-sm text-red-600 dark:text-red-400"
    >
      {message}
    </p>
  );
}

function TextField({
  label,
  name,
  type = "text",
  value,
  required = false,
  error,
  disabled = false,
  min,
  max,
  step,
  placeholder,
  onChange,
}) {
  return (
    <div>
      <FieldLabel
        htmlFor={name}
        required={required}
      >
        {label}
      </FieldLabel>

      <input
        id={name}
        name={name}
        type={type}
        value={value}
        required={required}
        disabled={disabled}
        min={min}
        max={max}
        step={step}
        placeholder={placeholder}
        aria-invalid={
          Boolean(error)
        }
        aria-describedby={
          error
            ? `${name}-error`
            : undefined
        }
        className={`${inputClasses} ${
          error
            ? "border-red-400 focus:border-red-500 focus:ring-red-500/20"
            : ""
        }`}
        onChange={onChange}
      />

      <div id={`${name}-error`}>
        <FieldError
          message={error}
        />
      </div>
    </div>
  );
}

function TextAreaField({
  label,
  name,
  value,
  required = false,
  error,
  disabled = false,
  placeholder,
  onChange,
}) {
  return (
    <div>
      <FieldLabel
        htmlFor={name}
        required={required}
      >
        {label}
      </FieldLabel>

      <textarea
        id={name}
        name={name}
        rows={5}
        value={value}
        required={required}
        disabled={disabled}
        placeholder={placeholder}
        aria-invalid={
          Boolean(error)
        }
        className={`${inputClasses} resize-y ${
          error
            ? "border-red-400 focus:border-red-500 focus:ring-red-500/20"
            : ""
        }`}
        onChange={onChange}
      />

      <FieldError
        message={error}
      />
    </div>
  );
}

export default function CreateDonationPage() {
  const navigate = useNavigate();

  const {
    user,
  } = useAuth();

  const [form, setForm] =
    useState(INITIAL_FORM);

  const [categories, setCategories] =
    useState([]);

  const [images, setImages] =
    useState([]);

  const [
    categoriesLoading,
    setCategoriesLoading,
  ] = useState(true);

  const [submitting, setSubmitting] =
    useState(false);

  const [error, setError] =
    useState("");

  const [
    fieldErrors,
    setFieldErrors,
  ] = useState({});

  const selectedCategory =
    useMemo(
      () =>
        categories.find(
          (category) =>
            String(category.id) ===
            String(
              form.category_id,
            ),
        ) || null,
      [
        categories,
        form.category_id,
      ],
    );

  const currentLocalTime =
    useMemo(
      () =>
        localDateTimeValue(
          new Date(),
        ),
      [],
    );

  const cannotCreateDonation =
    user?.is_active === false ||
    user?.verification_status !==
      "VERIFIED" ||
    user?.role?.toUpperCase() !==
      "DONOR";

  useEffect(() => {
    let active = true;

    async function loadCategories() {
      setCategoriesLoading(true);
      setError("");

      try {
        const response =
          await api.get(
            "/donations/food-categories/",
          );

        if (!active) {
          return;
        }

        const availableCategories =
          normalizeList(
            response.data,
          ).filter(
            (category) =>
              category.active !==
              false,
          );

        setCategories(
          availableCategories,
        );
      } catch (requestError) {
        if (active) {
          setError(
            getApiErrorMessage(
              requestError,
              "Unable to load food categories.",
            ),
          );
        }
      } finally {
        if (active) {
          setCategoriesLoading(
            false,
          );
        }
      }
    }

    loadCategories();

    return () => {
      active = false;
    };
  }, []);

  function clearFieldError(name) {
    setFieldErrors(
      (current) => ({
        ...current,
        [name]: "",
      }),
    );
  }

  function handleChange(event) {
    const {
      name,
      value,
    } = event.target;

    setForm((current) => ({
      ...current,
      [name]: value,
    }));

    setError("");
    clearFieldError(name);
  }

  function handleCategoryChange(
    event,
  ) {
    const categoryId =
      event.target.value;

    const category =
      categories.find(
        (item) =>
          String(item.id) ===
          String(categoryId),
      );

    setForm((current) => ({
      ...current,
      category_id:
        categoryId,
      prepared_at:
        category
          ?.requires_preparation_time
          ? current.prepared_at
          : "",
      use_by_at:
        category?.requires_use_by
          ? current.use_by_at
          : "",
    }));

    setError("");

    setFieldErrors(
      (current) => ({
        ...current,
        category_id: "",
        prepared_at: "",
        use_by_at: "",
      }),
    );
  }

  function handleImageChange(
    event,
  ) {
    const selectedFiles =
      Array.from(
        event.target.files || [],
      );

    setError("");
    clearFieldError("images");

    if (
      images.length +
        selectedFiles.length >
      5
    ) {
      setFieldErrors(
        (current) => ({
          ...current,
          images:
            "A donation can contain a maximum of five images.",
        }),
      );

      event.target.value = "";
      return;
    }

    const invalidFile =
      selectedFiles.find(
        (file) =>
          ![
            "image/jpeg",
            "image/png",
            "image/webp",
          ].includes(file.type),
      );

    if (invalidFile) {
      setFieldErrors(
        (current) => ({
          ...current,
          images:
            "Images must be JPEG, PNG or WebP files.",
        }),
      );

      event.target.value = "";
      return;
    }

    const oversizedFile =
      selectedFiles.find(
        (file) =>
          file.size >
          5 * 1024 * 1024,
      );

    if (oversizedFile) {
      setFieldErrors(
        (current) => ({
          ...current,
          images:
            "Each image must be 5 MB or smaller.",
        }),
      );

      event.target.value = "";
      return;
    }

    setImages((current) => [
      ...current,
      ...selectedFiles,
    ]);

    event.target.value = "";
  }

  function removeImage(index) {
    setImages((current) =>
      current.filter(
        (_, imageIndex) =>
          imageIndex !== index,
      ),
    );
  }

  function validateForm() {
    const errors = {};

    if (!form.food_name.trim()) {
      errors.food_name =
        "Food name is required.";
    }

    if (!form.category_id) {
      errors.category_id =
        "Select a food category.";
    }

    const quantity =
      Number(form.quantity);

    if (
      !form.quantity ||
      Number.isNaN(quantity) ||
      quantity <= 0
    ) {
      errors.quantity =
        "Quantity must be greater than zero.";
    }

    if (
      [
        "PORTION",
        "PACKAGE",
      ].includes(form.unit) &&
      !Number.isInteger(quantity)
    ) {
      errors.quantity =
        "Portion and package quantities must be whole numbers.";
    }

    if (
      !form.storage_condition.trim()
    ) {
      errors.storage_condition =
        "Storage condition is required.";
    }

    if (!form.pickup_area.trim()) {
      errors.pickup_area =
        "Pickup area is required.";
    }

    if (
      !form.pickup_address.trim()
    ) {
      errors.pickup_address =
        "Pickup address is required.";
    }

    if (!form.pickup_starts_at) {
      errors.pickup_starts_at =
        "Pickup start time is required.";
    }

    if (!form.pickup_deadline) {
      errors.pickup_deadline =
        "Pickup deadline is required.";
    }

    if (
      form.pickup_starts_at &&
      new Date(
        form.pickup_starts_at,
      ) <= new Date()
    ) {
      errors.pickup_starts_at =
        "Pickup start time must be in the future.";
    }

    if (
      form.pickup_starts_at &&
      form.pickup_deadline &&
      new Date(
        form.pickup_starts_at,
      ) >=
        new Date(
          form.pickup_deadline,
        )
    ) {
      errors.pickup_deadline =
        "Pickup deadline must be after the pickup start time.";
    }

    if (
      form.pickup_deadline &&
      new Date(
        form.pickup_deadline,
      ) <= new Date()
    ) {
      errors.pickup_deadline =
        "Pickup deadline must be in the future.";
    }

    if (
      selectedCategory
        ?.requires_preparation_time &&
      !form.prepared_at
    ) {
      errors.prepared_at =
        "Preparation time is required for this category.";
    }

    if (
      form.prepared_at &&
      new Date(form.prepared_at) >
        new Date()
    ) {
      errors.prepared_at =
        "Preparation time cannot be in the future.";
    }

    if (
      selectedCategory
        ?.requires_use_by &&
      !form.use_by_at
    ) {
      errors.use_by_at =
        "Use-by time is required for this category.";
    }

    if (
      form.use_by_at &&
      new Date(form.use_by_at) <=
        new Date()
    ) {
      errors.use_by_at =
        "Use-by time must be in the future.";
    }

    if (
      form.use_by_at &&
      form.pickup_deadline &&
      new Date(form.use_by_at) <
        new Date(
          form.pickup_deadline,
        )
    ) {
      errors.use_by_at =
        "Use-by time cannot be before the pickup deadline.";
    }

    setFieldErrors(errors);

    return (
      Object.keys(errors).length ===
      0
    );
  }

  async function handleSubmit(
    event,
  ) {
    event.preventDefault();

    setError("");

    if (cannotCreateDonation) {
      setError(
        "Only active and verified donor accounts can create donations.",
      );

      return;
    }

    if (!validateForm()) {
      setError(
        "Review the highlighted fields before creating the donation.",
      );

      window.scrollTo({
        top: 0,
        behavior: "smooth",
      });

      return;
    }

    setSubmitting(true);

    try {
      const payload =
        new FormData();

      payload.append(
        "food_name",
        form.food_name.trim(),
      );

      payload.append(
        "category_id",
        form.category_id,
      );

      payload.append(
        "quantity",
        form.quantity,
      );

      payload.append(
        "unit",
        form.unit,
      );

      payload.append(
        "description",
        form.description.trim(),
      );

      payload.append(
        "storage_condition",
        form.storage_condition.trim(),
      );

      payload.append(
        "pickup_area",
        form.pickup_area.trim(),
      );

      payload.append(
        "pickup_address",
        form.pickup_address.trim(),
      );

      payload.append(
        "pickup_starts_at",
        toIsoString(
          form.pickup_starts_at,
        ),
      );

      payload.append(
        "pickup_deadline",
        toIsoString(
          form.pickup_deadline,
        ),
      );

      if (form.prepared_at) {
        payload.append(
          "prepared_at",
          toIsoString(
            form.prepared_at,
          ),
        );
      }

      if (form.use_by_at) {
        payload.append(
          "use_by_at",
          toIsoString(
            form.use_by_at,
          ),
        );
      }

      images.forEach((image) => {
        payload.append(
          "images",
          image,
        );
      });

      const response =
        await api.post(
          "/donations/",
          payload,
        );

      const donationId =
        response.data?.id ||
        response.data
          ?.donation?.id;

      if (!donationId) {
        throw new Error(
          "Donation was created, but the response did not contain its ID.",
        );
      }

      navigate(
        `/donor/donations/${donationId}`,
        {
          replace: true,
          state: {
            success:
              "Donation created successfully.",
          },
        },
      );
    } catch (requestError) {
      setFieldErrors(
        getBackendFieldErrors(
          requestError,
        ),
      );

      setError(
        getApiErrorMessage(
          requestError,
          "Unable to create the donation.",
        ),
      );

      window.scrollTo({
        top: 0,
        behavior: "smooth",
      });
    } finally {
      setSubmitting(false);
    }
  }

  if (cannotCreateDonation) {
    return (
      <div className="mx-auto max-w-3xl">
        <div className="rounded-3xl border border-amber-200 bg-amber-50 p-6 text-amber-800 shadow-sm dark:border-amber-900 dark:bg-amber-950/40 dark:text-amber-300">
          <div className="flex items-start gap-3">
            <AlertCircle
              aria-hidden="true"
              className="mt-0.5 size-6 shrink-0"
            />

            <div>
              <h1 className="text-xl font-black">
                Donation creation unavailable
              </h1>

              <p className="mt-2 leading-7">
                Only active, verified donor
                accounts can create donation
                listings.
              </p>

              <div className="mt-4 space-y-1 text-sm">
                <p>
                  Role:{" "}
                  {user?.role ||
                    "Unknown"}
                </p>

                <p>
                  Verification status:{" "}
                  {user
                    ?.verification_status ||
                    "PENDING"}
                </p>

                <p>
                  Account status:{" "}
                  {user?.is_active ===
                  false
                    ? "SUSPENDED"
                    : "ACTIVE"}
                </p>
              </div>

              <button
                type="button"
                onClick={() =>
                  navigate(
                    "/dashboard",
                  )
                }
                className="mt-5 min-h-11 rounded-xl bg-blue-600 px-5 py-2.5 font-semibold text-white transition hover:bg-blue-700 active:scale-[0.98]"
              >
                Return to dashboard
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (categoriesLoading) {
    return (
      <div
        role="status"
        className="flex min-h-72 items-center justify-center"
      >
        <div className="text-center">
          <LoaderCircle className="mx-auto size-9 animate-spin text-blue-600" />

          <p className="mt-3 text-sm text-slate-500 dark:text-slate-400">
            Loading donation form...
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl">
      <header className="mb-7">
        <p className="text-sm font-semibold uppercase tracking-[0.18em] text-blue-600 dark:text-blue-400">
          Donor
        </p>

        <h1 className="mt-2 text-3xl font-bold text-slate-900 dark:text-white">
          Create a donation
        </h1>

        <p className="mt-2 max-w-2xl text-slate-500 dark:text-slate-400">
          Provide accurate food and pickup
          information so a suitable receiver
          can respond in time.
        </p>
      </header>

      {error && (
        <div
          role="alert"
          className="mb-6 flex gap-3 rounded-2xl border border-red-200 bg-red-50 px-4 py-4 text-sm text-red-700 dark:border-red-900/60 dark:bg-red-950/30 dark:text-red-300"
        >
          <AlertCircle
            aria-hidden="true"
            className="mt-0.5 size-5 shrink-0"
          />

          <span>{error}</span>
        </div>
      )}

      <form
        className="space-y-6"
        onSubmit={handleSubmit}
      >
        <section className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm dark:border-slate-700/60 dark:bg-slate-800 sm:p-6">
          <div className="flex items-center gap-3 border-b border-slate-200 pb-5 dark:border-slate-700">
            <div className="flex size-12 items-center justify-center rounded-2xl bg-blue-100 text-blue-600 dark:bg-blue-950 dark:text-blue-300">
              <PackagePlus
                aria-hidden="true"
                className="size-6"
              />
            </div>

            <div>
              <h2 className="text-xl font-black text-slate-950 dark:text-white">
                Food details
              </h2>

              <p className="text-sm text-slate-500 dark:text-slate-400">
                Describe the complete
                donation batch.
              </p>
            </div>
          </div>

          <div className="mt-6 grid gap-5 sm:grid-cols-2">
            <div className="sm:col-span-2">
              <TextField
                label="Food name"
                name="food_name"
                required
                value={form.food_name}
                error={
                  fieldErrors.food_name
                }
                disabled={submitting}
                placeholder="Example: Vegetable rice meals"
                onChange={handleChange}
              />
            </div>

            <div>
              <FieldLabel
                htmlFor="category_id"
                required
              >
                Food category
              </FieldLabel>

              <select
                id="category_id"
                name="category_id"
                required
                value={
                  form.category_id
                }
                disabled={submitting}
                aria-invalid={Boolean(
                  fieldErrors.category_id,
                )}
                className={`${inputClasses} ${
                  fieldErrors.category_id
                    ? "border-red-400"
                    : ""
                }`}
                onChange={
                  handleCategoryChange
                }
              >
                <option value="">
                  Select category
                </option>

                {categories.map(
                  (category) => (
                    <option
                      key={category.id}
                      value={category.id}
                    >
                      {category.name}
                    </option>
                  ),
                )}
              </select>

              <FieldError
                message={
                  fieldErrors.category_id
                }
              />
            </div>

            <div className="grid grid-cols-[1fr_10rem] gap-3">
              <TextField
                label="Quantity"
                name="quantity"
                type="number"
                required
                min="0.01"
                step="0.01"
                value={form.quantity}
                error={
                  fieldErrors.quantity
                }
                disabled={submitting}
                onChange={handleChange}
              />

              <div>
                <FieldLabel
                  htmlFor="unit"
                  required
                >
                  Unit
                </FieldLabel>

                <select
                  id="unit"
                  name="unit"
                  value={form.unit}
                  disabled={submitting}
                  className={
                    inputClasses
                  }
                  onChange={
                    handleChange
                  }
                >
                  {UNIT_OPTIONS.map(
                    (option) => (
                      <option
                        key={
                          option.value
                        }
                        value={
                          option.value
                        }
                      >
                        {option.label}
                      </option>
                    ),
                  )}
                </select>
              </div>
            </div>

            <div className="sm:col-span-2">
              <TextAreaField
                label="Description"
                name="description"
                value={
                  form.description
                }
                error={
                  fieldErrors.description
                }
                disabled={submitting}
                placeholder="Packaging, ingredients, dietary details or handling information"
                onChange={handleChange}
              />
            </div>

            <div className="sm:col-span-2">
              <TextAreaField
                label="Storage condition"
                name="storage_condition"
                required
                value={
                  form.storage_condition
                }
                error={
                  fieldErrors
                    .storage_condition
                }
                disabled={submitting}
                placeholder="Example: Keep refrigerated below 5°C"
                onChange={handleChange}
              />
            </div>
          </div>
        </section>

        <section className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm dark:border-slate-700/60 dark:bg-slate-800 sm:p-6">
          <h2 className="text-xl font-black text-slate-950 dark:text-white">
            Preparation and use-by information
          </h2>

          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Required fields depend on the
            selected food category.
          </p>

          <div className="mt-6 grid gap-5 sm:grid-cols-2">
            <TextField
              label="Prepared at"
              name="prepared_at"
              type="datetime-local"
              required={
                Boolean(
                  selectedCategory
                    ?.requires_preparation_time,
                )
              }
              max={currentLocalTime}
              value={form.prepared_at}
              error={
                fieldErrors.prepared_at
              }
              disabled={
                submitting ||
                !selectedCategory
                  ?.requires_preparation_time
              }
              onChange={handleChange}
            />

            <TextField
              label="Use by"
              name="use_by_at"
              type="datetime-local"
              required={
                Boolean(
                  selectedCategory
                    ?.requires_use_by,
                )
              }
              min={currentLocalTime}
              value={form.use_by_at}
              error={
                fieldErrors.use_by_at
              }
              disabled={
                submitting ||
                !selectedCategory
                  ?.requires_use_by
              }
              onChange={handleChange}
            />
          </div>
        </section>

        <section className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm dark:border-slate-700/60 dark:bg-slate-800 sm:p-6">
          <h2 className="text-xl font-black text-slate-950 dark:text-white">
            Pickup information
          </h2>

          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Provide the collection location
            and available pickup window.
          </p>

          <div className="mt-6 grid gap-5 sm:grid-cols-2">
            <TextField
              label="Pickup area"
              name="pickup_area"
              required
              value={
                form.pickup_area
              }
              error={
                fieldErrors.pickup_area
              }
              disabled={submitting}
              placeholder="Example: College Road, Nashik"
              onChange={handleChange}
            />

            <TextField
              label="Pickup address"
              name="pickup_address"
              required
              value={
                form.pickup_address
              }
              error={
                fieldErrors
                  .pickup_address
              }
              disabled={submitting}
              placeholder="Building, street and landmark"
              onChange={handleChange}
            />

            <TextField
              label="Pickup starts at"
              name="pickup_starts_at"
              type="datetime-local"
              required
              min={currentLocalTime}
              value={
                form.pickup_starts_at
              }
              error={
                fieldErrors
                  .pickup_starts_at
              }
              disabled={submitting}
              onChange={handleChange}
            />

            <TextField
              label="Pickup deadline"
              name="pickup_deadline"
              type="datetime-local"
              required
              min={
                form.pickup_starts_at ||
                currentLocalTime
              }
              value={
                form.pickup_deadline
              }
              error={
                fieldErrors
                  .pickup_deadline
              }
              disabled={submitting}
              onChange={handleChange}
            />
          </div>
        </section>

        <section className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm dark:border-slate-700/60 dark:bg-slate-800 sm:p-6">
          <div className="flex items-center gap-3">
            <div className="flex size-11 items-center justify-center rounded-2xl bg-sky-100 text-sky-600 dark:bg-sky-950 dark:text-sky-300">
              <ImagePlus
                aria-hidden="true"
                className="size-5"
              />
            </div>

            <div>
              <h2 className="text-xl font-black text-slate-950 dark:text-white">
                Donation images
              </h2>

              <p className="text-sm text-slate-500 dark:text-slate-400">
                Optional. Maximum five JPEG,
                PNG or WebP files.
              </p>
            </div>
          </div>

          <div className="mt-6">
            <label
              htmlFor="images"
              className="focus-ring flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed border-slate-300 p-8 text-center transition hover:border-blue-400 hover:bg-blue-50/40 dark:border-slate-600 dark:hover:border-blue-500 dark:hover:bg-blue-950/20"
            >
              <ImagePlus
                aria-hidden="true"
                className="size-8 text-blue-600"
              />

              <span className="mt-3 font-semibold text-slate-700 dark:text-slate-200">
                Select donation images
              </span>

              <span className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                Each image must be 5 MB or
                smaller
              </span>
            </label>

            <input
              id="images"
              type="file"
              accept="image/jpeg,image/png,image/webp"
              multiple
              disabled={submitting}
              className="sr-only"
              onChange={
                handleImageChange
              }
            />

            <FieldError
              message={
                fieldErrors.images
              }
            />

            {images.length > 0 && (
              <ul className="mt-4 space-y-2">
                {images.map(
                  (image, index) => (
                    <li
                      key={`${image.name}-${image.lastModified}-${index}`}
                      className="flex items-center justify-between gap-4 rounded-xl border border-slate-200 p-3 dark:border-slate-700"
                    >
                      <div className="min-w-0">
                        <p className="truncate font-medium text-slate-800 dark:text-slate-200">
                          {image.name}
                        </p>

                        <p className="text-xs text-slate-500">
                          {(
                            image.size /
                            1024 /
                            1024
                          ).toFixed(2)}{" "}
                          MB
                        </p>
                      </div>

                      <button
                        type="button"
                        aria-label={`Remove ${image.name}`}
                        disabled={submitting}
                        className="flex size-10 shrink-0 items-center justify-center rounded-xl text-red-600 transition hover:bg-red-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-500 disabled:opacity-50 dark:hover:bg-red-950/30"
                        onClick={() =>
                          removeImage(
                            index,
                          )
                        }
                      >
                        <Trash2
                          aria-hidden="true"
                          className="size-5"
                        />
                      </button>
                    </li>
                  ),
                )}
              </ul>
            )}
          </div>
        </section>

        <div className="flex flex-col-reverse gap-3 rounded-2xl border border-slate-200/80 bg-white p-4 shadow-sm dark:border-slate-700/60 dark:bg-slate-800 sm:flex-row sm:justify-end">
          <button
            type="button"
            disabled={submitting}
            className="min-h-11 rounded-xl border border-slate-300 px-5 py-2.5 font-semibold text-slate-700 transition hover:bg-slate-50 active:scale-[0.98] disabled:opacity-60 dark:border-slate-600 dark:text-slate-200 dark:hover:bg-slate-700"
            onClick={() =>
              navigate("/dashboard")
            }
          >
            Cancel
          </button>

          <button
            type="submit"
            disabled={submitting}
            className="inline-flex min-h-11 items-center justify-center gap-2 rounded-xl bg-blue-600 px-6 py-2.5 font-semibold text-white transition hover:bg-blue-700 active:scale-[0.98] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {submitting ? (
              <LoaderCircle
                aria-hidden="true"
                className="size-5 animate-spin"
              />
            ) : (
              <PackagePlus
                aria-hidden="true"
                className="size-5"
              />
            )}

            {submitting
              ? "Creating donation..."
              : "Create donation"}
          </button>
        </div>
      </form>
    </div>
  );
}