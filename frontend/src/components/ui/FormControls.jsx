import {
  forwardRef,
  useId,
} from "react";

import { cn } from "../../lib/cn";

function FieldMessage({
  id,
  error,
  hint,
}) {
  const message = error || hint;

  if (!message) {
    return null;
  }

  return (
    <p
      id={id}
      className={cn(
        "mt-1.5 text-sm",
        error
          ? "text-red-600 dark:text-red-400"
          : "text-slate-500 dark:text-slate-400",
      )}
    >
      {message}
    </p>
  );
}

const commonControlClasses = cn(
  "focus-ring w-full rounded-xl border",
  "border-slate-300 bg-white px-3.5 py-2.5",
  "text-slate-950 shadow-sm transition",
  "placeholder:text-slate-400",
  "hover:border-slate-400",
  "disabled:cursor-not-allowed disabled:opacity-60",
  "dark:border-slate-700 dark:bg-slate-900",
  "dark:text-slate-100 dark:placeholder:text-slate-500",
);

function FieldWrapper({
  label,
  required,
  error,
  hint,
  fieldId,
  children,
  className,
}) {
  const messageId =
    error || hint
      ? `${fieldId}-message`
      : undefined;

  return (
    <div className={className}>
      <label
        htmlFor={fieldId}
        className="mb-1.5 block text-sm font-semibold text-slate-700 dark:text-slate-200"
      >
        {label}

        {required && (
          <span
            aria-hidden="true"
            className="ml-1 text-red-500"
          >
            *
          </span>
        )}
      </label>

      {children(messageId)}

      <FieldMessage
        id={messageId}
        error={error}
        hint={hint}
      />
    </div>
  );
}

export const Input = forwardRef(function Input(
  {
    id,
    label,
    required = false,
    error,
    hint,
    className,
    inputClassName,
    ...props
  },
  ref,
) {
  const generatedId = useId();
  const fieldId = id || generatedId;

  return (
    <FieldWrapper
      fieldId={fieldId}
      label={label}
      required={required}
      error={error}
      hint={hint}
      className={className}
    >
      {(messageId) => (
        <input
          ref={ref}
          id={fieldId}
          required={required}
          aria-invalid={Boolean(error)}
          aria-describedby={messageId}
          className={cn(
            commonControlClasses,
            error &&
              "border-red-500 focus-visible:ring-red-500",
            inputClassName,
          )}
          {...props}
        />
      )}
    </FieldWrapper>
  );
});

Input.displayName = "Input";

export const Select = forwardRef(function Select(
  {
    id,
    label,
    required = false,
    error,
    hint,
    className,
    selectClassName,
    children,
    ...props
  },
  ref,
) {
  const generatedId = useId();
  const fieldId = id || generatedId;

  return (
    <FieldWrapper
      fieldId={fieldId}
      label={label}
      required={required}
      error={error}
      hint={hint}
      className={className}
    >
      {(messageId) => (
        <select
          ref={ref}
          id={fieldId}
          required={required}
          aria-invalid={Boolean(error)}
          aria-describedby={messageId}
          className={cn(
            commonControlClasses,
            error && "border-red-500",
            selectClassName,
          )}
          {...props}
        >
          {children}
        </select>
      )}
    </FieldWrapper>
  );
});

Select.displayName = "Select";

export const Textarea = forwardRef(
  function Textarea(
    {
      id,
      label,
      required = false,
      error,
      hint,
      className,
      textareaClassName,
      rows = 4,
      ...props
    },
    ref,
  ) {
    const generatedId = useId();
    const fieldId = id || generatedId;

    return (
      <FieldWrapper
        fieldId={fieldId}
        label={label}
        required={required}
        error={error}
        hint={hint}
        className={className}
      >
        {(messageId) => (
          <textarea
            ref={ref}
            id={fieldId}
            rows={rows}
            required={required}
            aria-invalid={Boolean(error)}
            aria-describedby={messageId}
            className={cn(
              commonControlClasses,
              "resize-y",
              error && "border-red-500",
              textareaClassName,
            )}
            {...props}
          />
        )}
      </FieldWrapper>
    );
  },
);

Textarea.displayName = "Textarea";