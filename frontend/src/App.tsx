import { useState, useEffect } from "react";
import { useChat } from "./hooks/useChat";
import { useCompare } from "./hooks/useCompare";
import { ChatWindow } from "./components/Chat/ChatWindow";
import { ChatInput } from "./components/Chat/ChatInput";
import { SkillTracePanel } from "./components/SkillTrace/SkillTracePanel";
import { Sidebar } from "./components/Sidebar/Sidebar";
import { CompareToggle } from "./components/Compare/CompareToggle";
import { ComparisonView } from "./components/Compare/ComparisonView";
import type { SkillInfo } from "./types";
import { fetchSkills } from "./utils/api";

function App() {
  const { messages, skillSteps, planSteps, isLoading, error, sendMessage, clearChat } =
    useChat();
  const {
    skillsResult, agentResult, summary,
    isLoading: compareLoading, error: compareError,
    sendCompare, clearCompare,
  } = useCompare();

  const [skills, setSkills] = useState<SkillInfo[]>([]);
  const [compareMode, setCompareMode] = useState(false);

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
          { name: "Chart Generation", description: "Generate performance charts and visualizations", icon: "📊" },
        ]);
      });
  }, []);

  const handleToggleCompare = () => {
    setCompareMode((prev) => !prev);
  };

  const handleSend = (msg: string) => {
    if (compareMode) {
      sendCompare(msg);
    } else {
      sendMessage(msg);
    }
  };

  const handleClear = () => {
    if (compareMode) {
      clearCompare();
    } else {
      clearChat();
    }
  };

  return (
    <div className="app-layout">
      <Sidebar skills={skills} onSampleQuery={handleSend} />

      <div className="main-chat">
        <div className="chat-header">
          <div>
            <div className="chat-header-title">AMM Operations Chat</div>
            <div className="chat-header-status">
              <div className="status-dot" />
              Agent Online
            </div>
          </div>
          <div className="chat-header-actions">
            <CompareToggle compareMode={compareMode} onToggle={handleToggleCompare} />
            <button className="clear-btn" onClick={handleClear} id="clear-chat-btn">
              Clear Chat
            </button>
          </div>
        </div>

        {compareMode ? (
          <ComparisonView
            skillsResult={skillsResult}
            agentResult={agentResult}
            summary={summary}
            isLoading={compareLoading}
            error={compareError}
            onSend={sendCompare}
          />
        ) : (
          <>
            {error && (
              <div className="error-banner">
                ⚠️ {error}
              </div>
            )}
            <ChatWindow messages={messages} isLoading={isLoading} />
            <ChatInput onSend={sendMessage} isLoading={isLoading} />
          </>
        )}
      </div>

      {!compareMode && (
        <SkillTracePanel steps={skillSteps} planSteps={planSteps} />
      )}
    </div>
  );
}

export default App;
