function firstMessage(value) {
  if (!value) {
    return null;
  }

  if (typeof value === "string") {
    return value;
  }

  if (Array.isArray(value)) {
    for (const item of value) {
      const message =
        firstMessage(item);

      if (message) {
        return message;
      }
    }

    return null;
  }

  if (typeof value === "object") {
    const preferredKeys = [
      "detail",
      "message",
      "error",
      "non_field_errors",
    ];

    for (const key of preferredKeys) {
      const message =
        firstMessage(value[key]);

      if (message) {
        return message;
      }
    }

    for (const item of Object.values(value)) {
      const message =
        firstMessage(item);

      if (message) {
        return message;
      }
    }
  }

  return null;
}


export function getApiErrorMessage(
  error,
  fallback = "Something went wrong.",
) {
  if (
    error?.code === "ERR_NETWORK"
  ) {
    return (
      "Cannot connect to the SmartFood server. " +
      "Make sure Django is running."
    );
  }

  const responseMessage =
    firstMessage(
      error?.response?.data,
    );

  if (responseMessage) {
    return responseMessage;
  }

  if (error?.message) {
    return error.message;
  }

  return fallback;
}