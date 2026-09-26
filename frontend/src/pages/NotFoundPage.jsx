import {
  MapPinOff,
} from "lucide-react";

import { Link } from "react-router-dom";

export default function NotFoundPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50 p-5 dark:bg-slate-900">
      <section className="w-full max-w-lg text-center">
        <div className="mx-auto flex size-16 items-center justify-center rounded-3xl bg-blue-100 text-blue-600 dark:bg-blue-950/50 dark:text-blue-300">
          <MapPinOff
            aria-hidden="true"
            className="size-8"
          />
        </div>

        <p className="mt-6 text-sm font-black uppercase tracking-[0.2em] text-blue-600">
          Error 404
        </p>

        <h1 className="mt-3 text-4xl font-black text-slate-950 dark:text-white">
          Page not found
        </h1>

        <p className="mt-3 text-slate-600 dark:text-slate-300">
          The SmartFood page you requested does not exist.
        </p>

        <Link
          to="/dashboard"
          className="focus-ring mt-7 inline-flex min-h-11 items-center justify-center rounded-xl bg-blue-600 px-5 py-2.5 font-bold text-white hover:bg-blue-700"
        >
          Go to dashboard
        </Link>
      </section>
    </main>
  );
}