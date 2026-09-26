import {
  Navigate,
  Outlet,
  useLocation,
} from "react-router-dom";

import LoadingState from "../components/ui/LoadingState";
import { useAuth } from "./AuthProvider";

export default function ProtectedRoute() {
  const {
    isAuthenticated,
    isInitializing,
  } = useAuth();

  const location = useLocation();

  if (isInitializing) {
    return (
      <LoadingState
        fullScreen
        message="Restoring your SmartFood session..."
      />
    );
  }

  if (!isAuthenticated) {
    return (
      <Navigate
        to="/login"
        replace
        state={{
          from:
            location.pathname +
            location.search,
        }}
      />
    );
  }

  return <Outlet />;
}