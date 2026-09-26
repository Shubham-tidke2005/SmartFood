import axios from "axios";


function isHtmlResponse(value) {
  if (typeof value !== "string") {
    return false;
  }

  const normalizedValue = value
    .trim()
    .toLowerCase();

  return (
    normalizedValue.startsWith(
      "<!doctype html",
    ) ||
    normalizedValue.startsWith(
      "<html",
    )
  );
}


function firstMessage(value) {
  if (typeof value === "string") {
    if (isHtmlResponse(value)) {
      return "";
    }

    return value;
  }

  if (Array.isArray(value)) {
    return value
      .map(firstMessage)
      .filter(Boolean)
      .join(" ");
  }

  if (
    value &&
    typeof value === "object"
  ) {
    return Object.values(value)
      .map(firstMessage)
      .filter(Boolean)
      .join(" ");
  }

  return "";
}


export function getApiErrorMessage(
  error,
  fallback =
    "Something went wrong. Please try again.",
) {
  if (!axios.isAxiosError(error)) {
    return error instanceof Error
      ? error.message
      : fallback;
  }

  const status =
    error.response?.status;

  const data =
    error.response?.data;

  if (status === 400) {
    return (
      firstMessage(data) ||
      "Some submitted information is invalid."
    );
  }

  if (status === 401) {
    return (
      firstMessage(data) ||
      "Your email or password is incorrect."
    );
  }

  if (status === 403) {
    return (
      firstMessage(data) ||
      "The request was rejected. Refresh the page and try again."
    );
  }

  if (status === 404) {
    return (
      firstMessage(data) ||
      "The requested resource was not found."
    );
  }

  if (status === 409) {
    return (
      firstMessage(data) ||
      "This operation conflicts with the current resource state."
    );
  }

  if (status >= 500) {
    return (
      "The SmartFood server encountered an error. " +
      "Please try again."
    );
  }

  if (data?.detail) {
    return (
      firstMessage(data.detail) ||
      fallback
    );
  }

  if (data?.message) {
    return (
      firstMessage(data.message) ||
      fallback
    );
  }

  const validationMessage =
    firstMessage(data);

  if (validationMessage) {
    return validationMessage;
  }

  if (error.code === "ERR_NETWORK") {
    return (
      "Cannot connect to the SmartFood backend. " +
      "Make sure Django is running."
    );
  }

  return error.message || fallback;
}