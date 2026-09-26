import {
  BarChart3,
  Package,
  ShieldCheck,
  Users,
} from "lucide-react";

import {
  useApiResource,
} from "../../hooks/useApiResource";

import {
  MetricCard,
  PageHeader,
  ResourceGrid,
} from "../../components/ui/PageElements";

export function VerificationQueuePage() {
  const resource = useApiResource(
    "/verifications/?status=PENDING",
    {
      list: true,
    },
  );

  return (
    <AdminListPage
      title="Verification queue"
      description="Review pending participant and organization verification submissions."
      resource={resource}
      emptyTitle="Verification queue is clear"
    />
  );
}

export function AdminUsersPage() {
  const resource = useApiResource(
    "/profiles/",
    {
      list: true,
    },
  );

  return (
    <AdminListPage
      title="Users"
      description="Review participant roles, account status and verification state."
      resource={resource}
      emptyTitle="No users found"
    />
  );
}

export function AdminDonationsPage() {
  const resource = useApiResource(
    "/donations/?scope=admin",
    {
      list: true,
    },
  );

  return (
    <AdminListPage
      title="Donation monitoring"
      description="Monitor listings and complete redistribution workflows."
      resource={resource}
      emptyTitle="No donations found"
    />
  );
}

export function AdminComplaintsPage() {
  const resource = useApiResource(
    "/complaints/",
    {
      list: true,
    },
  );

  return (
    <AdminListPage
      title="Complaints"
      description="Review reported operational problems and participant complaints."
      resource={resource}
      emptyTitle="No complaints"
    />
  );
}

export function AdminAnalyticsPage() {
  const {
    data,
    loading,
    error,
    reload,
  } = useApiResource(
    "/analytics/",
  );

  if (loading || error) {
    return (
      <div>
        <PageHeader
          eyebrow="Administrator"
          title="Platform analytics"
          description="Review SmartFood activity and redistribution impact."
        />

        <ResourceGrid
          items={[]}
          loading={loading}
          error={error}
          onRetry={reload}
          emptyTitle="Analytics unavailable"
        />
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        eyebrow="Administrator"
        title="Platform analytics"
        description="Review SmartFood activity and redistribution impact."
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="Registered users"
          value={
            data?.total_users ?? 0
          }
          icon={Users}
        />

        <MetricCard
          label="Verified participants"
          value={
            data?.verified_users ?? 0
          }
          icon={ShieldCheck}
          color="emerald"
        />

        <MetricCard
          label="Total donations"
          value={
            data?.total_donations ?? 0
          }
          icon={Package}
          color="amber"
        />

        <MetricCard
          label="Completed donations"
          value={
            data?.completed_donations ??
            0
          }
          icon={BarChart3}
          color="emerald"
        />
      </div>
    </div>
  );
}

function AdminListPage({
  title,
  description,
  resource,
  emptyTitle,
}) {
  return (
    <div>
      <PageHeader
        eyebrow="Administrator"
        title={title}
        description={description}
      />

      <ResourceGrid
        items={resource.data}
        loading={resource.loading}
        error={resource.error}
        onRetry={resource.reload}
        emptyTitle={emptyTitle}
        emptyDescription="There are currently no records requiring attention."
      />
    </div>
  );
}