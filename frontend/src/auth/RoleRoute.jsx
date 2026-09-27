import {
  Navigate,
  Outlet,
} from "react-router-dom";

import useAuth from "./useAuth";


export default function RoleRoute({
  roles,
  allowedRoles,
  children,
}) {
  const {
    user,
    initializing,
  } = useAuth();


  if (initializing) {
    return (
      <div
        className="flex min-h-72 items-center justify-center"
        role="status"
      >
        <div className="h-9 w-9 animate-spin rounded-full border-4 border-blue-100 border-t-blue-600" />
      </div>
    );
  }


  if (!user) {
    return (
      <Navigate
        to="/login"
        replace
      />
    );
  }


  const acceptedRoles =
    allowedRoles ||
    roles ||
    [];


  if (
    acceptedRoles.length > 0 &&
    !acceptedRoles.includes(user.role)
  ) {
    return (
      <Navigate
        to="/unauthorized"
        replace
      />
    );
  }


  return children || <Outlet />;
}