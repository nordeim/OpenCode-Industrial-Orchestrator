/**
 * REACT QUERY PROVIDER
 * 
 * Client-side provider for React Query with optimized defaults.
 */

"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState, type ReactNode } from "react";

interface ProvidersProps {
    children: ReactNode;
}

/**
 * App-level providers wrapper
 */
export function Providers({ children }: ProvidersProps) {
    const [queryClient] = useState(
        () =>
            new QueryClient({
                defaultOptions: {
                    queries: {
                        // Stale time: 30 seconds
                        staleTime: 30 * 1000,
                        // Refetch on window focus in production
                        refetchOnWindowFocus: process.env.NODE_ENV === "production",
                        // Retry once on failure
                        retry: 1,
                        // Retry delay
                        retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
                    },
                    mutations: {
                        // Retry mutations once
                        retry: 1,
                    },
                },
            })
    );

    return (
        <QueryClientProvider client={queryClient}>
            {children}
        </QueryClientProvider>
    );
}
