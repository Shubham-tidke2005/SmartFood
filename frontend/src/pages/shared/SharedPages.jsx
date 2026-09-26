import {
  useState,
} from "react";

import {
  Link,
  useNavigate,
} from "react-router-dom";

import api from "../../lib/api";
import { getApiErrorMessage } from "../../lib/apiError";
import {
  useApiResource,
} from "../../hooks/useApiResource";

import { useAuth } from "../../auth/AuthProvider";
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
import LoadingState from "../../components/ui/LoadingState";
import {
  PageHeader,
  ResourceGrid,
  SubmitBar,
  Surface,
} from "../../components/ui/PageElements";

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
    setForm({
      ...form,
      [event.target.name]:
        event.target.value,
    });
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
      });
    } catch (requestError) {
      setError(
        getApiErrorMessage(requestError),
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
        <ErrorMessage message={error} />
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
          label="Email"
          name="email"
          type="email"
          required
          value={form.email}
          onChange={updateField}
        />

        <Input
          label="Mobile number"
          name="mobile"
          required
          value={form.mobile}
          onChange={updateField}
        />

        <Select
          label="Role"
          name="role"
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
          value={form.password_confirm}
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

      <p className="mt-5 text-center text-sm">
        Already registered?{" "}
        <Link
          className="font-bold text-blue-600"
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

  const [submitting, setSubmitting] =
    useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setSubmitting(true);

    try {
      await api.post(
        "/auth/password-reset/",
        {
          email,
        },
      );

      setSubmitted(true);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <PublicFormLayout
      title="Reset password"
      description="Enter your account email to receive password reset instructions."
    >
      {submitted ? (
        <EmptyState
          title="Check your email"
          description="If an eligible account exists, SmartFood has sent password reset instructions."
        />
      ) : (
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
    display_name:
      user?.display_name || "",
    mobile:
      user?.mobile || "",
  });

  const [message, setMessage] =
    useState("");

  const [error, setError] =
    useState("");

  const [submitting, setSubmitting] =
    useState(false);

  async function handleSubmit(event) {
    event.preventDefault();

    setSubmitting(true);
    setError("");
    setMessage("");

    try {
      await api.patch(
        "/profiles/me/",
        form,
      );

      await refreshUser();

      setMessage(
        "Profile updated successfully.",
      );
    } catch (requestError) {
      setError(
        getApiErrorMessage(requestError),
      );
    } finally {
      setSubmitting(false);
    }
  }

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
            className="mb-5 rounded-xl bg-emerald-50 p-4 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300"
          >
            {message}
          </p>
        )}

        {error && (
          <div className="mb-5">
            <ErrorMessage message={error} />
          </div>
        )}

        <form
          className="space-y-5"
          onSubmit={handleSubmit}
        >
          <Input
            label="Display name"
            required
            value={form.display_name}
            onChange={(event) =>
              setForm({
                ...form,
                display_name:
                  event.target.value,
              })
            }
          />

          <Input
            label="Email"
            value={user?.email || ""}
            disabled
            hint="Contact support to change your account email."
          />

          <Input
            label="Mobile number"
            value={form.mobile}
            onChange={(event) =>
              setForm({
                ...form,
                mobile:
                  event.target.value,
              })
            }
          />

          <Input
            label="Role"
            value={user?.role || ""}
            disabled
          />

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
  const resource = useApiResource(
    "/notifications/",
    {
      list: true,
    },
  );

  return (
    <div>
      <PageHeader
        title="Notifications"
        description="Review donation, request, transport and verification updates."
      />

      <ResourceGrid
        items={resource.data}
        loading={resource.loading}
        error={resource.error}
        onRetry={resource.reload}
        emptyTitle="No notifications"
        emptyDescription="Important SmartFood updates will appear here."
      />
    </div>
  );
}

export function HelpReportingPage() {
  const [form, setForm] = useState({
    subject: "",
    description: "",
  });

  const [submitted, setSubmitted] =
    useState(false);

  const [submitting, setSubmitting] =
    useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setSubmitting(true);

    try {
      await api.post(
        "/complaints/",
        form,
      );

      setSubmitted(true);
      setForm({
        subject: "",
        description: "",
      });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div>
      <PageHeader
        title="Help and reporting"
        description="Report a donation, delivery, participant or platform issue."
      />

      <Surface className="max-w-2xl">
        {submitted && (
          <p
            role="status"
            className="mb-5 rounded-xl bg-emerald-50 p-4 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300"
          >
            Your report was submitted successfully.
          </p>
        )}

        <form
          className="space-y-5"
          onSubmit={handleSubmit}
        >
          <Input
            label="Subject"
            required
            value={form.subject}
            onChange={(event) =>
              setForm({
                ...form,
                subject:
                  event.target.value,
              })
            }
          />

          <Textarea
            label="Problem description"
            required
            rows={6}
            value={form.description}
            onChange={(event) =>
              setForm({
                ...form,
                description:
                  event.target.value,
              })
            }
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
          className="text-xl font-black text-blue-600"
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