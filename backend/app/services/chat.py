import google.generativeai as genai
from app.core.config import settings

SYSTEM_INSTRUCTION = """
You are "CAD Diff AI Chatbot", a friendly, expert assistant built directly into the CAD Diff AI engineering dashboard. 
Your goal is to help beginners and experienced engineers understand engineering drawing comparisons, blueprints, and the detected modifications.

You have access to the comparison report context. When answering questions, follow these rules to make responses highly CATCHY, VISUAL, and EASY TO UNDERSTAND:
1. Use relevant emojis (like 🔴, 🟢, 🔵, ⚠️, 🔍, 📐, 💡, 🧱) to color-code and organize details.
2. Highlight drawing color differences in a bold, eye-catching way:
   - 🔴 **RED lines** show **REMOVED** elements (present in drawing A but deleted in B).
   - 🟢 **GREEN lines** show **ADDED** elements (brand new in drawing B).
   - 🔵 **BLUE / CYAN lines** show **CHANGED or SHIFTED** linework (modified details).
3. Keep technical explanations extremely simple, clear, and action-oriented. Bold key terms so they pop out immediately.
4. If asked about a region (e.g. "What is Region #1?"), explain its location and severity clearly using bullet points and emojis.
5. Keep your responses concise (2-4 bullet points or short sentences) so they fit beautifully in the chat interface.
"""

def generate_chat_response(report_data: dict, user_message: str, history: list[dict]) -> str:
    """
    Formulates a conversation with Gemini, feeding the comparison report context and
    generating a conversational response to the user's question.
    """
    if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY.strip() == "":
        return (
            "I'm sorry, I cannot answer questions right now because the server's Gemini API key "
            "is not configured. Please ask the developer to set the GEMINI_API_KEY environment variable."
        )

    # 1. Format the comparison session context
    stats = report_data.get("statistics", {})
    similarity = report_data.get("similarity_score", 0.0)
    status = report_data.get("status", "success")
    summary = report_data.get("summary", "")
    
    context_intro = f"""
Here is the context of the compared drawings (Reference A vs Comparison B):
- Alignment Status: {status.upper()}
- Structural Similarity Score: {similarity * 100:.1f}%
- Total Changed Regions: {stats.get("total_regions", 0)}
- Drawing Modified Area: {stats.get("change_percentage", 0)}%
- Noise Limit Filter Setting: {stats.get("detected_noise_limit", 40)}px
- AI Change Summary: {summary}
"""

    regions_list = []
    for r in stats.get("regions", []):
        regions_list.append(
            f"- Region #{r.get('id')}: Centered in the {r.get('location')}. Severity is {r.get('severity')}. Area is {int(r.get('area', 0))} px². Bounding Box: {r.get('bbox')}."
        )
    regions_context = "\n".join(regions_list) if regions_list else "No changed regions detected."

    # 2. Configure Gemini and start chat session
    genai.configure(api_key=settings.GEMINI_API_KEY.strip())
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=SYSTEM_INSTRUCTION
    )
    
    # 3. Format history for GenerativeModel start_chat structure
    formatted_history = []
    for msg in history:
        # Convert role: assistant/bot/model to role: model
        role = "model" if msg.get("role") in ["model", "assistant", "bot"] else "user"
        formatted_history.append({
            "role": role,
            "parts": [msg.get("content", "")]
        })
        
    # Start the chat session
    chat = model.start_chat(history=formatted_history)
    
    # Feed context to the chat on the first user interaction if history is empty
    full_message = user_message
    if len(formatted_history) == 0:
        full_message = f"{context_intro}\n\nList of modifications:\n{regions_context}\n\nUser Question: {user_message}"
        
    response = chat.send_message(full_message)
    return response.text.strip()
