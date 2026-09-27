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

import api from "../../lib/api";

import {
  getApiErrorMessage,
} from "../../lib/apiError";


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


function normalizeList(data) {
  if (Array.isArray(data)) {
    return data;
  }

  if (Array.isArray(data?.results)) {
    return data.results;
  }

  return [];
}


function localDateTimeValue(date) {
  const offset =
    date.getTimezoneOffset() * 60000;

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

  return new Date(value).toISOString();
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

  return Object.entries(data)
    .filter(
      ([field]) =>
        !ignoredFields.includes(field),
    )
    .reduce(
      (errors, [field, value]) => {
        errors[field] =
          firstFieldMessage(value);

        return errors;
      },
      {},
    );
}


function FieldError({ message }) {
  if (!message) {
    return null;
  }

  return (
    <p
      className="mt-1.5 text-sm text-red-600"
      role="alert"
    >
      {message}
    </p>
  );
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
          className="ml-1 text-red-500"
          aria-hidden="true"
        >
          *
        </span>
      )}
    </label>
  );
}


const inputClasses =
  "min-h-12 w-full rounded-xl border border-slate-300 " +
  "bg-white px-4 py-3 text-slate-900 outline-none transition " +
  "placeholder:text-slate-400 focus:border-blue-500 " +
  "focus:ring-2 focus:ring-blue-500/20 disabled:cursor-not-allowed " +
  "disabled:bg-slate-100 dark:border-slate-600 dark:bg-slate-900 " +
  "dark:text-white dark:disabled:bg-slate-950";


