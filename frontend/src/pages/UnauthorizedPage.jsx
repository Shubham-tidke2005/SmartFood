import {
  ShieldX,
} from "lucide-react";

import { Link } from "react-router-dom";

export default function UnauthorizedPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50 p-5 dark:bg-slate-900">
      <section className="w-full max-w-lg rounded-3xl border border-slate-200 bg-white p-8 text-center shadow-xl dark:border-slate-700 dark:bg-slate-800">
        <div className="mx-auto flex size-14 items-center justify-center rounded-2xl bg-red-100 text-red-600 dark:bg-red-950/50 dark:text-red-300">
          <ShieldX
            aria-hidden="true"
            className="size-7"
          />
        </div>

        <h1 className="mt-5 text-3xl font-black text-slate-950 dark:text-white">
          Access not allowed
        </h1>

        <p className="mt-3 leading-7 text-slate-600 dark:text-slate-300">
          Your SmartFood role does not have permission to
          access this page.
        </p>

        <Link
          to="/dashboard"
          className="focus-ring mt-6 inline-flex min-h-11 items-center justify-center rounded-xl bg-blue-600 px-5 py-2.5 font-bold text-white transition hover:bg-blue-700 active:scale-[0.98]"
        >
          Return to dashboard
        </Link>
      </section>
    </main>
  );
}