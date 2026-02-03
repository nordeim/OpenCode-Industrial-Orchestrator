/**
 * SESSIONS API HOOKS
 * 
 * React Query hooks for session management.
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "./client";
import type {
    Session,
    SessionListResponse,
    CreateSessionRequest,
    SessionStatistics,
    SessionStatus,
} from "./types";

// Query keys
export const sessionKeys = {
    all: ["sessions"] as const,
    lists: () => [...sessionKeys.all, "list"] as const,
    list: (filters: SessionFilters) => [...sessionKeys.lists(), filters] as const,
    details: () => [...sessionKeys.all, "detail"] as const,
    detail: (id: string) => [...sessionKeys.details(), id] as const,
    statistics: () => [...sessionKeys.all, "statistics"] as const,
};

// Filter types
export interface SessionFilters {
    status?: SessionStatus;
    page?: number;
    pageSize?: number;
    search?: string;
}

/**
 * Fetch sessions list
 */
export function useSessions(filters: SessionFilters = {}) {
    return useQuery({
        queryKey: sessionKeys.list(filters),
        queryFn: async () => {
            return api.get<SessionListResponse>("/api/v1/sessions", {
                params: {
                    status: filters.status,
                    page: filters.page,
                    page_size: filters.pageSize,
                    search: filters.search,
                },
            });
        },
    });
}

/**
 * Fetch single session
 */
export function useSession(id: string) {
    return useQuery({
        queryKey: sessionKeys.detail(id),
        queryFn: async () => {
            return api.get<Session>(`/api/v1/sessions/${id}`);
        },
        enabled: !!id,
    });
}

/**
 * Fetch session statistics
 */
export function useSessionStatistics() {
    return useQuery({
        queryKey: sessionKeys.statistics(),
        queryFn: async () => {
            return api.get<SessionStatistics>("/api/v1/sessions/statistics");
        },
    });
}

/**
 * Create session mutation
 */
export function useCreateSession() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async (data: CreateSessionRequest) => {
            return api.post<Session>("/api/v1/sessions", data);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: sessionKeys.lists() });
            queryClient.invalidateQueries({ queryKey: sessionKeys.statistics() });
        },
    });
}

/**
 * Start session mutation
 */
export function useStartSession() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async (id: string) => {
            return api.post<Session>(`/api/v1/sessions/${id}/start`);
        },
        onSuccess: (data) => {
            queryClient.setQueryData(sessionKeys.detail(data.id), data);
            queryClient.invalidateQueries({ queryKey: sessionKeys.lists() });
        },
    });
}

/**
 * Pause session mutation
 */
export function usePauseSession() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async (id: string) => {
            return api.post<Session>(`/api/v1/sessions/${id}/pause`);
        },
        onSuccess: (data) => {
            queryClient.setQueryData(sessionKeys.detail(data.id), data);
            queryClient.invalidateQueries({ queryKey: sessionKeys.lists() });
        },
    });
}

/**
 * Resume session mutation
 */
export function useResumeSession() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async (id: string) => {
            return api.post<Session>(`/api/v1/sessions/${id}/resume`);
        },
        onSuccess: (data) => {
            queryClient.setQueryData(sessionKeys.detail(data.id), data);
            queryClient.invalidateQueries({ queryKey: sessionKeys.lists() });
        },
    });
}

/**
 * Cancel session mutation
 */
export function useCancelSession() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async ({ id, reason }: { id: string; reason?: string }) => {
            return api.post<Session>(`/api/v1/sessions/${id}/cancel`, { reason });
        },
        onSuccess: (data) => {
            queryClient.setQueryData(sessionKeys.detail(data.id), data);
            queryClient.invalidateQueries({ queryKey: sessionKeys.lists() });
            queryClient.invalidateQueries({ queryKey: sessionKeys.statistics() });
        },
    });
}

/**
 * Complete session mutation
 */
export function useCompleteSession() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async ({ id, result }: { id: string; result: Record<string, unknown> }) => {
            return api.post<Session>(`/api/v1/sessions/${id}/complete`, { result });
        },
        onSuccess: (data) => {
            queryClient.setQueryData(sessionKeys.detail(data.id), data);
            queryClient.invalidateQueries({ queryKey: sessionKeys.lists() });
            queryClient.invalidateQueries({ queryKey: sessionKeys.statistics() });
        },
    });
}
