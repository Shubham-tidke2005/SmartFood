import {
  useCallback,
  useEffect,
  useState,
} from "react";

import api from "../lib/api";
import {
  getApiErrorMessage,
} from "../lib/apiError";

const LIST_KEYS = [
  "results",
  "items",
  "data",
  "donations",
  "requirements",
  "requests",
  "tasks",
  "notifications",
  "users",
  "complaints",
  "recommendations",
  "records",
];

export function normalizeList(
  data,
  visited = new Set(),
) {
  if (Array.isArray(data)) {
    return data;
  }

  if (
    !data ||
    typeof data !== "object"
  ) {
    return [];
  }

  if (visited.has(data)) {
    return [];
  }

  visited.add(data);

  for (const key of LIST_KEYS) {
    const value = data[key];

    if (Array.isArray(value)) {
      return value;
    }

    if (
      value &&
      typeof value === "object"
    ) {
      const nestedItems =
        normalizeList(
          value,
          visited,
        );

      if (nestedItems.length) {
        return nestedItems;
      }
    }
  }

  return [];
}

export function useApiResource(
  endpoint,
  {
    enabled = true,
    list = false,
    initialData,
  } = {},
) {
  const defaultData =
    initialData !== undefined
      ? initialData
      : list
        ? []
        : null;

  const [data, setData] =
    useState(defaultData);

  const [loading, setLoading] =
    useState(
      Boolean(
        enabled &&
        endpoint,
      ),
    );

  const [error, setError] =
    useState("");

  const reload =
    useCallback(async () => {
      if (!enabled || !endpoint) {
        setLoading(false);

        return list
          ? []
          : null;
      }

      setLoading(true);
      setError("");

      try {
        const response =
          await api.get(endpoint);

        const responseData =
          list
            ? normalizeList(
                response.data,
              )
            : response.data;

        setData(responseData);

        return responseData;
      } catch (requestError) {
        const message =
          getApiErrorMessage(
            requestError,
          );

        setError(message);

        return null;
      } finally {
        setLoading(false);
      }
    }, [
      enabled,
      endpoint,
      list,
    ]);

  useEffect(() => {
    reload();
  }, [reload]);

  return {
    data,
    setData,
    loading,
    error,
    reload,
  };
}