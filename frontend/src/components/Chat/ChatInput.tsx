import { useState, useRef, useEffect } from "react";

interface ChatInputProps {
    onSend: (message: string) => void;
    isLoading: boolean;
}

export const ChatInput: React.FC<ChatInputProps> = ({ onSend, isLoading }) => {
    const [input, setInput] = useState("");
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    useEffect(() => {
        if (!isLoading && textareaRef.current) {
            textareaRef.current.focus();
        }
    }, [isLoading]);

    const handleSend = () => {
        if (input.trim() && !isLoading) {
            onSend(input.trim());
            setInput("");
            if (textareaRef.current) {
                textareaRef.current.style.height = "auto";
            }
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
        setInput(e.target.value);
        // Auto-resize
        const textarea = e.target;
        textarea.style.height = "auto";
        textarea.style.height = `${Math.min(textarea.scrollHeight, 120)}px`;
    };

    return (
        <div className="chat-input-area">
            <div className="chat-input-wrapper">
                <textarea
                    ref={textareaRef}
                    value={input}
                    onChange={handleInput}
                    onKeyDown={handleKeyDown}
                    placeholder={isLoading ? "Agent is thinking..." : "Type your message..."}
                    disabled={isLoading}
                    rows={1}
                    id="chat-input"
                />
                <button
                    className="send-btn"
                    onClick={handleSend}
                    disabled={!input.trim() || isLoading}
                    id="send-button"
                    aria-label="Send message"
                >
                    ➤
                </button>
            </div>
        </div>
    );
};
