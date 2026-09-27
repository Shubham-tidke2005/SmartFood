import {
  BarChart3,
  CircleAlert,
  Package,
  ShieldCheck,
  Truck,
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
    "/admin/users/",
    {
      list: true,
    },
  );

  return (
    <AdminListPage
      title="Users"
      description="Review participant roles, verification status and account activity."
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
      description="Monitor food listings and redistribution workflow status."
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
      description="Review reported donation, participant and transport problems."
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
          description="Review SmartFood activity and redistribution performance."
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
        description="Review users, donations, volunteer transport and operational issues."
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="Registered users"
          value={data?.total_users}
          icon={Users}
        />

        <MetricCard
          label="Verified users"
          value={data?.verified_users}
          icon={ShieldCheck}
          color="emerald"
        />

        <MetricCard
          label="Total donations"
          value={data?.total_donations}
          icon={Package}
          color="amber"
        />

        <MetricCard
          label="Completed donations"
          value={
            data?.completed_donations
          }
          icon={BarChart3}
          color="emerald"
        />

        <MetricCard
          label="Volunteer tasks"
          value={
            data?.total_volunteer_tasks
          }
          icon={Truck}
        />

        <MetricCard
          label="Open tasks"
          value={
            data?.open_volunteer_tasks
          }
          icon={Truck}
          color="amber"
        />

        <MetricCard
          label="Open complaints"
          value={
            data?.open_complaints
          }
          icon={CircleAlert}
          color="red"
        />

        <MetricCard
          label="Complaints in review"
          value={
            data?.complaints_in_review
          }
          icon={CircleAlert}
          color="amber"
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