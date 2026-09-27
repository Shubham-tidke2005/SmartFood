import {
  createContext,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import api, {
  loginRequest,
  logoutRequest,
  refreshAccessToken,
  setAccessToken,
} from "../lib/api";


export const AuthContext =
  createContext(null);


export const ROLE_HOME = {
  DONOR: "/donor/dashboard",
  RECEIVER: "/receiver/dashboard",
  VOLUNTEER: "/volunteer/dashboard",
  ADMIN: "/admin/dashboard",
};


function normalizeProfile(data) {
  if (!data) {
    return null;
  }

  const account =
    data.user ||
    data.account ||
    data;

  return {
    ...account,
    profile:
      data.profile ||
      account.profile ||
      null,
  };
}


let initialSessionPromise = null;


async function restoreInitialSession() {
  if (!initialSessionPromise) {
    initialSessionPromise =
      refreshAccessToken()
        .then(async (refreshData) => {
          if (
            refreshData?.user ||
            refreshData?.account
          ) {
            return normalizeProfile(
              refreshData,
            );
          }

          const profileResponse =
            await api.get(
              "/profiles/me/",
            );

          return normalizeProfile(
            profileResponse.data,
          );
        })
        .catch(() => {
          setAccessToken(null);
          return null;
        });
  }

  return initialSessionPromise;
}


export default function AuthProvider({
  children,
}) {
  const [user, setUser] =
    useState(null);

  const [initializing, setInitializing] =
    useState(true);

  const [authError, setAuthError] =
    useState("");


  const loadProfile =
    useCallback(async () => {
      const response = await api.get(
        "/profiles/me/",
      );

      const profile =
        normalizeProfile(
          response.data,
        );

      setUser(profile);

      return profile;
    }, []);


  const login = useCallback(
    async ({ email, password }) => {
      setAuthError("");

      const loginData =
        await loginRequest(
          email,
          password,
        );

      let authenticatedUser =
        normalizeProfile(
          loginData.user
            ? loginData
            : null,
        );

      if (!authenticatedUser) {
        authenticatedUser =
          await loadProfile();
      } else {
        setUser(authenticatedUser);
      }

      return authenticatedUser;
    },
    [loadProfile],
  );


  const logout = useCallback(
    async () => {
      setAuthError("");

      try {
        await logoutRequest();
      } finally {
        setUser(null);
        setAccessToken(null);
        initialSessionPromise = null;
      }
    },
    [],
  );


  const updateProfile =
    useCallback(async (payload) => {
      const response = await api.patch(
        "/profiles/me/",
        payload,
      );

      const updatedUser =
        normalizeProfile(
          response.data,
        );

      setUser(updatedUser);

      return updatedUser;
    }, []);


  useEffect(() => {
    let active = true;

    restoreInitialSession()
      .then((restoredUser) => {
        if (active) {
          setUser(restoredUser);
        }
      })
      .finally(() => {
        if (active) {
          setInitializing(false);
        }
      });

    return () => {
      active = false;
    };
  }, []);


  useEffect(() => {
    function handleSessionExpired() {
      setUser(null);
      setAccessToken(null);

      if (
        window.location.pathname !==
        "/login"
      ) {
        window.location.assign(
          "/login?reason=session-expired",
        );
      }
    }

    window.addEventListener(
      "smartfood:session-expired",
      handleSessionExpired,
    );

    return () => {
      window.removeEventListener(
        "smartfood:session-expired",
        handleSessionExpired,
      );
    };
  }, []);


  const value = useMemo(
    () => ({
      user,
      initializing,
      authError,
      isAuthenticated: Boolean(user),
      login,
      logout,
      loadProfile,
      updateProfile,
      setAuthError,
    }),
    [
      user,
      initializing,
      authError,
      login,
      logout,
      loadProfile,
      updateProfile,
    ],
  );


  return (
    <AuthContext.Provider
      value={value}
    >
      {children}
    </AuthContext.Provider>
  );
}

export {
  default as useAuth,
} from "./useAuth";
