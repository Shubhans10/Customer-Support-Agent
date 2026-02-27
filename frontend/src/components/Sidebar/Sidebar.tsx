import type { SkillInfo } from "../../types";
import { SkillCard } from "./SkillCard.tsx";

interface SidebarProps {
    skills: SkillInfo[];
    onSampleQuery: (query: string) => void;
}

const SAMPLE_QUERIES = [
    "What's the status of work order WO-2001?",
    "Is CNC-001 operational?",
    "Report a defect on WO-2003",
    "What are the PPE requirements?",
    "Show all in-progress work orders",
    "I need engineering support for a tooling issue",
];

export const Sidebar: React.FC<SidebarProps> = ({ skills, onSampleQuery }) => {
    return (
        <div className="sidebar">
            <div className="sidebar-header">
                <div className="sidebar-brand">
                    <div className="sidebar-brand-icon">🏭</div>
                    <h1>AMM Assist</h1>
                </div>
                <div className="sidebar-brand-subtitle">Advanced Manufacturing Operations</div>
            </div>

            <div className="sidebar-section">
                <div className="sidebar-section-title">Agent Skills</div>
                {skills.map((skill) => (
                    <SkillCard key={skill.name} skill={skill} />
                ))}
            </div>

            <div className="sidebar-section">
                <div className="sidebar-section-title">Try These Queries</div>
            </div>

            <div className="sample-queries">
                {SAMPLE_QUERIES.map((query, i) => (
                    <div
                        key={i}
                        className="sample-query"
                        onClick={() => onSampleQuery(query)}
                    >
                        {query}
                    </div>
                ))}
            </div>
        </div>
    );
};
