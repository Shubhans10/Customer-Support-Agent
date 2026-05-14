export interface ChartData {
    image_base64: string;
    chart_type: string;
    summary: string;
}

export interface Message {
    id: string;
    role: "user" | "assistant";
    content: string;
    timestamp: string;
    charts?: ChartData[];
}

export type SkillStatus = "running" | "completed" | "error";

export interface SkillStep {
    id: string;
    skillName: string;
    displayName: string;
    icon: string;
    status: SkillStatus;
    input?: string;
    output?: Record<string, unknown>;
    timestamp: string;
    endTimestamp?: string;
}

export interface PlanStep {
    skill: string;
    reason: string;
}

export interface SkillInfo {
    name: string;
    description: string;
    icon: string;
    details?: string;
    examples?: string[];
    data_source?: string;
}

export interface ChatState {
    messages: Message[];
    skillSteps: SkillStep[];
    planSteps: PlanStep[];
    isLoading: boolean;
    conversationId: string;
    error: string | null;
}

// ═══════════════════════════════════════════════════════
// Comparison Mode Types
// ═══════════════════════════════════════════════════════

export interface TokenUsageNode {
    node: string;
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
}

export interface TokenUsage {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
    nodes: TokenUsageNode[];
}

export interface SkillEvent {
    type: "start" | "result";
    skill_name: string;
    display_name: string;
    icon: string;
}

export interface MethodResult {
    content: string;
    planSteps: PlanStep[];
    skillEvents: SkillEvent[];
    tokenUsage: TokenUsage;
    timeMs: number;
    estimatedCost: number;
}

export interface ComparisonSummary {
    skills: {
        total_tokens: number;
        prompt_tokens: number;
        completion_tokens: number;
        time_ms: number;
        estimated_cost: number;
        skills_used: number;
        nodes: TokenUsageNode[];
    };
    agent: {
        total_tokens: number;
        prompt_tokens: number;
        completion_tokens: number;
        time_ms: number;
        estimated_cost: number;
        nodes: TokenUsageNode[];
    };
    token_diff_pct: number;
    time_diff_pct: number;
    model: string;
}

export interface CompareState {
    skillsResult: MethodResult | null;
    agentResult: MethodResult | null;
    summary: ComparisonSummary | null;
    isLoading: boolean;
    error: string | null;
}
