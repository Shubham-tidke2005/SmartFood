import {
  useCallback,
  useEffect,
  useState,
} from "react";

import api from "../lib/api";
import { getApiErrorMessage } from "../lib/apiError";

export function normalizeList(data) {
  if (Array.isArray(data)) {
    return data;
  }

  if (Array.isArray(data?.results)) {
    return data.results;
  }

  if (Array.isArray(data?.data)) {
    return data.data;
  }

  if (Array.isArray(data?.items)) {
    return data.items;
  }

  return [];
}

export function useApiResource(
  endpoint,
  {
    enabled = true,
    list = false,
  } = {},
) {
  const [data, setData] = useState(
    list ? [] : null,
  );

  const [loading, setLoading] =
    useState(enabled);

  const [error, setError] =
    useState("");

  const reload = useCallback(async () => {
    if (!enabled || !endpoint) {
      setLoading(false);
      return null;
    }

    setLoading(true);
    setError("");

    try {
      const response =
        await api.get(endpoint);

      const responseData = list
        ? normalizeList(response.data)
        : response.data;

      setData(responseData);

      return responseData;
    } catch (requestError) {
      setError(
        getApiErrorMessage(requestError),
      );

      return null;
    } finally {
      setLoading(false);
    }
  }, [enabled, endpoint, list]);

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