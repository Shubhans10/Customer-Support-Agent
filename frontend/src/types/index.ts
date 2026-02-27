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
}

export interface ChatState {
    messages: Message[];
    skillSteps: SkillStep[];
    planSteps: PlanStep[];
    isLoading: boolean;
    conversationId: string;
    error: string | null;
}
