import axios from "axios";

import {
  clearAccessToken,
  getAccessToken,
  setAccessToken,
} from "../auth/tokenStore";

const baseURL =
  import.meta.env.VITE_API_BASE_URL ||
  "/api";


export const api = axios.create({
  baseURL,
  withCredentials: true,
  headers: {
    Accept: "application/json",
  },
});


const csrfClient = axios.create({
  baseURL,
  withCredentials: true,
  headers: {
    Accept: "application/json",
  },
});


const refreshClient = axios.create({
  baseURL,
  withCredentials: true,
  headers: {
    Accept: "application/json",
    "Content-Type": "application/json",
  },
});


let csrfPromise = null;
let refreshPromise = null;


/*
 * Read a cookie stored by Django.
 *
 * Django's default CSRF cookie name is "csrftoken".
 */
function getCookie(name) {
  const cookies = document.cookie
    ? document.cookie.split(";")
    : [];

  for (const cookie of cookies) {
    const trimmedCookie = cookie.trim();

    if (
      trimmedCookie.startsWith(
        `${encodeURIComponent(name)}=`,
      )
    ) {
      return decodeURIComponent(
        trimmedCookie.substring(
          trimmedCookie.indexOf("=") + 1,
        ),
      );
    }
  }

  return null;
}


function isUnsafeMethod(method) {
  return [
    "post",
    "put",
    "patch",
    "delete",
  ].includes(
    String(method || "get").toLowerCase(),
  );
}


function extractAccessToken(data) {
  return (
    data?.access ||
    data?.access_token ||
    data?.tokens?.access ||
    null
  );
}


/*
 * Calls Django's CSRF endpoint.
 *
 * Django will place the CSRF token in a browser cookie.
 */
export async function ensureCsrfCookie() {
  const existingToken = getCookie("csrftoken");

  if (existingToken) {
    return existingToken;
  }

  if (!csrfPromise) {
    csrfPromise = csrfClient
      .get("/auth/csrf/")
      .then((response) => {
        const cookieToken =
          getCookie("csrftoken");

        const responseToken =
          response.data?.csrfToken ||
          response.data?.csrf_token ||
          response.data?.token;

        const csrfToken =
          cookieToken || responseToken;

        if (!csrfToken) {
          throw new Error(
            "Django did not create a CSRF cookie.",
          );
        }

        return csrfToken;
      })
      .finally(() => {
        csrfPromise = null;
      });
  }

  return csrfPromise;
}


/*
 * Refresh the short-lived JWT access token.
 *
 * The refresh token remains in the HTTP-only cookie.
 */
export async function refreshAccessToken() {
  if (!refreshPromise) {
    refreshPromise = (async () => {
      const csrfToken =
        await ensureCsrfCookie();

      const response =
        await refreshClient.post(
          "/auth/refresh/",
          {},
          {
            headers: {
              "X-CSRFToken": csrfToken,
            },
          },
        );

      const accessToken =
        extractAccessToken(response.data);

      if (!accessToken) {
        throw new Error(
          "The refresh response did not contain an access token.",
        );
      }

      setAccessToken(accessToken);

      return accessToken;
    })()
      .catch((error) => {
        clearAccessToken();
        throw error;
      })
      .finally(() => {
        refreshPromise = null;
      });
  }

  return refreshPromise;
}


/*
 * Before every request:
 *
 * 1. Add JWT access token if available.
 * 2. Add CSRF protection for POST, PUT, PATCH and DELETE.
 */
api.interceptors.request.use(
  async (config) => {
    const accessToken =
      getAccessToken();

    if (accessToken) {
      config.headers.Authorization =
        `Bearer ${accessToken}`;
    }

    if (isUnsafeMethod(config.method)) {
      const csrfToken =
        await ensureCsrfCookie();

      config.headers["X-CSRFToken"] =
        csrfToken;
    }

    return config;
  },
  (error) => Promise.reject(error),
);


/*
 * If an access token expires, refresh it once and retry
 * the original request.
 */
api.interceptors.response.use(
  (response) => response,

  async (error) => {
    const originalRequest = error.config;

    const isUnauthorized =
      error.response?.status === 401;

    const isRefreshRequest =
      originalRequest?.url?.includes(
        "/auth/refresh/",
      );

    const isLoginRequest =
      originalRequest?.url?.includes(
        "/auth/login/",
      );

    if (
      !isUnauthorized ||
      !originalRequest ||
      originalRequest._retry ||
      isRefreshRequest ||
      isLoginRequest
    ) {
      return Promise.reject(error);
    }

    originalRequest._retry = true;

    try {
      const accessToken =
        await refreshAccessToken();

      originalRequest.headers = {
        ...originalRequest.headers,
        Authorization:
          `Bearer ${accessToken}`,
      };

      if (
        isUnsafeMethod(
          originalRequest.method,
        )
      ) {
        const csrfToken =
          await ensureCsrfCookie();

        originalRequest.headers[
          "X-CSRFToken"
        ] = csrfToken;
      }

      return api(originalRequest);
    } catch (refreshError) {
      clearAccessToken();

      window.dispatchEvent(
        new CustomEvent(
          "smartfood:session-expired",
        ),
      );

      return Promise.reject(
        refreshError,
      );
    }
  },
);


export default api;