/**
 * FINE-TUNING API HOOKS
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "./client";
import type {
    FineTuningJobResponse,
    CreateFineTuningJobRequest,
} from "./types";

export const fineTuningKeys = {
    all: ["fine-tuning"] as const,
    lists: () => [...fineTuningKeys.all, "list"] as const,
    details: () => [...fineTuningKeys.all, "detail"] as const,
    detail: (id: string) => [...fineTuningKeys.details(), id] as const,
};

export function useFineTuningJobs() {
    return useQuery({
        queryKey: fineTuningKeys.lists(),
        queryFn: async () => {
            // Placeholder: Backend doesn't have a list endpoint yet, 
            // but we'll assume it returns an array for the UI.
            return api.get<FineTuningJobResponse[]>("/api/v1/fine-tuning/jobs");
        },
    });
}

export function useFineTuningJob(id: string) {
    return useQuery({
        queryKey: fineTuningKeys.detail(id),
        queryFn: async () => {
            return api.get<FineTuningJobResponse>(`/api/v1/fine-tuning/jobs/${id}`);
        },
        enabled: !!id,
    });
}

export function useCreateFineTuningJob() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async (data: CreateFineTuningJobRequest) => {
            return api.post<FineTuningJobResponse>("/api/v1/fine-tuning/jobs", data);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: fineTuningKeys.lists() });
        },
    });
}

export function useStartFineTuningJob() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async ({ id, datasetDir }: { id: string; datasetDir: string }) => {
            return api.post<FineTuningJobResponse>(`/api/v1/fine-tuning/jobs/${id}/start`, null, {
                params: { dataset_dir: datasetDir }
            });
        },
        onSuccess: (data) => {
            queryClient.invalidateQueries({ queryKey: fineTuningKeys.lists() });
            queryClient.invalidateQueries({ queryKey: fineTuningKeys.detail(data.id) });
        },
    });
}

export function usePollFineTuningJobs() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async () => {
            return api.post<{ updated_count: number }>("/api/v1/fine-tuning/jobs/poll");
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: fineTuningKeys.all });
        },
    });
}
