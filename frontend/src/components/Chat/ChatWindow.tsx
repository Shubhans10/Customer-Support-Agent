import { useRef, useEffect } from "react";
import type { Message } from "../../types";
import { MessageBubble } from "./MessageBubble.tsx";

interface ChatWindowProps {
    messages: Message[];
    isLoading: boolean;
}

export const ChatWindow: React.FC<ChatWindowProps> = ({ messages, isLoading }) => {
    const bottomRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    if (messages.length === 0) {
        return (
            <div className="chat-messages">
                <div className="chat-empty">
                    <div className="chat-empty-icon">🏭</div>
                    <h2>How can I assist you today?</h2>
                    <p>
                        I'm your AMM operations assistant. Ask me about work orders,
                        equipment status, quality reports, or safety procedures. Watch
                        the skill trace panel to see my reasoning in real-time!
                    </p>
                </div>
            </div>
        );
    }

    return (
        <div className="chat-messages">
            {messages.map((msg) => (
                <MessageBubble key={msg.id} message={msg} />
            ))}
            {isLoading && messages[messages.length - 1]?.content === "" && (
                <div className="message-row">
                    <div className="message-avatar agent">🤖</div>
                    <div className="message-bubble agent">
                        <div className="typing-indicator">
                            <div className="typing-dot"></div>
                            <div className="typing-dot"></div>
                            <div className="typing-dot"></div>
                        </div>
                    </div>
                </div>
            )}
            <div ref={bottomRef} />
        </div>
    );
};
