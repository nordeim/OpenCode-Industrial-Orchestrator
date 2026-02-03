/**
 * TASKS API HOOKS
 * 
 * React Query hooks for task management.
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "./client";
import type {
    Task,
    TaskListResponse,
    CreateTaskRequest,
    TaskDecompositionResult,
    TaskStatus,
} from "./types";

// Query keys
export const taskKeys = {
    all: ["tasks"] as const,
    lists: () => [...taskKeys.all, "list"] as const,
    list: (filters?: TaskFilters) => [...taskKeys.lists(), filters] as const,
    details: () => [...taskKeys.all, "detail"] as const,
    detail: (id: string) => [...taskKeys.details(), id] as const,
    bySession: (sessionId: string) => [...taskKeys.all, "session", sessionId] as const,
};

// Filter types
export interface TaskFilters {
    session_id?: string;
    status?: TaskStatus;
    parent_only?: boolean;
}

/**
 * Fetch tasks list
 */
export function useTasks(filters: TaskFilters = {}) {
    return useQuery({
        queryKey: taskKeys.list(filters),
        queryFn: async () => {
            return api.get<TaskListResponse>("/api/v1/tasks", {
                params: {
                    session_id: filters.session_id,
                    status: filters.status,
                    parent_only: filters.parent_only,
                },
            });
        },
    });
}

/**
 * Fetch single task
 */
export function useTask(id: string) {
    return useQuery({
        queryKey: taskKeys.detail(id),
        queryFn: async () => {
            return api.get<Task>(`/api/v1/tasks/${id}`);
        },
        enabled: !!id,
    });
}

/**
 * Fetch tasks by session
 */
export function useTasksBySession(sessionId: string) {
    return useQuery({
        queryKey: taskKeys.bySession(sessionId),
        queryFn: async () => {
            return api.get<TaskListResponse>(`/api/v1/sessions/${sessionId}/tasks`);
        },
        enabled: !!sessionId,
    });
}

/**
 * Create task mutation
 */
export function useCreateTask() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async (data: CreateTaskRequest) => {
            return api.post<Task>("/api/v1/tasks", data);
        },
        onSuccess: (data) => {
            queryClient.invalidateQueries({ queryKey: taskKeys.lists() });
            queryClient.invalidateQueries({ queryKey: taskKeys.bySession(data.session_id) });
        },
    });
}

/**
 * Update task status mutation
 */
export function useUpdateTaskStatus() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async ({ id, status }: { id: string; status: TaskStatus }) => {
            return api.patch<Task>(`/api/v1/tasks/${id}/status`, { status });
        },
        onSuccess: (data) => {
            queryClient.setQueryData(taskKeys.detail(data.id), data);
            queryClient.invalidateQueries({ queryKey: taskKeys.lists() });
            queryClient.invalidateQueries({ queryKey: taskKeys.bySession(data.session_id) });
        },
    });
}

/**
 * Decompose task mutation
 */
export function useDecomposeTask() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async ({ id, template }: { id: string; template?: string }) => {
            return api.post<TaskDecompositionResult>(`/api/v1/tasks/${id}/decompose`, {
                template,
            });
        },
        onSuccess: (data) => {
            queryClient.invalidateQueries({ queryKey: taskKeys.lists() });
            // Invalidate parent task
            queryClient.invalidateQueries({
                queryKey: taskKeys.detail(data.parent_task_id)
            });
        },
    });
}

/**
 * Assign task to agent mutation
 */
export function useAssignTask() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async ({ taskId, agentId }: { taskId: string; agentId: string }) => {
            return api.post<Task>(`/api/v1/tasks/${taskId}/assign`, {
                agent_id: agentId,
            });
        },
        onSuccess: (data) => {
            queryClient.setQueryData(taskKeys.detail(data.id), data);
            queryClient.invalidateQueries({ queryKey: taskKeys.lists() });
        },
    });
}
