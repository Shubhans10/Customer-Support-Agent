import type { SkillStep as SkillStepType, PlanStep } from "../../types";
import { SkillStep } from "./SkillStep.tsx";

interface SkillTracePanelProps {
    steps: SkillStepType[];
    planSteps?: PlanStep[];
}

const SKILL_ICONS: Record<string, string> = {
    work_order_lookup: "📋",
    equipment_status: "🔧",
    defect_report: "🔍",
    knowledge_base_search: "📖",
    escalate_to_engineer: "🙋",
    generate_chart: "📊",
};

export const SkillTracePanel: React.FC<SkillTracePanelProps> = ({ steps, planSteps = [] }) => {
    return (
        <div className="skill-trace-panel">
            <div className="trace-header">
                <span className="trace-header-icon">⚡</span>
                <h2>Skill Execution Trace</h2>
            </div>
            <div className="trace-content">
                {steps.length === 0 && planSteps.length === 0 ? (
                    <div className="trace-empty">
                        <div className="trace-empty-icon">🔍</div>
                        <p>
                            Send a message to see the agent's skills in action. Each skill
                            invocation will appear here in real-time with animated steps.
                        </p>
                    </div>
                ) : (
                    <>
                        {planSteps.length > 0 && (
                            <div className="plan-section">
                                <div className="plan-header">
                                    <span className="plan-header-icon">🗺️</span>
                                    <span className="plan-header-title">Execution Plan</span>
                                </div>
                                <div className="plan-steps">
                                    {planSteps.map((ps, i) => {
                                        const isCompleted = steps.some(
                                            (s) => s.skillName === ps.skill && s.status === "completed"
                                        );
                                        const isRunning = steps.some(
                                            (s) => s.skillName === ps.skill && s.status === "running"
                                        );
                                        return (
                                            <div
                                                key={i}
                                                className={`plan-step ${isCompleted ? "completed" : isRunning ? "running" : "pending"}`}
                                            >
                                                <div className="plan-step-number">{i + 1}</div>
                                                <div className="plan-step-content">
                                                    <div className="plan-step-skill">
                                                        <span>{SKILL_ICONS[ps.skill] || "🔧"}</span>
                                                        <span>{ps.skill.replace(/_/g, " ")}</span>
                                                    </div>
                                                    <div className="plan-step-reason">{ps.reason}</div>
                                                </div>
                                                <div className="plan-step-indicator">
                                                    {isCompleted ? "✓" : isRunning ? (
                                                        <div className="skill-step-spinner" />
                                                    ) : ""}
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        )}
                        <div className="skill-timeline">
                            {steps.map((step, index) => (
                                <SkillStep key={step.id} step={step} index={index} />
                            ))}
                        </div>
                    </>
                )}
            </div>
        </div>
    );
};
