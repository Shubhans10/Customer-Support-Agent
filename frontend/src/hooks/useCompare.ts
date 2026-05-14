import { useState, useCallback } from "react";
import type { MethodResult, ComparisonSummary, CompareState, PlanStep, SkillEvent, TokenUsageNode } from "../types";
import { API_BASE_URL } from "../utils/api";

export function useCompare() {
    const [state, setState] = useState<CompareState>({
        skillsResult: null,
        agentResult: null,
        summary: null,
        isLoading: false,
        error: null,
    });

    const sendCompare = useCallback(
        async (content: string) => {
            if (!content.trim() || state.isLoading) return;

            setState({
                skillsResult: null,
                agentResult: null,
                summary: null,
                isLoading: true,
                error: null,
            });

            try {
                const response = await fetch(`${API_BASE_URL}/api/chat/compare`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ message: content.trim() }),
                });

                if (!response.ok) throw new Error("Compare request failed");

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
                                handleEvent(currentEventType, data);
                            } catch {
                                // Skip malformed JSON
                            }
                            currentEventType = "";
                        }
                    }
                }
            } catch (err) {
                setState((prev) => ({
                    ...prev,
                    error: err instanceof Error ? err.message : "Unknown error",
                }));
            } finally {
                setState((prev) => ({ ...prev, isLoading: false }));
            }
        },
        [state.isLoading]
    );

    const handleEvent = useCallback(
        (eventType: string, data: Record<string, unknown>) => {
            switch (eventType) {
                case "skills_result": {
                    const result: MethodResult = {
                        content: data.content as string,
                        planSteps: (data.plan_steps as PlanStep[]) || [],
                        skillEvents: (data.skill_events as SkillEvent[]) || [],
                        tokenUsage: {
                            prompt_tokens: (data.token_usage as Record<string, unknown>)?.prompt_tokens as number || 0,
                            completion_tokens: (data.token_usage as Record<string, unknown>)?.completion_tokens as number || 0,
                            total_tokens: (data.token_usage as Record<string, unknown>)?.total_tokens as number || 0,
                            nodes: ((data.token_usage as Record<string, unknown>)?.nodes as TokenUsageNode[]) || [],
                        },
                        timeMs: data.time_ms as number || 0,
                        estimatedCost: data.estimated_cost as number || 0,
                    };
                    setState((prev) => ({ ...prev, skillsResult: result }));
                    break;
                }

                case "agent_result": {
                    const result: MethodResult = {
                        content: data.content as string,
                        planSteps: [],
                        skillEvents: [],
                        tokenUsage: {
                            prompt_tokens: (data.token_usage as Record<string, unknown>)?.prompt_tokens as number || 0,
                            completion_tokens: (data.token_usage as Record<string, unknown>)?.completion_tokens as number || 0,
                            total_tokens: (data.token_usage as Record<string, unknown>)?.total_tokens as number || 0,
                            nodes: ((data.token_usage as Record<string, unknown>)?.nodes as TokenUsageNode[]) || [],
                        },
                        timeMs: data.time_ms as number || 0,
                        estimatedCost: data.estimated_cost as number || 0,
                    };
                    setState((prev) => ({ ...prev, agentResult: result }));
                    break;
                }

                case "comparison_summary": {
                    const summary: ComparisonSummary = {
                        skills: data.skills as ComparisonSummary["skills"],
                        agent: data.agent as ComparisonSummary["agent"],
                        token_diff_pct: data.token_diff_pct as number,
                        time_diff_pct: data.time_diff_pct as number,
                        model: data.model as string,
                    };
                    setState((prev) => ({ ...prev, summary }));
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

    const clearCompare = useCallback(() => {
        setState({
            skillsResult: null,
            agentResult: null,
            summary: null,
            isLoading: false,
            error: null,
        });
    }, []);

    return {
        skillsResult: state.skillsResult,
        agentResult: state.agentResult,
        summary: state.summary,
        isLoading: state.isLoading,
        error: state.error,
        sendCompare,
        clearCompare,
    };
}
