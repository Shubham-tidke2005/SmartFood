import {
  BarChart3,
  Bell,
  ClipboardCheck,
  HandHeart,
  LayoutDashboard,
  Package,
  Settings,
  ShieldCheck,
  Truck,
  Users,
} from "lucide-react";

const commonItems = [
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
];

const roleItems = {
  DONOR: [
    {
      label: "My donations",
      path: "/donations",
      icon: Package,
    },
    {
      label: "Receiver requests",
      path: "/requests",
      icon: HandHeart,
    },
    {
      label: "Impact",
      path: "/analytics",
      icon: BarChart3,
    },
  ],

  RECEIVER: [
    {
      label: "Discover food",
      path: "/discover",
      icon: Package,
    },
    {
      label: "My requests",
      path: "/requests",
      icon: ClipboardCheck,
    },
    {
      label: "Food received",
      path: "/received",
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
      label: "My deliveries",
      path: "/volunteer/deliveries",
      icon: ClipboardCheck,
    },
    {
      label: "Impact",
      path: "/analytics",
      icon: BarChart3,
    },
  ],

  ADMIN: [
    {
      label: "Participants",
      path: "/admin/participants",
      icon: Users,
    },
    {
      label: "Verifications",
      path: "/admin/verifications",
      icon: ShieldCheck,
    },
    {
      label: "Operations",
      path: "/admin/operations",
      icon: Truck,
    },
    {
      label: "Analytics",
      path: "/analytics",
      icon: BarChart3,
    },
  ],
};

export function getNavigationForRole(role) {
  const normalizedRole =
    role?.toUpperCase();

  return [
    commonItems[0],
    ...(roleItems[normalizedRole] || []),
    ...commonItems.slice(1),
  ];
}