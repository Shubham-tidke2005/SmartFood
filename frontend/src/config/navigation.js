import {
  BarChart3,
  Bell,
  CircleHelp,
  ClipboardCheck,
  HandHeart,
  History,
  LayoutDashboard,
  Package,
  PackagePlus,
  Settings,
  ShieldCheck,
  Truck,
  Users,
} from "lucide-react";

const sharedItems = {
  dashboard: {
    label: "Dashboard",
    path: "/dashboard",
    icon: LayoutDashboard,
  },

  analytics: {
    label: "Impact",
    path: "/analytics",
    icon: BarChart3,
  },

  notifications: {
    label: "Notifications",
    path: "/notifications",
    icon: Bell,
  },

  profile: {
    label: "Profile",
    path: "/profile",
    icon: Settings,
  },

  help: {
    label: "Help",
    path: "/help",
    icon: CircleHelp,
  },
};

const roleItems = {
  DONOR: [
    {
      label: "Create donation",
      path: "/donor/donations/new",
      icon: PackagePlus,
    },
    {
      label: "Requests",
      path: "/donor/requests",
      icon: HandHeart,
    },
    {
      label: "History",
      path: "/donor/history",
      icon: History,
    },
  ],

  RECEIVER: [
    {
      label: "Browse donations",
      path: "/receiver/donations",
      icon: Package,
    },
    {
      label: "Requirements",
      path: "/receiver/requirements",
      icon: ClipboardCheck,
    },
    {
      label: "My requests",
      path: "/receiver/requests",
      icon: HandHeart,
    },
  ],

  VOLUNTEER: [
    {
      label: "Available tasks",
      path: "/volunteer/tasks",
      icon: Truck,
    },
    {
      label: "Task history",
      path: "/volunteer/history",
      icon: History,
    },
  ],

  ADMIN: [
    {
      label: "Verifications",
      path: "/admin/verifications",
      icon: ShieldCheck,
    },
    {
      label: "Users",
      path: "/admin/users",
      icon: Users,
    },
    {
      label: "Donations",
      path: "/admin/donations",
      icon: Package,
    },
    {
      label: "Complaints",
      path: "/admin/complaints",
      icon: CircleHelp,
    },
  ],
};

export function getNavigationForRole(role) {
  const normalizedRole =
    role?.toUpperCase();

  return [
    sharedItems.dashboard,
    ...(roleItems[normalizedRole] || []),
    sharedItems.analytics,
    sharedItems.notifications,
    sharedItems.profile,
    sharedItems.help,
  ];
}