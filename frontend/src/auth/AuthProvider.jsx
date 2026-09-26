import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

import api, {
  refreshAccessToken,
} from "../lib/api";

import {
  clearAccessToken,
  setAccessToken,
} from "./tokenStore";

const AuthContext = createContext(null);

function normalizeUser(data) {
  return data?.user || data?.profile || data || null;
}

function extractAccessToken(data) {
  return (
    data?.access ||
    data?.access_token ||
    data?.tokens?.access ||
    null
  );
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [isInitializing, setIsInitializing] =
    useState(true);

  const loadCurrentUser = useCallback(async () => {
    const response = await api.get("/profiles/me/");
    const currentUser = normalizeUser(response.data);

    setUser(currentUser);

    return currentUser;
  }, []);

  const login = useCallback(
    async (credentials) => {
      const response = await api.post(
        "/auth/login/",
        credentials,
      );

      const accessToken = extractAccessToken(
        response.data,
      );

      if (!accessToken) {
        throw new Error(
          "Login succeeded but no access token was returned.",
        );
      }

      setAccessToken(accessToken);

      const returnedUser = normalizeUser(
        response.data?.user,
      );

      if (returnedUser) {
        setUser(returnedUser);
        return returnedUser;
      }

      return loadCurrentUser();
    },
    [loadCurrentUser],
  );

  const logout = useCallback(async () => {
    try {
      await api.post("/auth/logout/", {});
    } finally {
      clearAccessToken();
      setUser(null);
    }
  }, []);

  useEffect(() => {
    let active = true;

    async function initializeAuthentication() {
      try {
        await refreshAccessToken();

        if (active) {
          await loadCurrentUser();
        }
      } catch {
        clearAccessToken();

        if (active) {
          setUser(null);
        }
      } finally {
        if (active) {
          setIsInitializing(false);
        }
      }
    }

    initializeAuthentication();

    return () => {
      active = false;
    };
  }, [loadCurrentUser]);

  useEffect(() => {
    function handleSessionExpired() {
      clearAccessToken();
      setUser(null);
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
      isAuthenticated: Boolean(user),
      isInitializing,
      login,
      logout,
      refreshUser: loadCurrentUser,
    }),
    [
      user,
      isInitializing,
      login,
      logout,
      loadCurrentUser,
    ],
  );

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error(
      "useAuth must be used inside AuthProvider.",
    );
  }

  return context;
}