import { useState, useRef, useEffect } from "react";
import type { SkillInfo } from "../../types";

interface SkillCardProps {
    skill: SkillInfo;
    onExampleClick?: (query: string) => void;
}

export const SkillCard: React.FC<SkillCardProps> = ({ skill, onExampleClick }) => {
    const [showTooltip, setShowTooltip] = useState(false);
    const [tooltipPosition, setTooltipPosition] = useState<"bottom" | "top">("bottom");
    const cardRef = useRef<HTMLDivElement>(null);
    const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

    const handleMouseEnter = () => {
        timeoutRef.current = setTimeout(() => {
            // Determine if tooltip should go up or down
            if (cardRef.current) {
                const rect = cardRef.current.getBoundingClientRect();
                const spaceBelow = window.innerHeight - rect.bottom;
                setTooltipPosition(spaceBelow < 280 ? "top" : "bottom");
            }
            setShowTooltip(true);
        }, 300);
    };

    const handleMouseLeave = () => {
        if (timeoutRef.current) {
            clearTimeout(timeoutRef.current);
            timeoutRef.current = null;
        }
        setShowTooltip(false);
    };

    useEffect(() => {
        return () => {
            if (timeoutRef.current) clearTimeout(timeoutRef.current);
        };
    }, []);

    return (
        <div
            className="skill-card"
            ref={cardRef}
            onMouseEnter={handleMouseEnter}
            onMouseLeave={handleMouseLeave}
        >
            <div className="skill-card-icon">{skill.icon}</div>
            <div className="skill-card-info">
                <div className="skill-card-name">{skill.name}</div>
                <div className="skill-card-desc">{skill.description}</div>
            </div>

            {showTooltip && (skill.details || skill.examples) && (
                <div className={`skill-tooltip ${tooltipPosition}`}>
                    <div className="skill-tooltip-arrow" />
                    <div className="skill-tooltip-header">
                        <span className="skill-tooltip-icon">{skill.icon}</span>
                        <span className="skill-tooltip-title">{skill.name}</span>
                    </div>

                    {skill.details && (
                        <div className="skill-tooltip-details">{skill.details}</div>
                    )}

                    {skill.examples && skill.examples.length > 0 && (
                        <div className="skill-tooltip-examples">
                            <div className="skill-tooltip-examples-label">Try asking:</div>
                            {skill.examples.map((example, i) => (
                                <div
                                    key={i}
                                    className="skill-tooltip-example"
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        onExampleClick?.(example);
                                        setShowTooltip(false);
                                    }}
                                >
                                    <span className="skill-tooltip-example-icon">→</span>
                                    {example}
                                </div>
                            ))}
                        </div>
                    )}

                    {skill.data_source && (
                        <div className="skill-tooltip-source">
                            <span className="skill-tooltip-source-label">Data:</span>{" "}
                            {skill.data_source}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};
