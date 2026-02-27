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

    if (!message.content && message.role === "assistant") {
        return null;
    }

    return (
        <div className={`message-row ${message.role}`}>
            <div className={`message-avatar ${message.role}`}>
                {isUser ? "👤" : "🤖"}
            </div>
            <div className={`message-bubble ${message.role}`}>
                <div>{message.content}</div>
                <div className="message-time">{time}</div>
            </div>
        </div>
    );
};
