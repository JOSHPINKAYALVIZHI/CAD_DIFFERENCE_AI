import google.generativeai as genai
from app.core.config import settings

def generate_fallback_summary(stats: dict) -> str:
    """
    Generates a rule-based change summary when the Gemini API key is missing or fails.
    """
    total_regions = stats["total_regions"]
    pct = stats["change_percentage"]
    
    if total_regions == 0:
        return "The comparison detected no visible changes. The reference and comparison images appear to be identical."
        
    summary = f"The comparison identified {total_regions} distinct changed region{'s' if total_regions > 1 else ''} between the two drawings, affecting approximately {pct}% of the total drawing area. "
    
    high_sev = [r for r in stats["regions"] if r["severity"] == "high"]
    med_sev = [r for r in stats["regions"] if r["severity"] == "medium"]
    
    if high_sev:
        locs = list(dict.fromkeys([r["location"] for r in high_sev]))  # remove duplicates
        summary += f"Significant modifications with high severity were detected primarily in the {', '.join(locs[:3])} region{'s' if len(locs) > 1 else ''}. "
    elif med_sev:
        locs = list(dict.fromkeys([r["location"] for r in med_sev]))
        summary += f"Moderate structural differences were observed near the {', '.join(locs[:3])}. "
    else:
        locs = list(dict.fromkeys([r["location"] for r in stats["regions"]]))
        summary += f"Minor modifications were detected around the {', '.join(locs[:3])}. "
        
    summary += "Please review the colored difference mask where red indicates removed elements, green indicates new additions, and blue represents modified details."
    return summary

def generate_ai_summary(stats: dict) -> str:
    """
    Calls the Gemini API to generate a professional change summary based on the difference statistics.
    Falls back to a rule-based summary if the API is unconfigured or returns an error.
    """
    if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY.strip() == "":
        return generate_fallback_summary(stats)
        
    try:
        genai.configure(api_key=settings.GEMINI_API_KEY.strip())
        
        # Prepare summaries of regions for the LLM prompt
        regions_desc = []
        for r in stats["regions"][:12]:  # Send up to the top 12 largest modifications
            regions_desc.append(
                f"- Region #{r['id']}: Centered in the {r['location']}. Severity is {r['severity']}. Area: {int(r['area'])} px²."
            )
        regions_text = "\n".join(regions_desc)
        
        prompt = f"""
You are an expert AI system for comparing technical CAD drawings and blueprints.
Based on a computer vision analysis of the two versions, the following changes were detected:
- Total changed regions: {stats['total_regions']}
- Combined modified area: {int(stats['total_changed_area_px'])} pixels²
- Percentage of drawing area modified: {stats['change_percentage']}%

Here are the largest modified regions in order of size:
{regions_text}

Generate a concise, human-readable summary paragraph (around 80-130 words) explaining the modifications.
The summary MUST include:
1. An overall comparison statement (e.g. "The comparison identified four significant changes...")
2. Major changed objects or regions and their approximate layout position (e.g. top-left, center-right, bottom).
3. The severity/scale of the edits and the percentage area affected.
4. Keep the tone professional, technical, and objective. 
5. Do NOT mention "the list", "RANSAC", "computer vision", "the spreadsheet", "Region #1", or "bounding boxes". Speak as if you are directly looking at the drawing changes (e.g., "A new structure was added in the top-left...", "Modifications were observed near...").
"""
        # Initialize Gemini 1.5 Flash (highly optimized and fast)
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        # Return fallback with error details logged or prepended
        fallback = generate_fallback_summary(stats)
        return f"{fallback} (Note: Gemini API summary generation could not run because of: {str(e)})"
