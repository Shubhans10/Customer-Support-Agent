interface CompareToggleProps {
    compareMode: boolean;
    onToggle: () => void;
}

export const CompareToggle: React.FC<CompareToggleProps> = ({ compareMode, onToggle }) => {
    return (
        <button
            className={`compare-toggle ${compareMode ? "active" : ""}`}
            onClick={onToggle}
            id="compare-toggle-btn"
            title={compareMode ? "Switch to Standard mode" : "Switch to Compare mode"}
        >
            <div className="compare-toggle-track">
                <span className={`compare-toggle-option ${!compareMode ? "selected" : ""}`}>
                    💬 Standard
                </span>
                <span className={`compare-toggle-option ${compareMode ? "selected" : ""}`}>
                    ⚔️ Compare
                </span>
                <div className={`compare-toggle-slider ${compareMode ? "right" : "left"}`} />
            </div>
        </button>
    );
};
