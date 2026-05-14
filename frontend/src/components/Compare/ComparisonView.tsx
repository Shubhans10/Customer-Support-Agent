import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { ChatInput } from "../Chat/ChatInput";
import { TokenCounter } from "./TokenCounter";
import type { MethodResult, ComparisonSummary } from "../../types";

interface ComparisonViewProps {
    skillsResult: MethodResult | null;
    agentResult: MethodResult | null;
    summary: ComparisonSummary | null;
    isLoading: boolean;
    error: string | null;
    onSend: (message: string) => void;
}

const SKILL_ICONS: Record<string, string> = {
    work_order_lookup: "📋",
    equipment_status: "🔧",
    defect_report: "🔍",
    knowledge_base_search: "📖",
    escalate_to_engineer: "🙋",
    generate_chart: "📊",
};

export const ComparisonView: React.FC<ComparisonViewProps> = ({
    skillsResult,
    agentResult,
    summary,
    isLoading,
    error,
    onSend,
}) => {
    const [showTokens, setShowTokens] = useState(true);
    const hasResults = skillsResult || agentResult;

    return (
        <div className="comparison-view">
            {error && (
                <div className="error-banner">⚠️ {error}</div>
            )}

            {!hasResults && !isLoading && (
                <div className="comparison-empty">
                    <div className="comparison-empty-icon">⚔️</div>
                    <h2>Skills vs Agent Comparison</h2>
                    <p>
                        Send a message to see both approaches side by side.
                        The <strong>Skills</strong> side uses real tools and data,
                        while the <strong>Agent</strong> side relies purely on LLM reasoning.
                    </p>
                    <div className="comparison-empty-badges">
                        <div className="method-badge skills-badge">⚡ Skills — Real Data</div>
                        <span className="vs-label">VS</span>
                        <div className="method-badge agent-badge">🤖 Agent — LLM Only</div>
                    </div>
                </div>
            )}

            {isLoading && !hasResults && (
                <div className="comparison-loading">
                    <div className="comparison-loading-spinner" />
                    <div className="comparison-loading-text">
                        Running both pipelines...
                    </div>
                    <div className="comparison-loading-sub">
                        Skills (with tools) and Agent (pure LLM) executing concurrently
                    </div>
                </div>
            )}

            {hasResults && (
                <>
                    <div className="comparison-split">
                        {/* Skills Side */}
                        <div className="comparison-column skills-column">
                            <div className="column-header skills-header">
                                <div className="column-header-badge">
                                    <span className="column-badge-dot skills-dot" />
                                    <span className="column-badge-label">⚡ Skills</span>
                                </div>
                                {skillsResult && (
                                    <div className="column-header-meta">
                                        <span className="column-meta-time">{(skillsResult.timeMs / 1000).toFixed(1)}s</span>
                                        <span className="column-meta-tokens">{skillsResult.tokenUsage.total_tokens.toLocaleString()} tokens</span>
                                    </div>
                                )}
                            </div>

                            <div className="column-content">
                                {skillsResult ? (
                                    <>
                                        {/* Plan Steps */}
                                        {skillsResult.planSteps.length > 0 && (
                                            <div className="compare-plan">
                                                <div className="compare-plan-label">
                                                    🗺️ Execution Plan
                                                </div>
                                                <div className="compare-plan-steps">
                                                    {skillsResult.planSteps.map((ps, i) => (
                                                        <div key={i} className="compare-plan-step">
                                                            <span className="compare-plan-num">{i + 1}</span>
                                                            <span className="compare-plan-icon">
                                                                {SKILL_ICONS[ps.skill] || "🔧"}
                                                            </span>
                                                            <span className="compare-plan-skill">
                                                                {ps.skill.replace(/_/g, " ")}
                                                            </span>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        )}

                                        {/* Skills Used */}
                                        {skillsResult.skillEvents.length > 0 && (
                                            <div className="compare-skills-used">
                                                {skillsResult.skillEvents
                                                    .filter(e => e.type === "result")
                                                    .map((e, i) => (
                                                        <div key={i} className="compare-skill-chip">
                                                            <span>{e.icon}</span>
                                                            <span>{e.display_name}</span>
                                                            <span className="compare-skill-check">✓</span>
                                                        </div>
                                                    ))
                                                }
                                            </div>
                                        )}

                                        {/* Response */}
                                        <div className="compare-response">
                                            <div className="compare-response-label">Response</div>
                                            <div className="markdown-content">
                                                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                                    {skillsResult.content}
                                                </ReactMarkdown>
                                            </div>
                                        </div>
                                    </>
                                ) : (
                                    <div className="column-loading">
                                        <div className="skill-step-spinner" />
                                        <span>Running skills pipeline...</span>
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Divider */}
                        <div className="comparison-divider">
                            <div className="comparison-divider-line" />
                            <div className="comparison-divider-badge">VS</div>
                            <div className="comparison-divider-line" />
                        </div>

                        {/* Agent Side */}
                        <div className="comparison-column agent-column">
                            <div className="column-header agent-header">
                                <div className="column-header-badge">
                                    <span className="column-badge-dot agent-dot" />
                                    <span className="column-badge-label">🤖 Agent</span>
                                </div>
                                {agentResult && (
                                    <div className="column-header-meta">
                                        <span className="column-meta-time">{(agentResult.timeMs / 1000).toFixed(1)}s</span>
                                        <span className="column-meta-tokens">{agentResult.tokenUsage.total_tokens.toLocaleString()} tokens</span>
                                    </div>
                                )}
                            </div>

                            <div className="column-content">
                                {agentResult ? (
                                    <div className="compare-response">
                                        <div className="compare-response-label">Response (LLM Only — No Tools)</div>
                                        <div className="markdown-content">
                                            <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                                {agentResult.content}
                                            </ReactMarkdown>
                                        </div>
                                    </div>
                                ) : (
                                    <div className="column-loading">
                                        <div className="skill-step-spinner" />
                                        <span>Running agent pipeline...</span>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Token Counter Dashboard */}
                    {summary && (
                        <div className="token-counter-section">
                            <button
                                className="token-counter-toggle"
                                onClick={() => setShowTokens(!showTokens)}
                                id="token-counter-toggle"
                            >
                                <span>📊 Token Usage Comparison</span>
                                <span className={`toggle-chevron ${showTokens ? "open" : ""}`}>▼</span>
                            </button>
                            {showTokens && <TokenCounter summary={summary} />}
                        </div>
                    )}
                </>
            )}

            <ChatInput onSend={onSend} isLoading={isLoading} />
        </div>
    );
};
