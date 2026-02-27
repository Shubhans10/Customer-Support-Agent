import type { SkillStep as SkillStepType } from "../../types";
import { SkillStep } from "./SkillStep.tsx";

interface SkillTracePanelProps {
    steps: SkillStepType[];
}

export const SkillTracePanel: React.FC<SkillTracePanelProps> = ({ steps }) => {
    return (
        <div className="skill-trace-panel">
            <div className="trace-header">
                <span className="trace-header-icon">⚡</span>
                <h2>Skill Execution Trace</h2>
            </div>
            <div className="trace-content">
                {steps.length === 0 ? (
                    <div className="trace-empty">
                        <div className="trace-empty-icon">🔍</div>
                        <p>
                            Send a message to see the agent's skills in action. Each skill
                            invocation will appear here in real-time with animated steps.
                        </p>
                    </div>
                ) : (
                    <div className="skill-timeline">
                        {steps.map((step, index) => (
                            <SkillStep key={step.id} step={step} index={index} />
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};
