import {
  Bell,
  CheckCheck,
  CircleHelp,
} from "lucide-react";

import {
  useEffect,
  useState,
} from "react";

import {
  Link,
  useNavigate,
} from "react-router-dom";

import useAuth from "../../auth/useAuth";
import {
  useApiResource,
} from "../../hooks/useApiResource";

import api from "../../lib/api";
import {
  getApiErrorMessage,
} from "../../lib/apiError";

import Button from "../../components/ui/Button";

import {
  EmptyState,
  ErrorMessage,
} from "../../components/ui/FeedbackStates";

import {
  Input,
  Select,
  Textarea,
} from "../../components/ui/FormControls";

import {
  PageHeader,
  SubmitBar,
  Surface,
} from "../../components/ui/PageElements";

import StatusBadge from "../../components/ui/StatusBadge";

export function RegistrationPage() {
  const navigate = useNavigate();

  const [form, setForm] = useState({
    display_name: "",
    email: "",
    mobile: "",
    role: "DONOR",
    password: "",
    password_confirm: "",
  });

  const [error, setError] =
    useState("");

  const [submitting, setSubmitting] =
    useState(false);

  function updateField(event) {
    const {
      name,
      value,
    } = event.target;

    setForm((current) => ({
      ...current,
      [name]: value,
    }));

    setError("");
  }

  async function handleSubmit(event) {
    event.preventDefault();

    if (
      form.password !==
      form.password_confirm
    ) {
      setError(
        "The passwords do not match.",
      );

      return;
    }

    setSubmitting(true);
    setError("");

    try {
      await api.post(
        "/auth/register/",
        form,
      );

      navigate("/login", {
        replace: true,
        state: {
          registrationSuccess: true,
        },
      });
    } catch (requestError) {
      setError(
        getApiErrorMessage(
          requestError,
        ),
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <PublicFormLayout
      title="Create your SmartFood account"
      description="Register as a donor, receiver or volunteer."
    >
      {error && (
        <div className="mt-5">
          <ErrorMessage
            message={error}
          />
        </div>
      )}

      <form
        className="mt-6 space-y-5"
        onSubmit={handleSubmit}
      >
        <Input
          label="Full name"
          name="display_name"
          required
          value={form.display_name}
          onChange={updateField}
        />

        <Input
          label="Email address"
          name="email"
          type="email"
          required
          value={form.email}
          onChange={updateField}
        />

        <Input
          label="Mobile number"
          name="mobile"
          value={form.mobile}
          onChange={updateField}
        />

        <Select
          label="Role"
          name="role"
          required
          value={form.role}
          onChange={updateField}
        >
          <option value="DONOR">
            Donor
          </option>

          <option value="RECEIVER">
            Receiver
          </option>

          <option value="VOLUNTEER">
            Volunteer
          </option>
        </Select>

        <Input
          label="Password"
          name="password"
          type="password"
          required
          value={form.password}
          onChange={updateField}
        />

        <Input
          label="Confirm password"
          name="password_confirm"
          type="password"
          required
          value={
            form.password_confirm
          }
          onChange={updateField}
        />

        <Button
          type="submit"
          className="w-full"
          isLoading={submitting}
        >
          Register
        </Button>
      </form>

      <p className="mt-5 text-center text-sm text-slate-500 dark:text-slate-400">
        Already registered?{" "}

        <Link
          className="font-bold text-blue-600 dark:text-blue-400"
          to="/login"
        >
          Sign in
        </Link>
      </p>
    </PublicFormLayout>
  );
}

export function PasswordResetPage() {
  const [email, setEmail] =
    useState("");

  const [submitted, setSubmitted] =
    useState(false);

  const [error, setError] =
    useState("");

  const [submitting, setSubmitting] =
    useState(false);

  async function handleSubmit(event) {
    event.preventDefault();

    setSubmitting(true);
    setError("");

    try {
      await api.post(
        "/auth/password-reset/",
        {
          email: email.trim(),
        },
      );

      setSubmitted(true);
    } catch (requestError) {
      setError(
        getApiErrorMessage(
          requestError,
        ),
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <PublicFormLayout
      title="Reset password"
      description="Enter your account email to receive reset instructions."
    >
      {submitted ? (
        <div className="mt-6">
          <EmptyState
            title="Check your email"
            description="If an eligible account exists, SmartFood has sent reset instructions."
          />
        </div>
      ) : (
        <>
          {error && (
            <div className="mt-5">
              <ErrorMessage
                message={error}
              />
            </div>
          )}

          <form
            className="mt-6 space-y-5"
            onSubmit={handleSubmit}
          >
            <Input
              label="Email address"
              type="email"
              required
              value={email}
              onChange={(event) =>
                setEmail(
                  event.target.value,
                )
              }
            />

            <Button
              type="submit"
              className="w-full"
              isLoading={submitting}
            >
              Send reset instructions
            </Button>
          </form>

          <p className="mt-5 text-center text-sm">
            <Link
              to="/login"
              className="font-bold text-blue-600 dark:text-blue-400"
            >
              Return to sign in
            </Link>
          </p>
        </>
      )}
    </PublicFormLayout>
  );
}

export function ProfilePage() {
  const {
    user,
    refreshUser,
  } = useAuth();

  const [form, setForm] = useState({
    display_name: "",
    mobile: "",
  });

  const [message, setMessage] =
    useState("");

  const [error, setError] =
    useState("");

  const [submitting, setSubmitting] =
    useState(false);

  useEffect(() => {
    setForm({
      display_name:
        user?.display_name || "",
      mobile:
        user?.mobile || "",
    });
  }, [
    user?.display_name,
    user?.mobile,
  ]);

  function updateField(event) {
    const {
      name,
      value,
    } = event.target;

    setForm((current) => ({
      ...current,
      [name]: value,
    }));

    setMessage("");
    setError("");
  }

  async function handleSubmit(event) {
    event.preventDefault();

    if (!form.display_name.trim()) {
      setError(
        "Display name is required.",
      );

      return;
    }

    setSubmitting(true);
    setMessage("");
    setError("");

    try {
      await api.patch(
        "/profiles/me/",
        {
          display_name:
            form.display_name.trim(),
          mobile:
            form.mobile.trim(),
        },
      );

      await refreshUser();

      setMessage(
        "Profile updated successfully.",
      );
    } catch (requestError) {
      setError(
        getApiErrorMessage(
          requestError,
        ),
      );
    } finally {
      setSubmitting(false);
    }
  }

  const verificationStatus =
    user?.verification_status ||
    "PENDING";

  const accountStatus =
    user?.is_active === false
      ? "SUSPENDED"
      : "ACTIVE";

  return (
    <div>
      <PageHeader
        title="Profile"
        description="Manage your contact and participant information."
      />

      <Surface className="max-w-2xl">
        {message && (
          <p
            role="status"
            className="mb-5 rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-emerald-700 dark:border-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-300"
          >
            {message}
          </p>
        )}

        {error && (
          <div className="mb-5">
            <ErrorMessage
              message={error}
            />
          </div>
        )}

        <form
          className="space-y-5"
          onSubmit={handleSubmit}
        >
          <Input
            label="Display name"
            name="display_name"
            required
            value={form.display_name}
            onChange={updateField}
          />

          <Input
            label="Email address"
            value={user?.email || ""}
            disabled
          />

          <Input
            label="Mobile number"
            name="mobile"
            value={form.mobile}
            onChange={updateField}
          />

          <Input
            label="Role"
            value={user?.role || ""}
            disabled
          />

          <div className="grid gap-4 border-t border-slate-200 pt-5 dark:border-slate-700 sm:grid-cols-2">
            <div>
              <p className="mb-2 text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                Participant verification
              </p>

              <StatusBadge
                status={
                  verificationStatus
                }
              />
            </div>

            <div>
              <p className="mb-2 text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                Account access
              </p>

              <StatusBadge
                status={accountStatus}
              />
            </div>
          </div>

          {accountStatus ===
            "SUSPENDED" && (
            <p
              role="alert"
              className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm leading-6 text-red-700 dark:border-red-900 dark:bg-red-950/40 dark:text-red-300"
            >
              Your account is suspended.
              Protected operations are
              unavailable. Contact an
              administrator for assistance.
            </p>
          )}

          <SubmitBar
            submitLabel="Save profile"
            isSubmitting={submitting}
          />
        </form>
      </Surface>
    </div>
  );
}

export function NotificationsPage() {
  const {
    data,
    loading,
    error,
    reload,
  } = useApiResource(
    "/notifications/",
    {
      list: true,
    },
  );

  const [processingId, setProcessingId] =
    useState("");

  function isNotificationRead(
    notification,
  ) {
    return Boolean(
      notification.is_read ??
        notification.read_at,
    );
  }

  async function markRead(
    notificationId,
  ) {
    setProcessingId(notificationId);

    try {
      await api.post(
        `/notifications/${notificationId}/read/`,
        {},
      );

      await reload();
    } finally {
      setProcessingId("");
    }
  }

  async function markAllRead() {
    setProcessingId("ALL");

    try {
      await api.post(
        "/notifications/mark-all-read/",
        {},
      );

      await reload();
    } finally {
      setProcessingId("");
    }
  }

  const notifications =
    Array.isArray(data)
      ? data
      : [];

  const unreadCount =
    notifications.filter(
      (notification) =>
        !isNotificationRead(
          notification,
        ),
    ).length;

  return (
    <div>
      <PageHeader
        title="Notifications"
        description="Review donation, transport, verification and account updates."
        action={
          unreadCount > 0 ? (
            <Button
              variant="secondary"
              isLoading={
                processingId === "ALL"
              }
              onClick={markAllRead}
            >
              <CheckCheck
                aria-hidden="true"
                className="size-4"
              />

              Mark all read
            </Button>
          ) : null
        }
      />

      {error && (
        <ErrorMessage
          message={error}
          onRetry={reload}
        />
      )}

      {loading && (
        <p
          role="status"
          className="text-slate-500 dark:text-slate-400"
        >
          Loading notifications...
        </p>
      )}

      {!loading &&
        !error &&
        notifications.length ===
          0 && (
          <EmptyState
            icon={Bell}
            title="No notifications"
            description="Important SmartFood updates will appear here."
          />
        )}

      {!loading &&
        !error &&
        notifications.length >
          0 && (
          <div className="space-y-3">
            {notifications.map(
              (notification) => {
                const read =
                  isNotificationRead(
                    notification,
                  );

                const createdAt =
                  notification.created_at
                    ? new Date(
                        notification.created_at,
                      ).toLocaleString(
                        "en-IN",
                      )
                    : "";

                return (
                  <Surface
                    key={
                      notification.id
                    }
                    className={
                      read
                        ? ""
                        : "border-blue-200 bg-blue-50/50 dark:border-blue-900 dark:bg-blue-950/20"
                    }
                  >
                    <div className="flex items-start gap-4">
                      <div className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-blue-100 text-blue-600 dark:bg-blue-950 dark:text-blue-300">
                        <Bell
                          aria-hidden="true"
                          className="size-5"
                        />
                      </div>

                      <div className="min-w-0 flex-1">
                        <div className="flex flex-wrap items-start justify-between gap-2">
                          <h2 className="font-black text-slate-950 dark:text-white">
                            {notification.title ||
                              "SmartFood update"}
                          </h2>

                          <StatusBadge
                            status={
                              read
                                ? "READ"
                                : "PENDING"
                            }
                          />
                        </div>

                        <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                          {notification.message}
                        </p>

                        {createdAt && (
                          <p className="mt-3 text-xs text-slate-500 dark:text-slate-400">
                            {createdAt}
                          </p>
                        )}

                        {!read && (
                          <Button
                            variant="ghost"
                            size="sm"
                            className="mt-3"
                            isLoading={
                              processingId ===
                              notification.id
                            }
                            disabled={
                              Boolean(
                                processingId,
                              )
                            }
                            onClick={() =>
                              markRead(
                                notification.id,
                              )
                            }
                          >
                            Mark as read
                          </Button>
                        )}
                      </div>
                    </div>
                  </Surface>
                );
              },
            )}
          </div>
        )}
    </div>
  );
}

export function HelpReportingPage() {
  const [form, setForm] = useState({
    complaint_type: "OTHER",
    subject: "",
    description: "",
  });

  const [submitted, setSubmitted] =
    useState(false);

  const [error, setError] =
    useState("");

  const [submitting, setSubmitting] =
    useState(false);

  function updateField(event) {
    const {
      name,
      value,
    } = event.target;

    setForm((current) => ({
      ...current,
      [name]: value,
    }));

    setError("");
    setSubmitted(false);
  }

  async function handleSubmit(event) {
    event.preventDefault();

    if (
      !form.subject.trim() ||
      !form.description.trim()
    ) {
      setError(
        "Subject and problem description are required.",
      );

      return;
    }

    setSubmitting(true);
    setError("");
    setSubmitted(false);

    try {
      await api.post(
        "/complaints/",
        {
          complaint_type:
            form.complaint_type,
          subject:
            form.subject.trim(),
          description:
            form.description.trim(),
        },
      );

      setSubmitted(true);

      setForm({
        complaint_type: "OTHER",
        subject: "",
        description: "",
      });
    } catch (requestError) {
      setError(
        getApiErrorMessage(
          requestError,
        ),
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div>
      <PageHeader
        title="Help and reporting"
        description="Report a donation, participant, transport or platform issue."
      />

      <Surface className="max-w-2xl">
        <div className="mb-6 flex size-12 items-center justify-center rounded-2xl bg-blue-100 text-blue-600 dark:bg-blue-950 dark:text-blue-300">
          <CircleHelp
            aria-hidden="true"
            className="size-6"
          />
        </div>

        {submitted && (
          <p
            role="status"
            className="mb-5 rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-emerald-700 dark:border-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-300"
          >
            Your report was submitted
            successfully.
          </p>
        )}

        {error && (
          <div className="mb-5">
            <ErrorMessage
              message={error}
            />
          </div>
        )}

        <form
          className="space-y-5"
          onSubmit={handleSubmit}
        >
          <Select
            label="Problem type"
            name="complaint_type"
            value={
              form.complaint_type
            }
            onChange={updateField}
          >
            <option value="DONATION">
              Donation
            </option>

            <option value="TRANSPORT">
              Transport
            </option>

            <option value="PARTICIPANT">
              Participant
            </option>

            <option value="VERIFICATION">
              Verification
            </option>

            <option value="OTHER">
              Other
            </option>
          </Select>

          <Input
            label="Subject"
            name="subject"
            required
            value={form.subject}
            onChange={updateField}
          />

          <Textarea
            label="Problem description"
            name="description"
            required
            rows={6}
            value={form.description}
            onChange={updateField}
          />

          <Button
            type="submit"
            isLoading={submitting}
          >
            Submit report
          </Button>
        </form>
      </Surface>
    </div>
  );
}

function PublicFormLayout({
  title,
  description,
  children,
}) {
  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50 p-5 dark:bg-slate-900">
      <section className="w-full max-w-lg rounded-3xl border border-slate-200 bg-white p-6 shadow-xl dark:border-slate-700 dark:bg-slate-800 sm:p-8">
        <Link
          to="/login"
          className="text-xl font-black text-blue-600 dark:text-blue-400"
        >
          SmartFood
        </Link>

        <h1 className="mt-7 text-3xl font-black tracking-tight text-slate-950 dark:text-white">
          {title}
        </h1>

        <p className="mt-2 text-slate-500 dark:text-slate-400">
          {description}
        </p>

        {children}
      </section>
    </main>
  );
}