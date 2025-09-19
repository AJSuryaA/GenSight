import json
import re

def extract_sections_from_gpt_response(text: str):
    eda_summary, image_insights, summary_text = "", [], ""

    try:
        # Try to parse as JSON directly
        data = json.loads(text)

        # --- Extract EDA Overview ---
        if "EDA_overview" in data:
            # Convert dict to nicely formatted text
            eda_summary = "\n".join([f"{k}: {v}" for k, v in data["EDA_overview"].items()])

        # --- Extract Image Insights ---
        if "image_insights" in data:
            image_insights = [(k, v) for k, v in data["image_insights"].items()]

        # --- Extract Summary ---
        if "summary" in data:
            summary_text = "\n".join([f"{k}: {v}" for k, v in data["summary"].items()])

    except json.JSONDecodeError:
        # Fallback to regex if JSON parsing fails (for older GPT responses)
        eda_match = re.search(r"EDA overview :\s*(\{[\s\S]+?\})", text, re.IGNORECASE)
        if eda_match:
            eda_summary = re.sub(r"[\'\"\{\}]", "", eda_match.group(1)).strip()
            eda_summary = re.sub(r",\s*", "\n", eda_summary)

        image_pattern = re.compile(
            r"(\d+_[\w\-]+\.png)\s*([\s\S]+?)(?=\n\d+_[\w\-]+\.png|\nsummary:|$)",
            re.IGNORECASE,
        )
        for match in image_pattern.finditer(text):
            img_name = match.group(1).strip()
            insight_text = re.sub(r"\s+", " ", match.group(2).strip())
            image_insights.append((img_name, insight_text))

        summary_match = re.search(r"summary:\s*(\{[\s\S]+\})", text, re.IGNORECASE)
        if summary_match:
            summary_text = re.sub(r"[\'\"\{\}]", "", summary_match.group(1)).strip()
            summary_text = re.sub(r",\s*", "\n", summary_text)

    return eda_summary, image_insights, summary_text
