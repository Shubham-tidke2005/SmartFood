import {
  useState,
} from "react";

import {
  useNavigate,
  useParams,
} from "react-router-dom";

import api from "../../lib/api";
import { getApiErrorMessage } from "../../lib/apiError";
import {
  useApiResource,
} from "../../hooks/useApiResource";

import Button from "../../components/ui/Button";
import {
  ErrorMessage,
} from "../../components/ui/FeedbackStates";
import LoadingState from "../../components/ui/LoadingState";
import {
  PageHeader,
  ResourceGrid,
  Surface,
} from "../../components/ui/PageElements";
import StatusBadge from "../../components/ui/StatusBadge";

export function AvailableTasksPage() {
  const resource = useApiResource(
    "/transport-tasks/?scope=available",
    {
      list: true,
    },
  );

  return (
    <div>
      <PageHeader
        eyebrow="Volunteer"
        title="Available transport tasks"
        description="Browse pickup opportunities that match your availability and service area."
      />

      <ResourceGrid
        items={resource.data}
        loading={resource.loading}
        error={resource.error}
        onRetry={resource.reload}
        emptyTitle="No eligible tasks"
        emptyDescription="New transport opportunities will appear here."
        getDetailPath={(item) =>
          `/volunteer/tasks/${item.id}`
        }
      />
    </div>
  );
}

export function ActiveTaskPage() {
  const { taskId } = useParams();
  const navigate = useNavigate();

  const {
    data,
    loading,
    error,
    reload,
  } = useApiResource(
    `/transport-tasks/${taskId}/`,
  );

  const [actionError, setActionError] =
    useState("");

  const [processingAction, setProcessingAction] =
    useState("");

  async function performAction(
    action,
  ) {
    setProcessingAction(action);
    setActionError("");

    try {
      await api.post(
        `/transport-tasks/${taskId}/${action}/`,
        {},
      );

      await reload();
    } catch (requestError) {
      setActionError(
        getApiErrorMessage(requestError),
      );
    } finally {
      setProcessingAction("");
    }
  }

  if (loading) {
    return (
      <LoadingState message="Loading transport task..." />
    );
  }

  if (error) {
    return (
      <ErrorMessage
        message={error}
        onRetry={reload}
      />
    );
  }

  return (
    <div>
      <PageHeader
        eyebrow="Volunteer task"
        title={
          data?.task_number ||
          "Transport task"
        }
        description="Follow each physical transport step in the correct order."
        action={
          <StatusBadge
            status={data?.status}
          />
        }
      />

      {actionError && (
        <div className="mb-5">
          <ErrorMessage
            message={actionError}
          />
        </div>
      )}

      <Surface>
        <div className="grid gap-5 sm:grid-cols-2">
          <TaskInformation
            label="Pickup"
            value={
              data?.donor_location ||
              data?.pickup_location
            }
          />

          <TaskInformation
            label="Delivery"
            value={
              data?.receiver_location ||
              data?.delivery_location
            }
          />

          <TaskInformation
            label="Food"
            value={
              data?.food_name ||
              data?.donation?.food_name
            }
          />

          <TaskInformation
            label="Deadline"
            value={
              data?.pickup_deadline
                ? new Date(
                    data.pickup_deadline,
                  ).toLocaleString()
                : "—"
            }
          />
        </div>

        <div className="mt-7 flex flex-wrap gap-3">
          <TaskAction
            label="Accept task"
            action="accept"
            currentAction={
              processingAction
            }
            onAction={performAction}
          />

          <TaskAction
            label="Confirm pickup"
            action="confirm-pickup"
            currentAction={
              processingAction
            }
            onAction={performAction}
          />

          <TaskAction
            label="Confirm delivery"
            action="confirm-delivery"
            currentAction={
              processingAction
            }
            onAction={performAction}
          />

          <Button
            variant="danger"
            isLoading={
              processingAction ===
              "report-failure"
            }
            onClick={() =>
              performAction(
                "report-failure",
              )
            }
          >
            Report failure
          </Button>

          <Button
            variant="ghost"
            onClick={() =>
              navigate(
                "/volunteer/tasks",
              )
            }
          >
            Back to tasks
          </Button>
        </div>
      </Surface>
    </div>
  );
}

export function VolunteerTaskHistoryPage() {
  const resource = useApiResource(
    "/transport-tasks/?scope=history",
    {
      list: true,
    },
  );

  return (
    <div>
      <PageHeader
        eyebrow="Volunteer"
        title="Task history"
        description="Review completed, cancelled and failed transport tasks."
      />

      <ResourceGrid
        items={resource.data}
        loading={resource.loading}
        error={resource.error}
        onRetry={resource.reload}
        emptyTitle="No previous tasks"
        emptyDescription="Completed transport tasks will appear here."
        getDetailPath={(item) =>
          `/volunteer/tasks/${item.id}`
        }
      />
    </div>
  );
}

function TaskAction({
  label,
  action,
  currentAction,
  onAction,
}) {
  return (
    <Button
      variant="secondary"
      isLoading={
        currentAction === action
      }
      disabled={
        Boolean(currentAction) &&
        currentAction !== action
      }
      onClick={() =>
        onAction(action)
      }
    >
      {label}
    </Button>
  );
}

function TaskInformation({
  label,
  value,
}) {
  return (
    <div>
      <p className="text-sm font-semibold text-slate-500 dark:text-slate-400">
        {label}
      </p>
      <p className="mt-1 font-medium text-slate-950 dark:text-white">
        {value || "—"}
      </p>
    </div>
  );
}