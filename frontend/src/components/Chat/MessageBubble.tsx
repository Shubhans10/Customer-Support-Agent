import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { Message } from "../../types";

interface MessageBubbleProps {
    message: Message;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
    const isUser = message.role === "user";
    const time = new Date(message.timestamp).toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
    });

    if (!message.content && !message.charts?.length && message.role === "assistant") {
        return null;
    }

    return (
        <div className={`message-row ${message.role}`}>
            <div className={`message-avatar ${message.role}`}>
                {isUser ? "👤" : "🏭"}
            </div>
            <div className={`message-bubble ${message.role}`}>
                {isUser ? (
                    <div>{message.content}</div>
                ) : (
                    <div className="markdown-content">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {message.content}
                        </ReactMarkdown>
                    </div>
                )}
                {message.charts && message.charts.length > 0 && (
                    <div className="chart-container">
                        {message.charts.map((chart, i) => (
                            <div key={i} className="chart-wrapper">
                                <img
                                    src={`data:image/png;base64,${chart.image_base64}`}
                                    alt={chart.summary || "Performance Chart"}
                                    className="chart-image"
                                />
                                {chart.summary && (
                                    <div className="chart-caption">{chart.summary}</div>
                                )}
                            </div>
                        ))}
                    </div>
                )}
                <div className="message-time">{time}</div>
            </div>
        </div>
    );
};
