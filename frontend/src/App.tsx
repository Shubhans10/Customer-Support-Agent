import { useState, useEffect } from "react";
import { useChat } from "./hooks/useChat";
import { ChatWindow } from "./components/Chat/ChatWindow";
import { ChatInput } from "./components/Chat/ChatInput";
import { SkillTracePanel } from "./components/SkillTrace/SkillTracePanel";
import { Sidebar } from "./components/Sidebar/Sidebar";
import type { SkillInfo } from "./types";
import { fetchSkills } from "./utils/api";

function App() {
  const { messages, skillSteps, isLoading, error, sendMessage, clearChat } =
    useChat();
  const [skills, setSkills] = useState<SkillInfo[]>([]);

  useEffect(() => {
    fetchSkills()
      .then((data) => setSkills(data.skills))
      .catch(() => {
        // Use default skills if API is not available
        setSkills([
          { name: "Work Order Lookup", description: "Search work orders by ID, product, or status", icon: "📋" },
          { name: "Equipment Status", description: "Check machine health, sensors, and maintenance", icon: "🔧" },
          { name: "Defect Report", description: "Log quality defects and non-conformance reports", icon: "🔍" },
          { name: "Knowledge Base", description: "Search SOPs, safety protocols, and procedures", icon: "📖" },
          { name: "Engineer Escalation", description: "Escalate issues to engineering or management", icon: "🙋" },
        ]);
      });
  }, []);

  return (
    <div className="app-layout">
      <Sidebar skills={skills} onSampleQuery={sendMessage} />

      <div className="main-chat">
        <div className="chat-header">
          <div>
            <div className="chat-header-title">AMM Operations Chat</div>
            <div className="chat-header-status">
              <div className="status-dot" />
              Agent Online
            </div>
          </div>
          <button className="clear-btn" onClick={clearChat} id="clear-chat-btn">
            Clear Chat
          </button>
        </div>

        {error && (
          <div className="error-banner">
            ⚠️ {error}
          </div>
        )}

        <ChatWindow messages={messages} isLoading={isLoading} />
        <ChatInput onSend={sendMessage} isLoading={isLoading} />
      </div>

      <SkillTracePanel steps={skillSteps} />
    </div>
  );
}

export default App;
