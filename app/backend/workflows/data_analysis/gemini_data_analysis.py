import os
import pandas as pd
from google.genai import types
from google.genai import Client
from dotenv import load_dotenv

load_dotenv()

def generate_dataframe_summary(df: pd.DataFrame) -> str:
    summary = [
        "Data Types:\n" + df.dtypes.to_string(),
        "\nMissing Values:\n" + df.isnull().sum().to_string(),
        "\nUnique Values:\n" + df.nunique().to_string(),
        "\nSample Data (first 5 rows):\n" + df.head(5).to_string(),
    ]
    return "\n".join(summary)

def read_images_from_folder(folder_path: str) -> list:
    images = []
    for filename in os.listdir(folder_path):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            full_path = os.path.join(folder_path, filename)
            with open(full_path, "rb") as f:
                images.append((filename, f.read()))
    return images

def analyze_with_gemini(client, df_summary: str, images: list, model_name: str = "gemini-2.5-flash") -> str:
    contents = [types.Part(
        text=(
            f"Dataset Summary:\n{df_summary}\n\n"
            "Please analyze the attached visualization images and provide insights.\n"
            "Return output strictly in dictionary format (JSON-like). Do not use bold, do not add extra text, "
            "and do not deviate from the structure.\n\n"
            "The dictionary must follow this structure:\n"
            "{\n"
            "  'EDA_overview': {\n"
            "       'point1': '...'\n"
            "       'point2': '...'\n"
            "   },\n"
            "  'image_insights': {\n"
            "       '1_boxplot_age_target.png': 'insight about the plot',\n"
            "       '2_boxplot_thalach_target.png': 'insight about the plot',\n"
            "       ...\n"
            "   },\n"
            "  'summary': {\n"
            "       'insight1': '...',\n"
            "       'insight2': '...'\n"
            "   }\n"
            "}\n\n"
            "Do not use the word 'target'. Instead, describe what the column represents (e.g., medical condition presence/absence).\n"
        )
    )]

    for filename, image_bytes in images:
        contents.append(types.Part.from_bytes(data=image_bytes, mime_type='image/png'))
        contents.append(types.Part(text=f"Please analyze the visualization image named '{filename}' and provide data insights."))

    response = client.models.generate_content(
        model=model_name,
        contents=contents
    )
    return response.text

