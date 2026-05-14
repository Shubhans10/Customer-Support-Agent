import { useEffect, useState } from "react";
import type { ComparisonSummary } from "../../types";

interface TokenCounterProps {
    summary: ComparisonSummary;
}

function AnimatedNumber({ value, duration = 1200 }: { value: number; duration?: number }) {
    const [display, setDisplay] = useState(0);

    useEffect(() => {
        if (value === 0) { setDisplay(0); return; }
        const start = performance.now();
        const startVal = 0;

        const animate = (now: number) => {
            const elapsed = now - start;
            const progress = Math.min(elapsed / duration, 1);
            // Ease out cubic
            const eased = 1 - Math.pow(1 - progress, 3);
            setDisplay(Math.round(startVal + (value - startVal) * eased));
            if (progress < 1) requestAnimationFrame(animate);
        };
        requestAnimationFrame(animate);
    }, [value, duration]);

    return <span className="animated-number">{display.toLocaleString()}</span>;
}

function CostDisplay({ cost }: { cost: number }) {
    return (
        <span className="cost-value">
            ${cost < 0.01 ? cost.toFixed(4) : cost.toFixed(3)}
        </span>
    );
}

export const TokenCounter: React.FC<TokenCounterProps> = ({ summary }) => {
    const maxTokens = Math.max(summary.skills.total_tokens, summary.agent.total_tokens, 1);
    const skillsPct = (summary.skills.total_tokens / maxTokens) * 100;
    const agentPct = (summary.agent.total_tokens / maxTokens) * 100;

    const tokenDiff = summary.skills.total_tokens - summary.agent.total_tokens;
    const tokenDiffPct = Math.abs(summary.token_diff_pct);
    const agentIsCheaper = tokenDiff > 0;

    const timeDiff = summary.skills.time_ms - summary.agent.time_ms;
    const agentIsFaster = timeDiff > 0;

    return (
        <div className="token-counter">
            {/* Summary Badges */}
            <div className="token-badges">
                <div className={`token-badge ${agentIsCheaper ? "positive" : "neutral"}`}>
                    <span className="token-badge-icon">{agentIsCheaper ? "📉" : "📈"}</span>
                    <span>
                        Agent used <strong>{tokenDiffPct.toFixed(0)}%</strong> {agentIsCheaper ? "fewer" : "more"} tokens
                    </span>
                </div>
                <div className={`token-badge ${agentIsFaster ? "positive" : "neutral"}`}>
                    <span className="token-badge-icon">⏱️</span>
                    <span>
                        Agent was <strong>{Math.abs(timeDiff / 1000).toFixed(1)}s</strong> {agentIsFaster ? "faster" : "slower"}
                    </span>
                </div>
                <div className="token-badge info">
                    <span className="token-badge-icon">🔧</span>
                    <span>
                        Skills used <strong>{summary.skills.skills_used}</strong> tool{summary.skills.skills_used !== 1 ? "s" : ""}
                    </span>
                </div>
                <div className="token-badge info">
                    <span className="token-badge-icon">🧠</span>
                    <span>Model: <strong>{summary.model}</strong></span>
                </div>
            </div>

            {/* Visual Bar Comparison */}
            <div className="token-bars">
                <div className="token-bar-row">
                    <div className="token-bar-label">
                        <span className="token-bar-method skills-text">⚡ Skills</span>
                        <span className="token-bar-count">
                            <AnimatedNumber value={summary.skills.total_tokens} />
                        </span>
                    </div>
                    <div className="token-bar-track">
                        <div
                            className="token-bar-fill skills-fill"
                            style={{ width: `${skillsPct}%` }}
                        >
                            <div className="token-bar-shimmer" />
                        </div>
                    </div>
                    <div className="token-bar-cost">
                        <CostDisplay cost={summary.skills.estimated_cost} />
                    </div>
                </div>

                <div className="token-bar-row">
                    <div className="token-bar-label">
                        <span className="token-bar-method agent-text">🤖 Agent</span>
                        <span className="token-bar-count">
                            <AnimatedNumber value={summary.agent.total_tokens} />
                        </span>
                    </div>
                    <div className="token-bar-track">
                        <div
                            className="token-bar-fill agent-fill"
                            style={{ width: `${agentPct}%` }}
                        >
                            <div className="token-bar-shimmer" />
                        </div>
                    </div>
                    <div className="token-bar-cost">
                        <CostDisplay cost={summary.agent.estimated_cost} />
                    </div>
                </div>
            </div>

            {/* Detailed Node Breakdown */}
            <div className="token-breakdown">
                <div className="token-breakdown-header">
                    <span>Per-Node Token Breakdown</span>
                </div>
                <table className="token-table">
                    <thead>
                        <tr>
                            <th>Node</th>
                            <th>Method</th>
                            <th>Prompt</th>
                            <th>Completion</th>
                            <th>Total</th>
                        </tr>
                    </thead>
                    <tbody>
                        {summary.skills.nodes.map((node, i) => (
                            <tr key={`skills-${i}`} className="skills-row">
                                <td>
                                    <span className="node-name">{node.node.replace(/_/g, " ")}</span>
                                </td>
                                <td><span className="method-chip skills-chip">Skills</span></td>
                                <td className="num-cell">{node.prompt_tokens.toLocaleString()}</td>
                                <td className="num-cell">{node.completion_tokens.toLocaleString()}</td>
                                <td className="num-cell total-cell">{node.total_tokens.toLocaleString()}</td>
                            </tr>
                        ))}
                        <tr className="total-row skills-total-row">
                            <td><strong>Skills Total</strong></td>
                            <td><span className="method-chip skills-chip">⚡</span></td>
                            <td className="num-cell"><strong>{summary.skills.prompt_tokens.toLocaleString()}</strong></td>
                            <td className="num-cell"><strong>{summary.skills.completion_tokens.toLocaleString()}</strong></td>
                            <td className="num-cell total-cell">
                                <strong>{summary.skills.total_tokens.toLocaleString()}</strong>
                            </td>
                        </tr>
                        <tr className="divider-row"><td colSpan={5}></td></tr>
                        {summary.agent.nodes.map((node, i) => (
                            <tr key={`agent-${i}`} className="agent-row">
                                <td>
                                    <span className="node-name">{node.node.replace(/_/g, " ")}</span>
                                </td>
                                <td><span className="method-chip agent-chip">Agent</span></td>
                                <td className="num-cell">{node.prompt_tokens.toLocaleString()}</td>
                                <td className="num-cell">{node.completion_tokens.toLocaleString()}</td>
                                <td className="num-cell total-cell">{node.total_tokens.toLocaleString()}</td>
                            </tr>
                        ))}
                        <tr className="total-row agent-total-row">
                            <td><strong>Agent Total</strong></td>
                            <td><span className="method-chip agent-chip">🤖</span></td>
                            <td className="num-cell"><strong>{summary.agent.prompt_tokens.toLocaleString()}</strong></td>
                            <td className="num-cell"><strong>{summary.agent.completion_tokens.toLocaleString()}</strong></td>
                            <td className="num-cell total-cell">
                                <strong>{summary.agent.total_tokens.toLocaleString()}</strong>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>

            {/* Time Comparison */}
            <div className="time-comparison">
                <div className="time-card skills-time">
                    <div className="time-card-label">⚡ Skills Time</div>
                    <div className="time-card-value">{(summary.skills.time_ms / 1000).toFixed(2)}s</div>
                    <div className="time-card-cost">
                        Cost: <CostDisplay cost={summary.skills.estimated_cost} />
                    </div>
                </div>
                <div className="time-vs">vs</div>
                <div className="time-card agent-time">
                    <div className="time-card-label">🤖 Agent Time</div>
                    <div className="time-card-value">{(summary.agent.time_ms / 1000).toFixed(2)}s</div>
                    <div className="time-card-cost">
                        Cost: <CostDisplay cost={summary.agent.estimated_cost} />
                    </div>
                </div>
            </div>
        </div>
    );
};
