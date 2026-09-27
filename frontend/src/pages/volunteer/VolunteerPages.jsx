import {
  useMemo,
  useState,
} from "react";

import {
  useNavigate,
  useParams,
} from "react-router-dom";

import api from "../../lib/api";

import {
  getApiErrorMessage,
} from "../../lib/apiError";

import {
  useApiResource,
} from "../../hooks/useApiResource";

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
  Surface,
} from "../../components/ui/PageElements";

import StatusBadge from "../../components/ui/StatusBadge";


export function AvailableTasksPage() {
  const resource = useApiResource(
    "/logistics/volunteer/tasks/eligible/",
    {
      list: true,
    },
  );

  return (
    <div>
      <PageHeader
        eyebrow="Volunteer"
        title="Available transport tasks"
        description="Browse transport opportunities matching your service area, availability and capacity."
      />

      <ResourceGrid
        items={resource.data}
        loading={resource.loading}
        error={resource.error}
        onRetry={resource.reload}
        emptyTitle="No eligible tasks"
        emptyDescription="New eligible transport tasks will appear here."
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

  const eligibleResource =
    useApiResource(
      "/logistics/volunteer/tasks/eligible/",
      {
        list: true,
      },
    );

  const myTasksResource =
    useApiResource(
      "/logistics/volunteer/tasks/mine/",
      {
        list: true,
      },
    );

  const task = useMemo(() => {
    const tasks = [
      ...(eligibleResource.data || []),
      ...(myTasksResource.data || []),
    ];

    return tasks.find(
      (item) =>
        String(item.id) ===
        String(taskId),
    );
  }, [
    eligibleResource.data,
    myTasksResource.data,
    taskId,
  ]);

  const [processingAction, setProcessingAction] =
    useState("");

  const [actionError, setActionError] =
    useState("");

  const [successMessage, setSuccessMessage] =
    useState("");

  const [quantityForm, setQuantityForm] =
    useState({
      quantity: "",
      unit: "MEALS",
      notes: "",
    });

  const [failureForm, setFailureForm] =
    useState({
      stage: "BEFORE_PICKUP",
      reason: "",
      reassign_requested: true,
    });

  async function reloadTasks() {
    await Promise.all([
      eligibleResource.reload(),
      myTasksResource.reload(),
    ]);
  }

  async function acceptTask() {
    await performRequest(
      "accept",
      `/logistics/volunteer/tasks/${taskId}/accept/`,
      {},
      "Task accepted successfully.",
    );
  }

  async function recordPickup() {
    const quantity =
      Number(quantityForm.quantity);

    if (
      !Number.isFinite(quantity) ||
      quantity <= 0
    ) {
      setActionError(
        "Enter a positive pickup quantity.",
      );
      return;
    }

    await performRequest(
      "pickup",
      `/logistics/volunteer/tasks/${taskId}/pickup/`,
      {
        actual_quantity: quantity,
        unit: quantityForm.unit,
        notes: quantityForm.notes.trim(),
        picked_up_at:
          new Date().toISOString(),
      },
      "Pickup recorded successfully.",
    );
  }

  async function recordDelivery() {
    const quantity =
      Number(quantityForm.quantity);

    if (
      !Number.isFinite(quantity) ||
      quantity <= 0
    ) {
      setActionError(
        "Enter a positive delivered quantity.",
      );
      return;
    }

    await performRequest(
      "delivery",
      `/logistics/volunteer/tasks/${taskId}/delivery/`,
      {
        actual_quantity: quantity,
        unit: quantityForm.unit,
        notes: quantityForm.notes.trim(),
        delivered_at:
          new Date().toISOString(),
      },
      "Delivery recorded successfully.",
    );
  }

  async function cancelAssignment() {
    await performRequest(
      "cancel",
      `/logistics/volunteer/tasks/${taskId}/cancel-assignment/`,
      {
        reason:
          "Assignment cancelled by volunteer.",
      },
      "Assignment cancelled.",
    );
  }

  async function reportFailure() {
    if (
      failureForm.reason.trim().length <
      5
    ) {
      setActionError(
        "Enter a clear failure reason.",
      );
      return;
    }

    await performRequest(
      "failure",
      `/logistics/volunteer/tasks/${taskId}/report-failure/`,
      {
        stage: failureForm.stage,
        reason:
          failureForm.reason.trim(),
        reassign_requested:
          failureForm.reassign_requested,
      },
      "Failure report submitted.",
    );
  }

  async function performRequest(
    action,
    endpoint,
    payload,
    success,
  ) {
    setProcessingAction(action);
    setActionError("");
    setSuccessMessage("");

    try {
      await api.post(
        endpoint,
        payload,
      );

      setSuccessMessage(success);
      await reloadTasks();
    } catch (requestError) {
      setActionError(
        getApiErrorMessage(requestError),
      );
    } finally {
      setProcessingAction("");
    }
  }

  const loading =
    eligibleResource.loading ||
    myTasksResource.loading;

  if (loading) {
    return (
      <LoadingState message="Loading transport task..." />
    );
  }

  if (
    eligibleResource.error &&
    myTasksResource.error
  ) {
    return (
      <ErrorMessage
        message={
          myTasksResource.error ||
          eligibleResource.error
        }
        onRetry={reloadTasks}
      />
    );
  }

  if (!task) {
    return (
      <div>
        <PageHeader
          eyebrow="Volunteer"
          title="Transport task"
          description="The requested transport task is unavailable."
        />

        <EmptyState
          title="Task not found"
          description="The task may have been accepted, cancelled or completed."
          action={
            <Button
              onClick={() =>
                navigate(
                  "/volunteer/tasks",
                )
              }
            >
              Return to tasks
            </Button>
          }
        />
      </div>
    );
  }

  const status =
    task.status ||
    task.task_status;

  return (
    <div>
      <PageHeader
        eyebrow="Volunteer task"
        title={
          task.task_number ||
          `Task ${task.id}`
        }
        description="Complete each physical transport step in the correct order."
        action={
          <StatusBadge status={status} />
        }
      />

      {successMessage && (
        <p
          role="status"
          className="mb-5 rounded-xl bg-emerald-50 p-4 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300"
        >
          {successMessage}
        </p>
      )}

      {actionError && (
        <div className="mb-5">
          <ErrorMessage
            message={actionError}
          />
        </div>
      )}

      <div className="grid gap-5 xl:grid-cols-3">
        <Surface className="xl:col-span-2">
          <h2 className="text-xl font-black">
            Transport information
          </h2>

          <div className="mt-5 grid gap-5 sm:grid-cols-2">
            <Information
              label="Pickup area"
              value={
                task.pickup_area ||
                task.pickup_location
              }
            />

            <Information
              label="Receiver area"
              value={
                task.receiver_area ||
                task.receiver_location
              }
            />

            <Information
              label="Food"
              value={
                task.food_name ||
                task.donation?.food_name
              }
            />

            <Information
              label="Required quantity"
              value={
                `${task.required_quantity ?? task.quantity ?? "—"} ` +
                `${task.unit ?? ""}`
              }
            />

            <Information
              label="Pickup deadline"
              value={
                task.pickup_deadline
                  ? new Date(
                      task.pickup_deadline,
                    ).toLocaleString()
                  : "—"
              }
            />

            <Information
              label="Current status"
              value={status}
            />
          </div>

          <div className="mt-7 border-t border-slate-200 pt-6 dark:border-slate-700">
            <h3 className="text-lg font-black">
              Pickup and delivery quantity
            </h3>

            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <Input
                label="Actual quantity"
                type="number"
                min="0.001"
                step="0.001"
                value={
                  quantityForm.quantity
                }
                onChange={(event) =>
                  setQuantityForm({
                    ...quantityForm,
                    quantity:
                      event.target.value,
                  })
                }
              />

              <Select
                label="Unit"
                value={
                  quantityForm.unit
                }
                onChange={(event) =>
                  setQuantityForm({
                    ...quantityForm,
                    unit:
                      event.target.value,
                  })
                }
              >
                <option value="MEALS">
                  Meals
                </option>
                <option value="KG">
                  Kilograms
                </option>
                <option value="LITRES">
                  Litres
                </option>
                <option value="PACKETS">
                  Packets
                </option>
                <option value="PIECES">
                  Pieces
                </option>
              </Select>
            </div>

            <Textarea
              className="mt-4"
              label="Transport notes"
              value={quantityForm.notes}
              onChange={(event) =>
                setQuantityForm({
                  ...quantityForm,
                  notes:
                    event.target.value,
                })
              }
            />
          </div>
        </Surface>

        <div className="space-y-5">
          <Surface>
            <h2 className="text-lg font-black">
              Task actions
            </h2>

            <div className="mt-5 flex flex-col gap-3">
              <ActionButton
                label="Accept task"
                action="accept"
                currentAction={
                  processingAction
                }
                onClick={acceptTask}
              />

              <ActionButton
                label="Record pickup"
                action="pickup"
                currentAction={
                  processingAction
                }
                onClick={recordPickup}
              />

              <ActionButton
                label="Record delivery"
                action="delivery"
                currentAction={
                  processingAction
                }
                onClick={recordDelivery}
              />

              <ActionButton
                label="Cancel assignment"
                action="cancel"
                variant="secondary"
                currentAction={
                  processingAction
                }
                onClick={
                  cancelAssignment
                }
              />
            </div>
          </Surface>

          <Surface>
            <h2 className="text-lg font-black">
              Report transport failure
            </h2>

            <div className="mt-4 space-y-4">
              <Select
                label="Failure stage"
                value={failureForm.stage}
                onChange={(event) =>
                  setFailureForm({
                    ...failureForm,
                    stage:
                      event.target.value,
                  })
                }
              >
                <option value="BEFORE_PICKUP">
                  Before pickup
                </option>
                <option value="AFTER_PICKUP">
                  After pickup
                </option>
              </Select>

              <Textarea
                label="Failure reason"
                value={
                  failureForm.reason
                }
                onChange={(event) =>
                  setFailureForm({
                    ...failureForm,
                    reason:
                      event.target.value,
                  })
                }
              />

              <label className="flex items-center gap-3 text-sm font-semibold">
                <input
                  type="checkbox"
                  checked={
                    failureForm
                      .reassign_requested
                  }
                  onChange={(event) =>
                    setFailureForm({
                      ...failureForm,
                      reassign_requested:
                        event.target
                          .checked,
                    })
                  }
                  className="size-4 accent-blue-600"
                />

                Request reassignment
              </label>

              <Button
                variant="danger"
                className="w-full"
                isLoading={
                  processingAction ===
                  "failure"
                }
                onClick={reportFailure}
              >
                Report failure
              </Button>
            </div>
          </Surface>
        </div>
      </div>
    </div>
  );
}


export function VolunteerTaskHistoryPage() {
  const resource = useApiResource(
    "/logistics/volunteer/tasks/mine/",
    {
      list: true,
    },
  );

  const historyTasks = useMemo(() => {
    const finalStatuses = [
      "DELIVERED",
      "COMPLETED",
      "CANCELLED",
      "FAILED",
    ];

    return (
      resource.data || []
    ).filter((task) =>
      finalStatuses.includes(
        String(
          task.status ||
          task.task_status ||
          "",
        ).toUpperCase(),
      ),
    );
  }, [resource.data]);

  return (
    <div>
      <PageHeader
        eyebrow="Volunteer"
        title="Task history"
        description="Review completed, cancelled and failed transport tasks."
      />

      <ResourceGrid
        items={historyTasks}
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


function ActionButton({
  label,
  action,
  currentAction,
  onClick,
  variant = "secondary",
}) {
  return (
    <Button
      variant={variant}
      className="w-full"
      isLoading={
        currentAction === action
      }
      disabled={
        Boolean(currentAction) &&
        currentAction !== action
      }
      onClick={onClick}
    >
      {label}
    </Button>
  );
}


function Information({
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