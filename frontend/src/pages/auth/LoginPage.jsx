import {
  useEffect,
  useState,
} from "react";

import {
  Eye,
  EyeOff,
  Leaf,
  LoaderCircle,
  LockKeyhole,
  Mail,
} from "lucide-react";

import {
  Link,
  Navigate,
  useLocation,
  useNavigate,
} from "react-router-dom";

import {
  ROLE_HOME,
} from "../../auth/AuthProvider";

import useAuth from "../auth/useAuth";

import {
  getApiErrorMessage,
} from "../../lib/apiError";

export default function LoginPage() {
  const {
    user,
    initializing,
    login,
  } = useAuth();

  const navigate = useNavigate();
  const location = useLocation();

  const [form, setForm] =
    useState({
      email: "",
      password: "",
    });

  const [showPassword, setShowPassword] =
    useState(false);

  const [submitting, setSubmitting] =
    useState(false);

  const [error, setError] =
    useState("");


  useEffect(() => {
    const params =
      new URLSearchParams(
        location.search,
      );

    if (
      params.get("reason") ===
      "session-expired"
    ) {
      setError(
        "Your session expired. Please sign in again.",
      );
    }
  }, [location.search]);


  if (initializing) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50 dark:bg-slate-900">
        <LoaderCircle
          className="h-9 w-9 animate-spin text-blue-600"
          aria-label="Loading"
        />
      </div>
    );
  }


  if (user) {
    return (
      <Navigate
        to={
          ROLE_HOME[user.role] ||
          "/profile"
        }
        replace
      />
    );
  }


  function handleChange(event) {
    const {
      name,
      value,
    } = event.target;

    setForm((current) => ({
      ...current,
      [name]: value,
    }));

    if (error) {
      setError("");
    }
  }


  async function handleSubmit(event) {
    event.preventDefault();

    if (!form.email.trim()) {
      setError(
        "Enter your email address.",
      );
      return;
    }

    if (!form.password) {
      setError(
        "Enter your password.",
      );
      return;
    }

    setSubmitting(true);
    setError("");

    try {
      const authenticatedUser =
        await login(form);

      const attemptedPath =
        location.state?.from?.pathname;

      const homePath =
        ROLE_HOME[
          authenticatedUser.role
        ] || "/profile";

      navigate(
        attemptedPath || homePath,
        {
          replace: true,
        },
      );
    } catch (requestError) {
      setError(
        getApiErrorMessage(
          requestError,
          "Unable to sign in. Check your email and password.",
        ),
      );
    } finally {
      setSubmitting(false);
    }
  }


  return (
    <main className="min-h-screen bg-slate-50 px-4 py-8 dark:bg-slate-900 sm:px-6 lg:grid lg:grid-cols-2 lg:px-0 lg:py-0">
      <section className="hidden bg-gradient-to-br from-blue-700 via-blue-600 to-sky-500 p-12 text-white lg:flex lg:flex-col lg:justify-between">
        <Link
          to="/"
          className="inline-flex items-center gap-3 text-xl font-bold"
        >
          <span className="grid h-11 w-11 place-items-center rounded-2xl bg-white/15 backdrop-blur">
            <Leaf className="h-6 w-6" />
          </span>

          SmartFood
        </Link>

        <div className="max-w-xl">
          <p className="text-sm font-semibold uppercase tracking-[0.22em] text-blue-100">
            Food redistribution
          </p>

          <h1 className="mt-4 text-5xl font-bold leading-tight">
            Help surplus food reach the right people.
          </h1>

          <p className="mt-6 text-lg leading-8 text-blue-100">
            Coordinate donors, receivers and volunteers through one secure platform.
          </p>
        </div>

        <p className="text-sm text-blue-100">
          List · Match · Collect · Deliver · Measure
        </p>
      </section>

      <section className="flex items-center justify-center">
        <div className="w-full max-w-md">
          <Link
            to="/"
            className="mb-8 inline-flex items-center gap-3 text-xl font-bold text-slate-900 dark:text-white lg:hidden"
          >
            <span className="grid h-10 w-10 place-items-center rounded-xl bg-blue-600 text-white">
              <Leaf className="h-5 w-5" />
            </span>

            SmartFood
          </Link>

          <div className="rounded-3xl border border-slate-200/80 bg-white p-6 shadow-xl shadow-blue-500/5 dark:border-slate-700/60 dark:bg-slate-800 sm:p-8">
            <p className="text-sm font-semibold text-blue-600">
              Welcome back
            </p>

            <h2 className="mt-2 text-3xl font-bold text-slate-900 dark:text-white">
              Sign in
            </h2>

            <p className="mt-2 text-sm leading-6 text-slate-500 dark:text-slate-400">
              Sign in to continue to your role-specific dashboard.
            </p>

            {error && (
              <div
                className="mt-6 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900/60 dark:bg-red-950/30 dark:text-red-300"
                role="alert"
              >
                {error}
              </div>
            )}

            <form
              className="mt-7 space-y-5"
              onSubmit={handleSubmit}
              noValidate
            >
              <div>
                <label
                  htmlFor="email"
                  className="mb-2 block text-sm font-medium text-slate-700 dark:text-slate-200"
                >
                  Email address
                </label>

                <div className="relative">
                  <Mail className="pointer-events-none absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400" />

                  <input
                    id="email"
                    name="email"
                    type="email"
                    autoComplete="email"
                    value={form.email}
                    onChange={handleChange}
                    className="min-h-12 w-full rounded-xl border border-slate-300 bg-white py-3 pl-11 pr-4 text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 dark:border-slate-600 dark:bg-slate-900 dark:text-white"
                    placeholder="name@example.com"
                    disabled={submitting}
                    required
                  />
                </div>
              </div>

              <div>
                <label
                  htmlFor="password"
                  className="mb-2 block text-sm font-medium text-slate-700 dark:text-slate-200"
                >
                  Password
                </label>

                <div className="relative">
                  <LockKeyhole className="pointer-events-none absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400" />

                  <input
                    id="password"
                    name="password"
                    type={
                      showPassword
                        ? "text"
                        : "password"
                    }
                    autoComplete="current-password"
                    value={form.password}
                    onChange={handleChange}
                    className="min-h-12 w-full rounded-xl border border-slate-300 bg-white py-3 pl-11 pr-12 text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 dark:border-slate-600 dark:bg-slate-900 dark:text-white"
                    placeholder="Enter your password"
                    disabled={submitting}
                    required
                  />

                  <button
                    type="button"
                    onClick={() =>
                      setShowPassword(
                        (current) =>
                          !current,
                      )
                    }
                    className="absolute right-2 top-1/2 grid h-10 w-10 -translate-y-1/2 place-items-center rounded-lg text-slate-500 hover:bg-slate-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 dark:hover:bg-slate-700"
                    aria-label={
                      showPassword
                        ? "Hide password"
                        : "Show password"
                    }
                  >
                    {showPassword ? (
                      <EyeOff className="h-5 w-5" />
                    ) : (
                      <Eye className="h-5 w-5" />
                    )}
                  </button>
                </div>
              </div>

              <div className="flex justify-end">
                <Link
                  to="/password-reset"
                  className="text-sm font-semibold text-blue-600 hover:text-blue-700"
                >
                  Forgot password?
                </Link>
              </div>

              <button
                type="submit"
                disabled={submitting}
                className="inline-flex min-h-12 w-full items-center justify-center gap-2 rounded-xl bg-blue-600 px-5 py-3 font-semibold text-white transition hover:bg-blue-700 active:scale-[0.98] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {submitting && (
                  <LoaderCircle className="h-5 w-5 animate-spin" />
                )}

                {submitting
                  ? "Signing in…"
                  : "Sign in"}
              </button>
            </form>

            <p className="mt-7 text-center text-sm text-slate-500 dark:text-slate-400">
              Need an account?{" "}
              <Link
                to="/register"
                className="font-semibold text-blue-600 hover:text-blue-700"
              >
                Register
              </Link>
            </p>
          </div>
        </div>
      </section>
    </main>
  );
}