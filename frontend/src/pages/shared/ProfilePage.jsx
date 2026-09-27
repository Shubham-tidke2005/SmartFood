import {
  useEffect,
  useState,
} from "react";

import {
  BadgeCheck,
  LoaderCircle,
  Mail,
  Phone,
  Save,
  ShieldCheck,
  UserRound,
} from "lucide-react";

import useAuth from "../../auth/useAuth";

import {
  getApiErrorMessage,
} from "../../lib/apiError";


const STATUS_STYLE = {
  VERIFIED:
    "border-emerald-200 bg-emerald-50 text-emerald-700",
  PENDING:
    "border-amber-200 bg-amber-50 text-amber-700",
  REJECTED:
    "border-red-200 bg-red-50 text-red-700",
  SUSPENDED:
    "border-red-200 bg-red-50 text-red-700",
};


export default function ProfilePage() {
  const {
    user,
    loadProfile,
    updateProfile,
  } = useAuth();

  const [form, setForm] =
    useState({
      display_name: "",
      mobile: "",
    });

  const [loading, setLoading] =
    useState(!user);

  const [saving, setSaving] =
    useState(false);

  const [error, setError] =
    useState("");

  const [success, setSuccess] =
    useState("");


  useEffect(() => {
    let active = true;

    async function initialize() {
      try {
        const profile =
          user || await loadProfile();

        if (!active) {
          return;
        }

        setForm({
          display_name:
            profile?.display_name || "",
          mobile:
            profile?.mobile || "",
        });
      } catch (requestError) {
        if (active) {
          setError(
            getApiErrorMessage(
              requestError,
              "Unable to load your profile.",
            ),
          );
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    initialize();

    return () => {
      active = false;
    };
  }, [user, loadProfile]);


  function handleChange(event) {
    const {
      name,
      value,
    } = event.target;

    setForm((current) => ({
      ...current,
      [name]: value,
    }));

    setError("");
    setSuccess("");
  }


  async function handleSubmit(event) {
    event.preventDefault();

    if (!form.display_name.trim()) {
      setError(
        "Display name is required.",
      );
      return;
    }

    setSaving(true);
    setError("");
    setSuccess("");

    try {
      await updateProfile({
        display_name:
          form.display_name.trim(),
        mobile:
          form.mobile.trim(),
      });

      setSuccess(
        "Profile updated successfully.",
      );
    } catch (requestError) {
      setError(
        getApiErrorMessage(
          requestError,
          "Unable to update your profile.",
        ),
      );
    } finally {
      setSaving(false);
    }
  }


  if (loading) {
    return (
      <div
        className="flex min-h-72 items-center justify-center"
        role="status"
      >
        <LoaderCircle className="h-9 w-9 animate-spin text-blue-600" />
      </div>
    );
  }


  const status =
    user?.verification_status ||
    "PENDING";


  return (
    <div className="mx-auto max-w-5xl">
      <header className="mb-7">
        <p className="text-sm font-semibold uppercase tracking-[0.18em] text-blue-600">
          Account
        </p>

        <h1 className="mt-2 text-3xl font-bold text-slate-900 dark:text-white">
          My profile
        </h1>

        <p className="mt-2 text-slate-500 dark:text-slate-400">
          Manage your SmartFood account information.
        </p>
      </header>

      <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
        <form
          onSubmit={handleSubmit}
          className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm dark:border-slate-700/60 dark:bg-slate-800"
        >
          <div className="flex items-center gap-3 border-b border-slate-200 pb-5 dark:border-slate-700">
            <span className="grid h-11 w-11 place-items-center rounded-xl bg-blue-50 text-blue-600 dark:bg-blue-950/40">
              <UserRound className="h-6 w-6" />
            </span>

            <div>
              <h2 className="font-semibold text-slate-900 dark:text-white">
                Personal information
              </h2>

              <p className="text-sm text-slate-500 dark:text-slate-400">
                Information visible to authorized participants.
              </p>
            </div>
          </div>

          {error && (
            <div
              className="mt-5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
              role="alert"
            >
              {error}
            </div>
          )}

          {success && (
            <div
              className="mt-5 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700"
              role="status"
            >
              {success}
            </div>
          )}

          <div className="mt-6 grid gap-5 sm:grid-cols-2">
            <div className="sm:col-span-2">
              <label
                htmlFor="display_name"
                className="mb-2 block text-sm font-medium text-slate-700 dark:text-slate-200"
              >
                Display name
              </label>

              <input
                id="display_name"
                name="display_name"
                value={form.display_name}
                onChange={handleChange}
                className="min-h-12 w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 dark:border-slate-600 dark:bg-slate-900 dark:text-white"
                disabled={saving}
                required
              />
            </div>

            <div>
              <label
                htmlFor="email"
                className="mb-2 block text-sm font-medium text-slate-700 dark:text-slate-200"
              >
                Email address
              </label>

              <div className="relative">
                <Mail className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400" />

                <input
                  id="email"
                  value={user?.email || ""}
                  className="min-h-12 w-full rounded-xl border border-slate-200 bg-slate-100 py-3 pl-11 pr-4 text-slate-500 dark:border-slate-700 dark:bg-slate-900/60"
                  readOnly
                />
              </div>
            </div>

            <div>
              <label
                htmlFor="mobile"
                className="mb-2 block text-sm font-medium text-slate-700 dark:text-slate-200"
              >
                Mobile number
              </label>

              <div className="relative">
                <Phone className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400" />

                <input
                  id="mobile"
                  name="mobile"
                  type="tel"
                  value={form.mobile}
                  onChange={handleChange}
                  className="min-h-12 w-full rounded-xl border border-slate-300 bg-white py-3 pl-11 pr-4 text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 dark:border-slate-600 dark:bg-slate-900 dark:text-white"
                  disabled={saving}
                />
              </div>
            </div>
          </div>

          <div className="mt-7 flex justify-end">
            <button
              type="submit"
              disabled={saving}
              className="inline-flex min-h-11 items-center justify-center gap-2 rounded-xl bg-blue-600 px-5 py-2.5 font-semibold text-white transition hover:bg-blue-700 active:scale-[0.98] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 disabled:opacity-60"
            >
              {saving ? (
                <LoaderCircle className="h-5 w-5 animate-spin" />
              ) : (
                <Save className="h-5 w-5" />
              )}

              {saving
                ? "Saving…"
                : "Save changes"}
            </button>
          </div>
        </form>

        <aside className="space-y-5">
          <section className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm dark:border-slate-700/60 dark:bg-slate-800">
            <ShieldCheck className="h-7 w-7 text-blue-600" />

            <h2 className="mt-4 font-semibold text-slate-900 dark:text-white">
              Account status
            </h2>

            <dl className="mt-5 space-y-4 text-sm">
              <div>
                <dt className="text-slate-500">
                  Role
                </dt>

                <dd className="mt-1 font-semibold text-slate-900 dark:text-white">
                  {user?.role || "Unknown"}
                </dd>
              </div>

              <div>
                <dt className="text-slate-500">
                  Verification
                </dt>

                <dd className="mt-2">
                  <span
                    className={
                      "inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-semibold " +
                      (
                        STATUS_STYLE[status] ||
                        STATUS_STYLE.PENDING
                      )
                    }
                  >
                    <BadgeCheck className="h-4 w-4" />

                    {status}
                  </span>
                </dd>
              </div>

              <div>
                <dt className="text-slate-500">
                  Contact
                </dt>

                <dd className="mt-1 font-semibold text-slate-900 dark:text-white">
                  {user?.contact_verified_at
                    ? "Verified"
                    : "Not verified"}
                </dd>
              </div>
            </dl>
          </section>
        </aside>
      </div>
    </div>
  );
}