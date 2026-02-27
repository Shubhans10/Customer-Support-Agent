export interface Message {
    id: string;
    role: "user" | "assistant";
    content: string;
    timestamp: string;
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

export interface SkillInfo {
    name: string;
    description: string;
    icon: string;
}

export interface ChatState {
    messages: Message[];
    skillSteps: SkillStep[];
    isLoading: boolean;
    conversationId: string;
    error: string | null;
}
