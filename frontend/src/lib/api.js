import axios from "axios";


let accessToken = null;
let refreshPromise = null;
let csrfPromise = null;


function readCookie(name) {
  const cookies = document.cookie
    .split(";")
    .map((cookie) => cookie.trim());

  const match = cookies.find((cookie) =>
    cookie.startsWith(`${name}=`)
  );

  if (!match) {
    return null;
  }

  return decodeURIComponent(
    match.substring(name.length + 1)
  );
}


export function setAccessToken(token) {
  accessToken = token || null;
}


export function getAccessToken() {
  return accessToken;
}


function extractAccessToken(data) {
  return (
    data?.access ||
    data?.access_token ||
    null
  );
}


const api = axios.create({
  baseURL: "/api",
  withCredentials: true,
  headers: {
    Accept: "application/json",
  },
});


api.interceptors.request.use((config) => {
  if (accessToken) {
    config.headers.Authorization =
      `Bearer ${accessToken}`;
  }

  const method = (
    config.method || "get"
  ).toLowerCase();

  const unsafeMethods = [
    "post",
    "put",
    "patch",
    "delete",
  ];

  if (unsafeMethods.includes(method)) {
    const csrfToken =
      readCookie("csrftoken");

    if (csrfToken) {
      config.headers["X-CSRFToken"] =
        csrfToken;
    }
  }

  return config;
});


export async function ensureCsrfCookie() {
  if (!csrfPromise) {
    csrfPromise = api
      .get("/auth/csrf/", {
        skipAuthRefresh: true,
      })
      .finally(() => {
        csrfPromise = null;
      });
  }

  await csrfPromise;

  return readCookie("csrftoken");
}


export async function refreshAccessToken() {
  if (!refreshPromise) {
    refreshPromise = (async () => {
      await ensureCsrfCookie();

      const response = await api.post(
        "/auth/refresh/",
        {},
        {
          skipAuthRefresh: true,
        },
      );

      const token = extractAccessToken(
        response.data,
      );

      if (!token) {
        throw new Error(
          "The refresh response did not contain an access token.",
        );
      }

      setAccessToken(token);

      return response.data;
    })().finally(() => {
      refreshPromise = null;
    });
  }

  return refreshPromise;
}


api.interceptors.response.use(
  (response) => response,

  async (error) => {
    const originalRequest =
      error.config;

    if (!originalRequest) {
      return Promise.reject(error);
    }

    const isUnauthorized =
      error.response?.status === 401;

    const refreshDisabled =
      originalRequest.skipAuthRefresh;

    const wasRetried =
      originalRequest._authRetried;

    if (
      !isUnauthorized ||
      refreshDisabled ||
      wasRetried
    ) {
      return Promise.reject(error);
    }

    originalRequest._authRetried = true;

    try {
      await refreshAccessToken();

      return api(originalRequest);
    } catch (refreshError) {
      setAccessToken(null);

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


export async function loginRequest(
  email,
  password,
) {
  await ensureCsrfCookie();

  const response = await api.post(
    "/auth/login/",
    {
      email: email.trim().toLowerCase(),
      password,
    },
    {
      skipAuthRefresh: true,
    },
  );

  const token = extractAccessToken(
    response.data,
  );

  if (!token) {
    throw new Error(
      "The login response did not contain an access token.",
    );
  }

  setAccessToken(token);

  return response.data;
}


export async function logoutRequest() {
  await ensureCsrfCookie();

  try {
    await api.post(
      "/auth/logout/",
      {},
      {
        skipAuthRefresh: true,
      },
    );
  } finally {
    setAccessToken(null);
  }
}


export default api;