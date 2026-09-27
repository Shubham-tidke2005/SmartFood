import {
  Navigate,
  Outlet,
  useLocation,
} from "react-router-dom";

import useAuth from "./useAuth";


export default function ProtectedRoute({
  children,
}) {
  const {
    user,
    initializing,
  } = useAuth();

  const location = useLocation();


  if (initializing) {
    return (
      <div
        className="flex min-h-screen items-center justify-center bg-slate-50 dark:bg-slate-900"
        role="status"
        aria-live="polite"
      >
        <div className="text-center">
          <div className="mx-auto h-10 w-10 animate-spin rounded-full border-4 border-blue-100 border-t-blue-600" />

          <p className="mt-4 text-sm font-medium text-slate-600 dark:text-slate-300">
            Restoring your session…
          </p>
        </div>
      </div>
    );
  }


  if (!user) {
    return (
      <Navigate
        to="/login"
        replace
        state={{
          from: location,
        }}
      />
    );
  }


  return children || <Outlet />;
}