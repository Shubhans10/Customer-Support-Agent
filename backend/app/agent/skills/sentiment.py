import json
from langchain_core.tools import tool


@tool
def analyze_sentiment(message: str) -> str:
    """Analyze the sentiment and emotional tone of a customer message.
    Use this tool when you need to gauge the customer's emotional state
    to adjust your response tone appropriately, or when the customer
    appears to be frustrated, angry, or upset.
    Provide the customer's exact message for analysis.
    """
    message_lower = message.lower()

    # Keyword-based sentiment indicators
    angry_words = {"furious", "angry", "terrible", "worst", "horrible", "disgusting",
                   "unacceptable", "ridiculous", "outrageous", "scam", "fraud", "sue",
                   "lawyer", "complaint", "useless", "incompetent", "waste"}
    negative_words = {"disappointed", "frustrated", "unhappy", "upset", "annoyed",
                      "waiting", "delayed", "broken", "wrong", "missing", "problem",
                      "issue", "bad", "poor", "slow", "never", "still"}
    positive_words = {"thank", "thanks", "great", "excellent", "amazing", "perfect",
                      "wonderful", "love", "awesome", "happy", "pleased", "good",
                      "helpful", "appreciate", "satisfied"}

    msg_words = set(message_lower.split())
    angry_count = len(msg_words & angry_words)
    negative_count = len(msg_words & negative_words)
    positive_count = len(msg_words & positive_words)

    # Exclamation marks and caps indicate intensity
    exclamation_count = message.count("!")
    caps_ratio = sum(1 for c in message if c.isupper()) / max(len(message), 1)

    if angry_count >= 2 or (angry_count >= 1 and exclamation_count >= 2):
        sentiment = "angry"
        score = -0.9
        recommendation = "Apologize sincerely, acknowledge frustration, offer immediate resolution, and consider escalation."
    elif angry_count >= 1 or (negative_count >= 2 and (exclamation_count >= 1 or caps_ratio > 0.3)):
        sentiment = "very_negative"
        score = -0.7
        recommendation = "Express empathy, acknowledge the issue, prioritize resolution."
    elif negative_count >= 2:
        sentiment = "negative"
        score = -0.4
        recommendation = "Acknowledge concern, provide reassurance, work toward a solution."
    elif negative_count == 1:
        sentiment = "slightly_negative"
        score = -0.2
        recommendation = "Address the concern while maintaining a positive, helpful tone."
    elif positive_count >= 2:
        sentiment = "very_positive"
        score = 0.8
        recommendation = "Maintain the positive interaction, thank the customer."
    elif positive_count >= 1:
        sentiment = "positive"
        score = 0.5
        recommendation = "Continue with a friendly, warm tone."
    else:
        sentiment = "neutral"
        score = 0.0
        recommendation = "Maintain a professional and helpful tone."

    return json.dumps({
        "sentiment": sentiment,
        "score": score,
        "recommendation": recommendation,
        "analysis": {
            "angry_indicators": angry_count,
            "negative_indicators": negative_count,
            "positive_indicators": positive_count,
            "intensity_signals": {
                "exclamation_marks": exclamation_count,
                "caps_ratio": round(caps_ratio, 2)
            }
        },
        "summary": f"Customer sentiment: {sentiment} (score: {score}). {recommendation}"
    }, indent=2)
