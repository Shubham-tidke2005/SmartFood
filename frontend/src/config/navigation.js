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

const sharedItems = [
  {
    label: "Dashboard",
    path: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    label: "Notifications",
    path: "/notifications",
    icon: Bell,
  },
  {
    label: "Profile",
    path: "/profile",
    icon: Settings,
  },
  {
    label: "Help",
    path: "/help",
    icon: CircleHelp,
  },
];

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
    {
      label: "Analytics",
      path: "/admin/analytics",
      icon: BarChart3,
    },
  ],
};

export function getNavigationForRole(role) {
  const normalizedRole =
    role?.toUpperCase();

  return [
    sharedItems[0],
    ...(roleItems[normalizedRole] || []),
    ...sharedItems.slice(1),
  ];
}