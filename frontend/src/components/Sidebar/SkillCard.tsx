import type { SkillInfo } from "../../types";

interface SkillCardProps {
    skill: SkillInfo;
}

export const SkillCard: React.FC<SkillCardProps> = ({ skill }) => {
    return (
        <div className="skill-card">
            <div className="skill-card-icon">{skill.icon}</div>
            <div className="skill-card-info">
                <div className="skill-card-name">{skill.name}</div>
                <div className="skill-card-desc">{skill.description}</div>
            </div>
        </div>
    );
};
