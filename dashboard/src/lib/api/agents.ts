/**
 * AGENTS API HOOKS
 * 
 * React Query hooks for agent management.
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "./client";
import type {
    Agent,
    AgentListResponse,
    RegisterAgentRequest,
    AgentPerformanceSummary,
    AgentCapability,
} from "./types";

// Query keys
export const agentKeys = {
    all: ["agents"] as const,
    lists: () => [...agentKeys.all, "list"] as const,
    list: (filters?: AgentFilters) => [...agentKeys.lists(), filters] as const,
    details: () => [...agentKeys.all, "detail"] as const,
    detail: (id: string) => [...agentKeys.details(), id] as const,
    performance: () => [...agentKeys.all, "performance"] as const,
};

// Filter types
export interface AgentFilters {
    capability?: AgentCapability;
    available_only?: boolean;
}

/**
 * Fetch agents list
 */
export function useAgents(filters: AgentFilters = {}) {
    return useQuery({
        queryKey: agentKeys.list(filters),
        queryFn: async () => {
            return api.get<AgentListResponse>("/api/v1/agents", {
                params: {
                    capability: filters.capability,
                    available_only: filters.available_only,
                },
            });
        },
    });
}

/**
 * Fetch single agent
 */
export function useAgent(id: string) {
    return useQuery({
        queryKey: agentKeys.detail(id),
        queryFn: async () => {
            return api.get<Agent>(`/api/v1/agents/${id}`);
        },
        enabled: !!id,
    });
}

/**
 * Fetch agent performance summary
 */
export function useAgentPerformance() {
    return useQuery({
        queryKey: agentKeys.performance(),
        queryFn: async () => {
            return api.get<AgentPerformanceSummary>("/api/v1/agents/performance");
        },
    });
}

/**
 * Register agent mutation
 */
export function useRegisterAgent() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async (data: RegisterAgentRequest) => {
            return api.post<Agent>("/api/v1/agents/register", data);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: agentKeys.lists() });
            queryClient.invalidateQueries({ queryKey: agentKeys.performance() });
        },
    });
}

/**
 * Deregister agent mutation
 */
export function useDeregisterAgent() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async (id: string) => {
            return api.post(`/api/v1/agents/${id}/deregister`);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: agentKeys.lists() });
            queryClient.invalidateQueries({ queryKey: agentKeys.performance() });
        },
    });
}

/**
 * Send heartbeat mutation
 */
export function useAgentHeartbeat() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async ({ id, load }: { id: string; load: number }) => {
            return api.post<Agent>(`/api/v1/agents/${id}/heartbeat`, {
                current_load: load,
            });
        },
        onSuccess: (data) => {
            queryClient.setQueryData(agentKeys.detail(data.id), data);
        },
    });
}
