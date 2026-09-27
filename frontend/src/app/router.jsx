import {
  Navigate,
  createBrowserRouter,
} from "react-router-dom";

import ProtectedRoute from "../auth/ProtectedRoute";
import RoleRoute from "../auth/RoleRoute";

import AppShell from "../components/layout/AppShell";

import DashboardPage from "../pages/DashboardPage";
import LoginPage from "../pages/LoginPage";
import NotFoundPage from "../pages/NotFoundPage";
import UnauthorizedPage from "../pages/UnauthorizedPage";

import CreateDonationPage from "../pages/donor/CreateDonationPage";
import DonationRequestsPage from "../pages/donor/DonationRequestsPage";
import ReceiverRecommendationsPage from "../pages/donor/ReceiverRecommendationsPage";

import {
  DonorDonationDetailPage,
  DonorHistoryPage,
} from "../pages/donor/DonorPages";

import BrowseDonationsPage from "../pages/receiver/BrowseDonationsPage";

import {
  ReceiptConfirmationPage,
  ReceiverDonationDetailPage,
  ReceiverRequestsPage,
  ReceiverRequirementsPage,
} from "../pages/receiver/ReceiverPages";

import {
  ActiveTaskPage,
  AvailableTasksPage,
  VolunteerTaskHistoryPage,
} from "../pages/volunteer/VolunteerPages";

import {
  AdminDonationsPage,
  AdminUsersPage,
  VerificationQueuePage,
} from "../pages/admin/AdminPages";

import AdminComplaintsPage from "../pages/admin/AdminComplaintsPage";

import AnalyticsPage from "../pages/shared/AnalyticsPage";
import ComplaintsPage from "../pages/shared/ComplaintsPage";
import DirectFulfilmentPage from "../pages/shared/DirectFulfilmentPage";

import {
  HelpReportingPage,
  NotificationsPage,
  PasswordResetPage,
  ProfilePage,
  RegistrationPage,
} from "../pages/shared/SharedPages";


const router = createBrowserRouter([
  {
    path: "/",
    element: (
      <Navigate
        to="/dashboard"
        replace
      />
    ),
  },

  /*
   * Public routes
   */
  {
    path: "/login",
    element: <LoginPage />,
  },
  {
    path: "/register",
    element: <RegistrationPage />,
  },
  {
    path: "/password-reset",
    element: <PasswordResetPage />,
  },
  {
    path: "/unauthorized",
    element: <UnauthorizedPage />,
  },

  /*
   * Authenticated routes
   */
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <AppShell />,
        children: [
          /*
           * Shared authenticated pages
           */
          {
            path: "/dashboard",
            element: <DashboardPage />,
          },
          {
            path: "/profile",
            element: <ProfilePage />,
          },
          {
            path: "/notifications",
            element: <NotificationsPage />,
          },
          {
            path: "/complaints",
            element: <ComplaintsPage />,
          },
          {
            path: "/analytics",
            element: <AnalyticsPage />,
          },
          {
            path: "/help",
            element: <HelpReportingPage />,
          },

          /*
           * Shared fulfilment routes
           *
           * Django still verifies whether the user
           * is the donor, approved receiver or admin.
           */
          {
            element: (
              <RoleRoute
                allowedRoles={[
                  "DONOR",
                  "RECEIVER",
                  "ADMIN",
                ]}
              />
            ),
            children: [
              {
                path: "/fulfilment/:donationId",
                element: <DirectFulfilmentPage />,
              },
            ],
          },

          /*
           * Donor routes
           */
          {
            element: (
              <RoleRoute
                allowedRoles={["DONOR"]}
              />
            ),
            children: [
              {
                path: "/donor/donations/new",
                element: <CreateDonationPage />,
              },
              {
                path: "/donor/donations/:donationId",
                element: <DonorDonationDetailPage />,
              },
              {
                path: (
                  "/donor/donations/"
                  + ":donationId/recommendations"
                ),
                element: (
                  <ReceiverRecommendationsPage />
                ),
              },
              {
                path: "/donor/requests",
                element: <DonationRequestsPage />,
              },
              {
                path: "/donor/history",
                element: <DonorHistoryPage />,
              },
            ],
          },

          /*
           * Receiver routes
           */
          {
            element: (
              <RoleRoute
                allowedRoles={["RECEIVER"]}
              />
            ),
            children: [
              {
                path: "/receiver/donations",
                element: <BrowseDonationsPage />,
              },
              {
                path: (
                  "/receiver/donations/"
                  + ":donationId"
                ),
                element: (
                  <ReceiverDonationDetailPage />
                ),
              },
              {
                path: "/receiver/requirements",
                element: (
                  <ReceiverRequirementsPage />
                ),
              },
              {
                path: "/receiver/requests",
                element: <ReceiverRequestsPage />,
              },
              {
                path: (
                  "/receiver/receipts/"
                  + ":donationId"
                ),
                element: (
                  <ReceiptConfirmationPage />
                ),
              },
            ],
          },

          /*
           * Volunteer routes
           */
          {
            element: (
              <RoleRoute
                allowedRoles={["VOLUNTEER"]}
              />
            ),
            children: [
              {
                path: "/volunteer/tasks",
                element: <AvailableTasksPage />,
              },
              {
                path: "/volunteer/tasks/:taskId",
                element: <ActiveTaskPage />,
              },
              {
                path: "/volunteer/history",
                element: (
                  <VolunteerTaskHistoryPage />
                ),
              },
            ],
          },

          /*
           * Administrator routes
           */
          {
            element: (
              <RoleRoute
                allowedRoles={["ADMIN"]}
              />
            ),
            children: [
              {
                path: "/admin/verifications",
                element: <VerificationQueuePage />,
              },
              {
                path: "/admin/users",
                element: <AdminUsersPage />,
              },
              {
                path: "/admin/donations",
                element: <AdminDonationsPage />,
              },
              {
                path: "/admin/complaints",
                element: <AdminComplaintsPage />,
              },
              {
                path: "/admin/analytics",
                element: <AnalyticsPage />,
              },
            ],
          },
        ],
      },
    ],
  },

  /*
   * Unknown route
   */
  {
    path: "*",
    element: <NotFoundPage />,
  },
]);


export default router;