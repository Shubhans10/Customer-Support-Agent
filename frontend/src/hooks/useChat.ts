import { useState, useCallback, useRef } from "react";
import type { Message, SkillStep, ChatState } from "../types";
import { API_BASE_URL } from "../utils/api";

function generateId(): string {
    return `${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
}

export function useChat() {
    const [state, setState] = useState<ChatState>({
        messages: [],
        skillSteps: [],
        isLoading: false,
        conversationId: generateId(),
        error: null,
    });

    const abortRef = useRef<AbortController | null>(null);

    const sendMessage = useCallback(
        async (content: string) => {
            if (!content.trim() || state.isLoading) return;

            // Add user message
            const userMessage: Message = {
                id: generateId(),
                role: "user",
                content: content.trim(),
                timestamp: new Date().toISOString(),
            };

            setState((prev) => ({
                ...prev,
                messages: [...prev.messages, userMessage],
                skillSteps: [],
                isLoading: true,
                error: null,
            }));

            // Create assistant message placeholder
            const assistantId = generateId();
            const assistantMessage: Message = {
                id: assistantId,
                role: "assistant",
                content: "",
                timestamp: new Date().toISOString(),
            };

            setState((prev) => ({
                ...prev,
                messages: [...prev.messages, assistantMessage],
            }));

            try {
                abortRef.current = new AbortController();

                const response = await fetch(`${API_BASE_URL}/api/chat`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        message: content.trim(),
                        conversation_id: state.conversationId,
                    }),
                    signal: abortRef.current.signal,
                });

                if (!response.ok) throw new Error("Chat request failed");

                const reader = response.body?.getReader();
                if (!reader) throw new Error("No response body");

                const decoder = new TextDecoder();
                let buffer = "";

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    buffer += decoder.decode(value, { stream: true });
                    const lines = buffer.split("\n");
                    buffer = lines.pop() || "";

                    let currentEventType = "";

                    for (const line of lines) {
                        if (line.startsWith("event: ")) {
                            currentEventType = line.slice(7).trim();
                        } else if (line.startsWith("data: ") && currentEventType) {
                            try {
                                const data = JSON.parse(line.slice(6));
                                handleSSEEvent(currentEventType, data, assistantId);
                            } catch {
                                // Skip malformed JSON
                            }
                            currentEventType = "";
                        }
                    }
                }
            } catch (err) {
                if (err instanceof Error && err.name !== "AbortError") {
                    setState((prev) => ({
                        ...prev,
                        error: err instanceof Error ? err.message : "Unknown error",
                    }));
                }
            } finally {
                setState((prev) => ({ ...prev, isLoading: false }));
            }
        },
        [state.isLoading, state.conversationId]
    );

    const handleSSEEvent = useCallback(
        (eventType: string, data: Record<string, unknown>, assistantId: string) => {
            switch (eventType) {
                case "skill_start": {
                    const step: SkillStep = {
                        id: generateId(),
                        skillName: data.skill_name as string,
                        displayName: data.display_name as string,
                        icon: data.icon as string,
                        status: "running",
                        input: data.input as string,
                        timestamp: data.timestamp as string,
                    };
                    setState((prev) => ({
                        ...prev,
                        skillSteps: [...prev.skillSteps, step],
                    }));
                    break;
                }

                case "skill_result": {
                    setState((prev) => ({
                        ...prev,
                        skillSteps: prev.skillSteps.map((step) =>
                            step.skillName === (data.skill_name as string) &&
                                step.status === "running"
                                ? {
                                    ...step,
                                    status: "completed" as const,
                                    output: data.output as Record<string, unknown>,
                                    endTimestamp: data.timestamp as string,
                                }
                                : step
                        ),
                    }));
                    break;
                }

                case "message": {
                    setState((prev) => ({
                        ...prev,
                        messages: prev.messages.map((msg) =>
                            msg.id === assistantId
                                ? { ...msg, content: msg.content + (data.content as string) }
                                : msg
                        ),
                    }));
                    break;
                }

                case "error": {
                    setState((prev) => ({
                        ...prev,
                        error: data.message as string,
                    }));
                    break;
                }
            }
        },
        []
    );

    const clearChat = useCallback(() => {
        setState({
            messages: [],
            skillSteps: [],
            isLoading: false,
            conversationId: generateId(),
            error: null,
        });
    }, []);

    return {
        messages: state.messages,
        skillSteps: state.skillSteps,
        isLoading: state.isLoading,
        error: state.error,
        sendMessage,
        clearChat,
    };
}