export default function CreateDonationPage() {
  const navigate = useNavigate();

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

  const [fieldErrors, setFieldErrors] =
    useState({});


  const selectedCategory =
    useMemo(
      () =>
        categories.find(
          (category) =>
            String(category.id) ===
            String(form.category_id),
        ) || null,
      [categories, form.category_id],
    );


  const currentLocalTime =
    useMemo(
      () =>
        localDateTimeValue(
          new Date(),
        ),
      [],
    );


  useEffect(() => {
    let active = true;

    async function loadCategories() {
      setCategoriesLoading(true);
      setError("");

      try {
        const response = await api.get(
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
              category.active !== false,
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
          setCategoriesLoading(false);
        }
      }
    }

    loadCategories();

    return () => {
      active = false;
    };
  }, []);


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

    setFieldErrors((current) => ({
      ...current,
      [name]: "",
    }));
  }


  function handleCategoryChange(event) {
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
      category_id: categoryId,

      prepared_at:
        category?.requires_preparation_time
          ? current.prepared_at
          : "",

      use_by_at:
        category?.requires_use_by
          ? current.use_by_at
          : "",
    }));

    setError("");

    setFieldErrors((current) => ({
      ...current,
      category_id: "",
      prepared_at: "",
      use_by_at: "",
    }));
  }


  function handleImageChange(event) {
    const selectedFiles =
      Array.from(
        event.target.files || [],
      );

    setError("");
    setFieldErrors((current) => ({
      ...current,
      images: "",
    }));

    if (
      images.length +
        selectedFiles.length >
      5
    ) {
      setFieldErrors((current) => ({
        ...current,
        images:
          "A donation can contain a maximum of five images.",
      }));

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
      setFieldErrors((current) => ({
        ...current,
        images:
          "Images must be JPEG, PNG or WebP files.",
      }));

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
      setFieldErrors((current) => ({
        ...current,
        images:
          "Each image must be 5 MB or smaller.",
      }));

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
      ["PORTION", "PACKAGE"].includes(
        form.unit,
      ) &&
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

    if (!form.pickup_address.trim()) {
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
      Object.keys(errors).length === 0
    );
  }


  async function handleSubmit(event) {
    event.preventDefault();

    setError("");

    if (!validateForm()) {
      setError(
        "Review the highlighted fields before creating the donation.",
      );
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

      const response = await api.post(
        "/donations/",
        payload,
      );

      const donationId =
        response.data?.id ||
        response.data?.donation?.id;

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


  if (categoriesLoading) {
    return (
      <div
        className="flex min-h-72 items-center justify-center"
        role="status"
      >
        <div className="text-center">
          <LoaderCircle className="mx-auto h-9 w-9 animate-spin text-blue-600" />

          <p className="mt-3 text-sm text-slate-500">
            Loading donation form…
          </p>
        </div>
      </div>
    );
  }


  return (
    <div className="mx-auto max-w-4xl">
      <header className="mb-7">
        <p className="text-sm font-semibold uppercase tracking-[0.18em] text-blue-600">
          Donor
        </p>

        <h1 className="mt-2 text-3xl font-bold text-slate-900 dark:text-white">
          Create a donation
        </h1>

        <p className="mt-2 max-w-2xl text-slate-500 dark:text-slate-400">
          Provide accurate food and pickup information so a suitable receiver can respond in time.
        </p>
      </header>

      {error && (
        <div
          className="mb-6 flex gap-3 rounded-2xl border border-red-200 bg-red-50 px-4 py-4 text-sm text-red-700 dark:border-red-900/60 dark:bg-red-950/30 dark:text-red-300"
          role="alert"
        >
          <AlertCircle className="mt-0.5 h-5 w-5 shrink-0" />

          <p>{error}</p>
        </div>
      )}

      <form
        onSubmit={handleSubmit}
        encType="multipart/form-data"
        className="space-y-6"
        noValidate
      >
        <section className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm dark:border-slate-700/60 dark:bg-slate-800 sm:p-6">
          <div className="mb-6 flex items-center gap-3 border-b border-slate-200 pb-5 dark:border-slate-700">
            <span className="grid h-11 w-11 place-items-center rounded-xl bg-blue-50 text-blue-600 dark:bg-blue-950/40">
              <PackagePlus className="h-6 w-6" />
            </span>

            <div>
              <h2 className="font-semibold text-slate-900 dark:text-white">
                Food details
              </h2>

              <p className="text-sm text-slate-500 dark:text-slate-400">
                Describe the complete donation batch.
              </p>
            </div>
          </div>

          <div className="grid gap-5 sm:grid-cols-2">
            <div className="sm:col-span-2">
              <FieldLabel
                htmlFor="food_name"
                required
              >
                Food name
              </FieldLabel>

              <input
                id="food_name"
                name="food_name"
                value={form.food_name}
                onChange={handleChange}
                className={inputClasses}
                placeholder="Example: Vegetable rice meals"
                disabled={submitting}
              />

              <FieldError
                message={
                  fieldErrors.food_name
                }
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
                value={form.category_id}
                onChange={
                  handleCategoryChange
                }
                className={inputClasses}
                disabled={submitting}
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

            <div className="grid grid-cols-[1fr_150px] gap-3">
              <div>
                <FieldLabel
                  htmlFor="quantity"
                  required
                >
                  Quantity
                </FieldLabel>

                <input
                  id="quantity"
                  name="quantity"
                  type="number"
                  min="0.001"
                  step={
                    ["PORTION", "PACKAGE"]
                      .includes(form.unit)
                      ? "1"
                      : "0.001"
                  }
                  value={form.quantity}
                  onChange={handleChange}
                  className={inputClasses}
                  disabled={submitting}
                />
              </div>

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
                  onChange={handleChange}
                  className={inputClasses}
                  disabled={submitting}
                >
                  {UNIT_OPTIONS.map(
                    (unit) => (
                      <option
                        key={unit.value}
                        value={unit.value}
                      >
                        {unit.label}
                      </option>
                    ),
                  )}
                </select>
              </div>

              <div className="col-span-2">
                <FieldError
                  message={
                    fieldErrors.quantity ||
                    fieldErrors.unit
                  }
                />
              </div>
            </div>

            <div className="sm:col-span-2">
              <FieldLabel htmlFor="description">
                Description
              </FieldLabel>

              <textarea
                id="description"
                name="description"
                rows="4"
                value={form.description}
                onChange={handleChange}
                className={inputClasses}
                placeholder="Packaging, ingredients, allergens or handling information"
                disabled={submitting}
              />

              <FieldError
                message={
                  fieldErrors.description
                }
              />
            </div>

            <div className="sm:col-span-2">
              <FieldLabel
                htmlFor="storage_condition"
                required
              >
                Storage condition
              </FieldLabel>

              <input
                id="storage_condition"
                name="storage_condition"
                value={
                  form.storage_condition
                }
                onChange={handleChange}
                className={inputClasses}
                placeholder="Example: Refrigerated"
                disabled={submitting}
              />

              <FieldError
                message={
                  fieldErrors
                    .storage_condition
                }
              />
            </div>

            {selectedCategory
              ?.requires_preparation_time && (
              <div>
                <FieldLabel
                  htmlFor="prepared_at"
                  required
                >
                  Prepared at
                </FieldLabel>

                <input
                  id="prepared_at"
                  name="prepared_at"
                  type="datetime-local"
                  max={currentLocalTime}
                  value={form.prepared_at}
                  onChange={handleChange}
                  className={inputClasses}
                  disabled={submitting}
                />

                <FieldError
                  message={
                    fieldErrors.prepared_at
                  }
                />
              </div>
            )}

            {selectedCategory
              ?.requires_use_by && (
              <div>
                <FieldLabel
                  htmlFor="use_by_at"
                  required
                >
                  Use by
                </FieldLabel>

                <input
                  id="use_by_at"
                  name="use_by_at"
                  type="datetime-local"
                  min={currentLocalTime}
                  value={form.use_by_at}
                  onChange={handleChange}
                  className={inputClasses}
                  disabled={submitting}
                />

                <FieldError
                  message={
                    fieldErrors.use_by_at
                  }
                />
              </div>
            )}
          </div>
        </section>

        <section className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm dark:border-slate-700/60 dark:bg-slate-800 sm:p-6">
          <h2 className="font-semibold text-slate-900 dark:text-white">
            Pickup information
          </h2>

          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Exact addresses are shown only where operationally necessary.
          </p>

          <div className="mt-6 grid gap-5 sm:grid-cols-2">
            <div>
              <FieldLabel
                htmlFor="pickup_area"
                required
              >
                Pickup area
              </FieldLabel>

              <input
                id="pickup_area"
                name="pickup_area"
                value={form.pickup_area}
                onChange={handleChange}
                className={inputClasses}
                placeholder="Example: College Road"
                disabled={submitting}
              />

              <FieldError
                message={
                  fieldErrors.pickup_area
                }
              />
            </div>

            <div className="sm:col-span-2">
              <FieldLabel
                htmlFor="pickup_address"
                required
              >
                Complete pickup address
              </FieldLabel>

              <textarea
                id="pickup_address"
                name="pickup_address"
                rows="3"
                value={
                  form.pickup_address
                }
                onChange={handleChange}
                className={inputClasses}
                disabled={submitting}
              />

              <FieldError
                message={
                  fieldErrors.pickup_address
                }
              />
            </div>

            <div>
              <FieldLabel
                htmlFor="pickup_starts_at"
                required
              >
                Pickup starts
              </FieldLabel>

              <input
                id="pickup_starts_at"
                name="pickup_starts_at"
                type="datetime-local"
                min={currentLocalTime}
                value={
                  form.pickup_starts_at
                }
                onChange={handleChange}
                className={inputClasses}
                disabled={submitting}
              />

              <FieldError
                message={
                  fieldErrors
                    .pickup_starts_at
                }
              />
            </div>

            <div>
              <FieldLabel
                htmlFor="pickup_deadline"
                required
              >
                Pickup deadline
              </FieldLabel>

              <input
                id="pickup_deadline"
                name="pickup_deadline"
                type="datetime-local"
                min={
                  form.pickup_starts_at ||
                  currentLocalTime
                }
                value={
                  form.pickup_deadline
                }
                onChange={handleChange}
                className={inputClasses}
                disabled={submitting}
              />

              <FieldError
                message={
                  fieldErrors
                    .pickup_deadline
                }
              />
            </div>
          </div>
        </section>

        <section className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm dark:border-slate-700/60 dark:bg-slate-800 sm:p-6">
          <h2 className="font-semibold text-slate-900 dark:text-white">
            Donation images
          </h2>

          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Optional. Add up to five JPEG, PNG or WebP images. Maximum 5 MB each.
          </p>

          <label className="mt-5 flex min-h-32 cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed border-slate-300 bg-slate-50 px-5 py-6 text-center transition hover:border-blue-400 hover:bg-blue-50 focus-within:ring-2 focus-within:ring-blue-500 dark:border-slate-600 dark:bg-slate-900/50">
            <ImagePlus className="h-8 w-8 text-blue-600" />

            <span className="mt-3 text-sm font-semibold text-slate-700 dark:text-slate-200">
              Select donation images
            </span>

            <span className="mt-1 text-xs text-slate-500">
              {images.length}/5 selected
            </span>

            <input
              type="file"
              accept="image/jpeg,image/png,image/webp"
              multiple
              onChange={handleImageChange}
              className="sr-only"
              disabled={
                submitting ||
                images.length >= 5
              }
            />
          </label>

          <FieldError
            message={fieldErrors.images}
          />

          {images.length > 0 && (
            <ul className="mt-4 space-y-2">
              {images.map(
                (image, index) => (
                  <li
                    key={
                      image.name +
                      image.lastModified
                    }
                    className="flex items-center justify-between gap-3 rounded-xl border border-slate-200 px-4 py-3 dark:border-slate-700"
                  >
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium text-slate-700 dark:text-slate-200">
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
                      onClick={() =>
                        removeImage(index)
                      }
                      className="grid h-10 w-10 shrink-0 place-items-center rounded-lg text-red-600 transition hover:bg-red-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-500 dark:hover:bg-red-950/30"
                      aria-label={`Remove ${image.name}`}
                      disabled={submitting}
                    >
                      <Trash2 className="h-5 w-5" />
                    </button>
                  </li>
                ),
              )}
            </ul>
          )}
        </section>

        <div className="sticky bottom-4 flex flex-col-reverse gap-3 rounded-2xl border border-slate-200/80 bg-white/90 p-4 shadow-xl backdrop-blur-md dark:border-slate-700/60 dark:bg-slate-900/90 sm:flex-row sm:justify-end">
          <button
            type="button"
            onClick={() =>
              navigate(
                "/donor/dashboard",
              )
            }
            disabled={submitting}
            className="min-h-11 rounded-xl border border-slate-300 px-5 py-2.5 font-semibold text-slate-700 transition hover:bg-slate-50 active:scale-[0.98] disabled:opacity-60 dark:border-slate-600 dark:text-slate-200 dark:hover:bg-slate-800"
          >
            Cancel
          </button>

          <button
            type="submit"
            disabled={submitting}
            className="inline-flex min-h-11 items-center justify-center gap-2 rounded-xl bg-blue-600 px-6 py-2.5 font-semibold text-white transition hover:bg-blue-700 active:scale-[0.98] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {submitting ? (
              <LoaderCircle className="h-5 w-5 animate-spin" />
            ) : (
              <PackagePlus className="h-5 w-5" />
            )}

            {submitting
              ? "Creating donation…"
              : "Create donation"}
          </button>
        </div>
      </form>
    </div>
  );
}