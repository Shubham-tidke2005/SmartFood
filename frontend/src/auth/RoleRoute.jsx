import {
  Navigate,
  Outlet,
  useLocation,
} from "react-router-dom";

import { useAuth } from "./AuthProvider";

export default function RoleRoute({
  allowedRoles,
}) {
  const { user } = useAuth();
  const location = useLocation();

  const normalizedRole =
    user?.role?.toUpperCase();

  const permitted = allowedRoles
    .map((role) => role.toUpperCase())
    .includes(normalizedRole);

  if (!permitted) {
    return (
      <Navigate
        to="/unauthorized"
        replace
        state={{
          from: location.pathname,
        }}
      />
    );
  }

  return <Outlet />;
}