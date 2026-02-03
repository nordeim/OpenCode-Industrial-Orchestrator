/**
 * WEBSOCKET PROVIDER
 * 
 * React context provider for WebSocket connections.
 * Features:
 * - Auto-reconnection with exponential backoff
 * - Room subscription
 * - Event handlers
 * - Connection state tracking
 */

"use client";

import React, {
    createContext,
    useContext,
    useEffect,
    useRef,
    useState,
    useCallback,
    type ReactNode,
} from "react";

// Configuration
const WS_BASE_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";

// Types
export type ConnectionStatus = "connecting" | "connected" | "disconnected" | "error";

export interface WebSocketMessage {
    type: string;
    payload: Record<string, unknown>;
    timestamp?: string;
}

export interface WebSocketContextValue {
    status: ConnectionStatus;
    clientId: string | null;
    connect: (endpoint: string) => void;
    disconnect: () => void;
    subscribe: (eventType: string, handler: (payload: unknown) => void) => () => void;
    sendMessage: (message: WebSocketMessage) => void;
}

// Context
const WebSocketContext = createContext<WebSocketContextValue | null>(null);

// Provider props
interface WebSocketProviderProps {
    children: ReactNode;
    defaultEndpoint?: string;
    autoConnect?: boolean;
}

/**
 * WebSocket Provider Component
 */
export function WebSocketProvider({
    children,
    defaultEndpoint = "/ws/system",
    autoConnect = true,
}: WebSocketProviderProps) {
    const wsRef = useRef<WebSocket | null>(null);
    const handlersRef = useRef<Map<string, Set<(payload: unknown) => void>>>(new Map());
    const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
    const reconnectAttempts = useRef(0);

    const [status, setStatus] = useState<ConnectionStatus>("disconnected");
    const [clientId, setClientId] = useState<string | null>(null);

    // Keep track of the current endpoint to reconnect to
    const activeEndpointRef = useRef(defaultEndpoint);

    // Connect function
    const connect = useCallback((endpoint: string) => {
        // Clean up existing connection
        if (wsRef.current) {
            wsRef.current.close();
        }

        activeEndpointRef.current = endpoint;
        setStatus("connecting");
        const url = `${WS_BASE_URL}${endpoint}`;

        try {
            const ws = new WebSocket(url);
            wsRef.current = ws;

            ws.onopen = () => {
                setStatus("connected");
                reconnectAttempts.current = 0;
                console.log("[WS] Connected to", url);
            };

            ws.onmessage = (event) => {
                try {
                    const message: WebSocketMessage = JSON.parse(event.data);

                    // Handle connection established message
                    if (message.type === "connection.established") {
                        setClientId((message.payload as { client_id: string }).client_id);
                    }

                    // Dispatch to registered handlers
                    const handlers = handlersRef.current.get(message.type);
                    if (handlers) {
                        handlers.forEach((handler) => handler(message.payload));
                    }

                    // Also dispatch to wildcard handlers
                    const wildcardHandlers = handlersRef.current.get("*");
                    if (wildcardHandlers) {
                        wildcardHandlers.forEach((handler) => handler(message));
                    }
                } catch (err) {
                    console.error("[WS] Failed to parse message:", err);
                }
            };

            ws.onerror = (error) => {
                console.error("[WS] Error:", error);
                setStatus("error");
            };

            ws.onclose = (event) => {
                setStatus("disconnected");
                setClientId(null);
                console.log("[WS] Disconnected:", event.code, event.reason);
                
                // Trigger reconnection via effect by updating a trigger state if needed
                // or handle it here if we can avoid the circular dependency.
                // We will handle it by checking the ref in a separate useEffect or timeout that calls a stable ref.
            };
        } catch (err) {
            console.error("[WS] Failed to connect:", err);
            setStatus("error");
        }
    }, []);

    // Reconnection Logic
    // We use a ref to the connect function to allow calling it from the timeout
    // without adding it to the dependency array or causing circular issues.
    const connectRef = useRef(connect);
    
    // Update ref when connect changes
    useEffect(() => {
        connectRef.current = connect;
    }, [connect]);

    useEffect(() => {
        // If disconnected and should auto-reconnect
        if (status === "disconnected" && autoConnect && reconnectAttempts.current < 5) {
             const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
             
             // Only schedule if not already scheduled (though we clear on disconnect usually)
             if (!reconnectTimeoutRef.current) {
                 console.log(`[WS] Scheduling reconnect in ${delay}ms (attempt ${reconnectAttempts.current + 1})`);
                 reconnectTimeoutRef.current = setTimeout(() => {
                     reconnectAttempts.current++;
                     connectRef.current(activeEndpointRef.current);
                     reconnectTimeoutRef.current = null;
                 }, delay);
             }
        }
    }, [status, autoConnect]);

    // Disconnect from WebSocket
    const disconnect = useCallback(() => {
        if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
            reconnectTimeoutRef.current = null;
        }
        reconnectAttempts.current = 5; // Prevent auto-reconnect

        if (wsRef.current) {
            wsRef.current.close();
            wsRef.current = null;
        }

        setStatus("disconnected");
        setClientId(null);
    }, []);

    // Subscribe to events
    const subscribe = useCallback(
        (eventType: string, handler: (payload: unknown) => void) => {
            if (!handlersRef.current.has(eventType)) {
                handlersRef.current.set(eventType, new Set());
            }
            handlersRef.current.get(eventType)!.add(handler);

            // Return unsubscribe function
            return () => {
                handlersRef.current.get(eventType)?.delete(handler);
            };
        },
        []
    );

    // Send message
    const sendMessage = useCallback((message: WebSocketMessage) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify(message));
        } else {
            console.warn("[WS] Cannot send message - not connected");
        }
    }, []);

    // Auto-connect on mount
    useEffect(() => {
        let timeoutId: NodeJS.Timeout;
        if (autoConnect) {
            // Defer connection to avoid synchronous state update in effect
            timeoutId = setTimeout(() => {
                connect(defaultEndpoint);
            }, 0);
        }

        return () => {
            if (timeoutId) clearTimeout(timeoutId);
            disconnect();
        };
    }, [autoConnect, defaultEndpoint, connect, disconnect]);

    const value: WebSocketContextValue = {
        status,
        clientId,
        connect,
        disconnect,
        subscribe,
        sendMessage,
    };

    return (
        <WebSocketContext.Provider value={value}>
            {children}
        </WebSocketContext.Provider>
    );
}

