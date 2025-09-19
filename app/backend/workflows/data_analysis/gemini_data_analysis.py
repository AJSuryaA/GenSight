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
        text=f"Dataset Summary:\n{df_summary}\n\nPlease analyze the attached visualization images and provide insights.\n"
        "do not use bold just print output without formating"
        "first give basic EDA overview \n"
        "followed by , nameof the image and inferance from that \n"
        "finally summary insights\n"
        "dont use name target, find whats the column about and indicate that\n"
        "For example:\n"
        "EDA overview :\n"
        "points\n"
        "2_boxplot_age_target.png \n"
        "insight\n"
        "summary: \n"
        "summary insights"
        )]
    for filename, image_bytes in images:
        contents.append(types.Part.from_bytes(data=image_bytes, mime_type='image/png'))
        contents.append(types.Part(text=f"Please analyze the visualization image named '{filename}' and provide data insights."))

    response = client.models.generate_content(
        model=model_name,
        contents=contents
    )
    return response.text

def main():
    # Load your dataframe (update path)
    df = pd.read_csv("/home/master_node/GenSight/uploaded_files/data.csv")

    # Folder with generated visualization images
    folder_path = "/home/master_node/GenSight/plots"

    df_summary = generate_dataframe_summary(df)
    images = read_images_from_folder(folder_path)

    client = Client(api_key=os.getenv("Gemini_API"))  # Make sure GOOGLE_APPLICATION_CREDENTIALS is set for authentication

    analysis = analyze_with_gemini(client, df_summary, images)
    print("\nGemini API Analysis Result:\n", analysis)

if __name__ == "__main__":
    main()
