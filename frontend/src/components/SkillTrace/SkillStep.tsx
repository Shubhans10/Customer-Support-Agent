import { useState } from "react";
import type { SkillStep as SkillStepType } from "../../types";

interface SkillStepProps {
    step: SkillStepType;
    index: number;
}

export const SkillStep: React.FC<SkillStepProps> = ({ step, index }) => {
    const [expanded, setExpanded] = useState(false);

    const duration =
        step.endTimestamp && step.timestamp
            ? (
                (new Date(step.endTimestamp).getTime() -
                    new Date(step.timestamp).getTime()) /
                1000
            ).toFixed(1)
            : null;

    return (
        <div
            className="skill-step"
            style={{ animationDelay: `${index * 100}ms` }}
        >
            <div className={`skill-step-dot ${step.status}`} />
            <div
                className="skill-step-card"
                onClick={() => setExpanded(!expanded)}
            >
                <div className="skill-step-header">
                    <span className="skill-step-icon">{step.icon}</span>
                    <span className="skill-step-name">{step.displayName}</span>
                    {step.status === "running" ? (
                        <div className="skill-step-spinner" />
                    ) : step.status === "completed" ? (
                        <span className="skill-step-check">✓</span>
                    ) : null}
                    <span className={`skill-step-status ${step.status}`}>
                        {step.status}
                    </span>
                </div>

                {step.input && (
                    <div className="skill-step-input">
                        <div className="skill-step-input-label">Input</div>
                        {step.input}
                    </div>
                )}

                {expanded && step.output && (
                    <div className="skill-step-output">
                        <div className="skill-step-output-label">Output</div>
                        {JSON.stringify(step.output, null, 2)}
                    </div>
                )}

                {duration && (
                    <div className="skill-step-duration">Completed in {duration}s</div>
                )}
            </div>
        </div>
    );
};