/**
 * Hook to use WebSocket context
 */
export function useWebSocket() {
    const context = useContext(WebSocketContext);

    if (!context) {
        throw new Error("useWebSocket must be used within a WebSocketProvider");
    }

    return context;
}

/**
 * Hook to subscribe to specific WebSocket events
 */
export function useWebSocketEvent<T = unknown>(
    eventType: string,
    handler: (payload: T) => void
) {
    const { subscribe } = useWebSocket();

    useEffect(() => {
        const unsubscribe = subscribe(eventType, handler as (payload: unknown) => void);
        return unsubscribe;
    }, [eventType, handler, subscribe]);
}

/**
 * Hook for session-specific WebSocket events
 */
export function useSessionEvents(
    sessionId: string,
    options?: {
        onStatusChanged?: (status: unknown) => void;
        onCheckpointCreated?: (checkpoint: unknown) => void;
        onMetricsUpdated?: (metrics: unknown) => void;
    }
) {
    const { connect, status, subscribe } = useWebSocket();

    useEffect(() => {
        if (sessionId) {
            connect(`/ws/sessions/${sessionId}`);
        }
    }, [sessionId, connect]);

    useEffect(() => {
        const unsubscribers: (() => void)[] = [];

        if (options?.onStatusChanged) {
            unsubscribers.push(
                subscribe("session.status_changed", options.onStatusChanged)
            );
        }

        if (options?.onCheckpointCreated) {
            unsubscribers.push(
                subscribe("session.checkpoint_created", options.onCheckpointCreated)
            );
        }

        if (options?.onMetricsUpdated) {
            unsubscribers.push(
                subscribe("session.metrics_updated", options.onMetricsUpdated)
            );
        }

        return () => {
            unsubscribers.forEach((unsub) => unsub());
        };
    }, [subscribe, options]);

    return { status };
}