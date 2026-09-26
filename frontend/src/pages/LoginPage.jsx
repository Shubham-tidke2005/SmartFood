import {
  ArrowRight,
  HeartHandshake,
  LockKeyhole,
  Mail,
} from "lucide-react";

import {
  useEffect,
  useState,
} from "react";

import {
  Navigate,
  useLocation,
  useNavigate,
} from "react-router-dom";

import { motion } from "motion/react";

import { useAuth } from "../auth/AuthProvider";
import Button from "../components/ui/Button";
import { ErrorMessage } from "../components/ui/FeedbackStates";
import { Input } from "../components/ui/FormControls";
import LoadingState from "../components/ui/LoadingState";
import { getApiErrorMessage } from "../lib/apiError";

export default function LoginPage() {
  const {
    login,
    isAuthenticated,
    isInitializing,
  } = useAuth();

  const location = useLocation();
  const navigate = useNavigate();

  const [form, setForm] = useState({
    email: "",
    password: "",
  });

  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] =
    useState(false);

  const destination =
    location.state?.from || "/dashboard";

  useEffect(() => {
    setError("");
  }, [form.email, form.password]);

  if (isInitializing) {
    return (
      <LoadingState
        fullScreen
        message="Checking your session..."
      />
    );
  }

  if (isAuthenticated) {
    return (
      <Navigate
        to="/dashboard"
        replace
      />
    );
  }

  function updateField(event) {
    const { name, value } = event.target;

    setForm((current) => ({
      ...current,
      [name]: value,
    }));
  }

  async function handleSubmit(event) {
    event.preventDefault();

    if (!form.email.trim() || !form.password) {
      setError(
        "Enter both your email address and password.",
      );

      return;
    }

    setIsSubmitting(true);
    setError("");

    try {
      await login({
        email: form.email.trim(),
        password: form.password,
      });

      navigate(destination, {
        replace: true,
      });
    } catch (requestError) {
      setError(
        getApiErrorMessage(
          requestError,
          "Unable to sign in. Check your credentials.",
        ),
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="grid min-h-screen bg-slate-50 dark:bg-slate-900 lg:grid-cols-2">
      <section className="relative hidden overflow-hidden bg-slate-950 p-12 text-white lg:flex lg:flex-col lg:justify-between">
        <div className="absolute -left-32 top-20 size-96 rounded-full bg-blue-600/25 blur-3xl" />
        <div className="absolute -right-32 bottom-12 size-96 rounded-full bg-sky-500/20 blur-3xl" />

        <div className="relative flex items-center gap-3">
          <div className="flex size-12 items-center justify-center rounded-2xl bg-blue-600 text-xl font-black">
            S
          </div>

          <div>
            <p className="text-xl font-black">
              SmartFood
            </p>

            <p className="text-sm text-slate-400">
              Food redistribution platform
            </p>
          </div>
        </div>

        <div className="relative max-w-xl">
          <HeartHandshake
            aria-hidden="true"
            className="mb-8 size-14 text-sky-400"
          />

          <h1 className="text-5xl font-black leading-tight tracking-tight">
            Help surplus food reach the right people.
          </h1>

          <p className="mt-6 text-lg leading-8 text-slate-300">
            Coordinate donors, verified receivers,
            volunteers and administrators through one
            transparent platform.
          </p>
        </div>

        <p className="relative text-sm text-slate-400">
          List → Match → Collect → Deliver → Verify
        </p>
      </section>

      <section className="flex items-center justify-center p-5 sm:p-8">
        <motion.div
          className="w-full max-w-md"
          initial={{
            opacity: 0,
            y: 18,
          }}
          animate={{
            opacity: 1,
            y: 0,
          }}
          transition={{
            duration: 0.3,
          }}
        >
          <div className="mb-8 lg:hidden">
            <div className="flex items-center gap-3">
              <div className="flex size-11 items-center justify-center rounded-2xl bg-blue-600 text-lg font-black text-white">
                S
              </div>

              <p className="text-xl font-black text-slate-950 dark:text-white">
                SmartFood
              </p>
            </div>
          </div>

          <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-xl shadow-slate-200/40 dark:border-slate-700 dark:bg-slate-800 dark:shadow-none sm:p-8">
            <h1 className="text-3xl font-black tracking-tight text-slate-950 dark:text-white">
              Welcome back
            </h1>

            <p className="mt-2 text-slate-500 dark:text-slate-400">
              Sign in to continue to your dashboard.
            </p>

            {error && (
              <div className="mt-6">
                <ErrorMessage message={error} />
              </div>
            )}

            <form
              className="mt-7 space-y-5"
              onSubmit={handleSubmit}
              noValidate
            >
              <div className="relative">
                <Mail
                  aria-hidden="true"
                  className="pointer-events-none absolute left-3.5 top-[2.7rem] z-10 size-4 text-slate-400"
                />

                <Input
                  label="Email address"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={form.email}
                  inputClassName="pl-10"
                  placeholder="you@example.com"
                  onChange={updateField}
                />
              </div>

              <div className="relative">
                <LockKeyhole
                  aria-hidden="true"
                  className="pointer-events-none absolute left-3.5 top-[2.7rem] z-10 size-4 text-slate-400"
                />

                <Input
                  label="Password"
                  name="password"
                  type="password"
                  autoComplete="current-password"
                  required
                  value={form.password}
                  inputClassName="pl-10"
                  placeholder="Enter your password"
                  onChange={updateField}
                />
              </div>

              <Button
                type="submit"
                size="lg"
                className="w-full"
                isLoading={isSubmitting}
              >
                Sign in

                <ArrowRight
                  aria-hidden="true"
                  className="size-4"
                />
              </Button>
            </form>

            <p className="mt-6 text-center text-sm text-slate-500 dark:text-slate-400">
              Contact an administrator if you cannot
              access your approved account.
            </p>
          </div>
        </motion.div>
      </section>
    </main>
  );
}