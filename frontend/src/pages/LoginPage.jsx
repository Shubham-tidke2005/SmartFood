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
  Link,
  Navigate,
  useLocation,
  useNavigate,
} from "react-router-dom";

import { motion } from "motion/react";

import { useAuth } from "../auth/AuthProvider";
import Button from "../components/ui/Button";
import {
  ErrorMessage,
} from "../components/ui/FeedbackStates";
import {
  Input,
} from "../components/ui/FormControls";
import LoadingState from "../components/ui/LoadingState";
import {
  getApiErrorMessage,
} from "../lib/apiError";


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

  const [error, setError] =
    useState("");

  const [isSubmitting, setIsSubmitting] =
    useState(false);

  const destination =
    location.state?.from ||
    "/dashboard";


  useEffect(() => {
    setError("");
  }, [
    form.email,
    form.password,
  ]);


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
    const {
      name,
      value,
    } = event.target;

    setForm((current) => ({
      ...current,
      [name]: value,
    }));
  }


  async function handleSubmit(event) {
    event.preventDefault();

    const email =
      form.email.trim();

    if (!email || !form.password) {
      setError(
        "Enter both your email address and password.",
      );

      return;
    }

    setIsSubmitting(true);
    setError("");

    try {
      await login({
        email,
        password: form.password,
      });

      navigate(destination, {
        replace: true,
      });
    } catch (requestError) {
      setError(
        getApiErrorMessage(
          requestError,
          "Unable to sign in. Check your email and password.",
        ),
      );
    } finally {
      setIsSubmitting(false);
    }
  }


  return (
    <main className="grid min-h-screen bg-slate-50 dark:bg-slate-900 lg:grid-cols-2">
      <section className="relative hidden overflow-hidden bg-slate-950 p-12 text-white lg:flex lg:flex-col lg:justify-between">
        <div
          aria-hidden="true"
          className="absolute -left-32 top-20 size-96 rounded-full bg-blue-600/25 blur-3xl"
        />

        <div
          aria-hidden="true"
          className="absolute -right-32 bottom-12 size-96 rounded-full bg-sky-500/20 blur-3xl"
        />

        <div className="relative flex items-center gap-3">
          <div className="flex size-12 items-center justify-center rounded-2xl bg-blue-600 text-xl font-black shadow-lg shadow-blue-600/20">
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
            secure and transparent platform.
          </p>

          <div className="mt-8 grid grid-cols-3 gap-3">
            <FeatureCard
              number="01"
              title="List food"
            />

            <FeatureCard
              number="02"
              title="Find matches"
            />

            <FeatureCard
              number="03"
              title="Deliver impact"
            />
          </div>
        </div>

        <p className="relative text-sm font-medium text-slate-400">
          List → Match → Collect → Deliver → Verify
        </p>
      </section>


      <section className="relative flex items-center justify-center overflow-hidden p-5 sm:p-8">
        <div
          aria-hidden="true"
          className="absolute right-0 top-0 size-72 rounded-full bg-blue-200/30 blur-3xl dark:bg-blue-900/20"
        />

        <motion.div
          className="relative w-full max-w-md"
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
              <div className="flex size-11 items-center justify-center rounded-2xl bg-blue-600 text-lg font-black text-white shadow-lg shadow-blue-600/20">
                S
              </div>

              <div>
                <p className="text-xl font-black text-slate-950 dark:text-white">
                  SmartFood
                </p>

                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Better redistribution
                </p>
              </div>
            </div>
          </div>


          <div className="rounded-3xl border border-slate-200/80 bg-white p-6 shadow-xl shadow-slate-200/40 dark:border-slate-700/60 dark:bg-slate-800 dark:shadow-none sm:p-8">
            <div>
              <p className="text-sm font-bold uppercase tracking-wider text-blue-600 dark:text-blue-400">
                Account access
              </p>

              <h1 className="mt-2 text-3xl font-black tracking-tight text-slate-950 dark:text-white">
                Welcome back
              </h1>

              <p className="mt-2 leading-6 text-slate-500 dark:text-slate-400">
                Sign in to continue to your SmartFood
                dashboard.
              </p>
            </div>


            {error && (
              <div className="mt-6">
                <ErrorMessage
                  message={error}
                />
              </div>
            )}


            <form
              className="mt-7 space-y-5"
              onSubmit={handleSubmit}
              noValidate
            >
              <div>
                <Input
                  label="Email address"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={form.email}
                  inputClassName="pl-11"
                  placeholder="you@example.com"
                  disabled={isSubmitting}
                  onChange={updateField}
                />

                <Mail
                  aria-hidden="true"
                  className="pointer-events-none absolute left-[2.4rem] top-[17.3rem] size-4 text-slate-400 sm:left-[3.4rem]"
                />
              </div>


              <div>
                <Input
                  label="Password"
                  name="password"
                  type="password"
                  autoComplete="current-password"
                  required
                  value={form.password}
                  inputClassName="pl-11"
                  placeholder="Enter your password"
                  disabled={isSubmitting}
                  onChange={updateField}
                />

                <LockKeyhole
                  aria-hidden="true"
                  className="pointer-events-none absolute left-[2.4rem] top-[23.6rem] size-4 text-slate-400 sm:left-[3.4rem]"
                />
              </div>


              <div className="flex justify-end">
                <Link
                  to="/password-reset"
                  className="focus-ring rounded-md text-sm font-semibold text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
                >
                  Forgot your password?
                </Link>
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


            <div className="mt-7 border-t border-slate-200 pt-6 text-center dark:border-slate-700">
              <p className="text-sm text-slate-500 dark:text-slate-400">
                New to SmartFood?{" "}

                <Link
                  to="/register"
                  className="focus-ring rounded-md font-bold text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
                >
                  Create an account
                </Link>
              </p>
            </div>
          </div>


          <p className="mt-6 text-center text-xs leading-5 text-slate-500 dark:text-slate-400">
            By signing in, you agree to use SmartFood
            responsibly and provide accurate information.
          </p>
        </motion.div>
      </section>
    </main>
  );
}


function FeatureCard({
  number,
  title,
}) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 p-4 backdrop-blur-sm">
      <p className="text-xs font-black text-sky-400">
        {number}
      </p>

      <p className="mt-2 text-sm font-bold text-white">
        {title}
      </p>
    </div>
  );
}