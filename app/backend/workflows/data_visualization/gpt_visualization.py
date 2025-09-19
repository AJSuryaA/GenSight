import requests
import pandas as pd
import re, ast, os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("PERPLEXITY_API_KEY_2")
API_URL = "https://api.perplexity.ai/chat/completions"

def create_visuvalization_summary_prompt(df: pd.DataFrame,  problem_type) -> str:
    summary = [
        "Data Types:\n" + df.dtypes.to_string(),
        "\nMissing Values:\n" + df.isnull().sum().to_string(),
        "\nUnique Values:\n" + df.nunique().to_string(),
        "\nSample Data:\n" + df.head(5).to_string(),
        "\nproblem_type:\n" + problem_type,
    ]
    prompt = "\n".join(summary)
    return (
    f"Here is the dataset summary and correlation matrix:\n{prompt}\n\n"
    "Based ONLY on correlation analysis and data types:\n"
    "- Suggest visualizations strictly necessary to understand feature relationships with the target for inference.\n"
    "- Do NOT include redundant visualizations for features highly correlated (> |0.8|); keep only one representative.\n"
    "- Skip features with low or zero correlation.\n"
    "- Prioritize features most relevant to the target based on correlation.\n"
    "- Include pair plots if they meaningfully contribute to inference.\n"
    "- Use only these chart types: ['histogram', 'boxplot', 'violin', 'bar', 'heatmap', 'line-chart', 'scatter'].\n"
    "- For numeric features vs target: use scatter plots if regression, box or violin plots if classification.\n"
    "- For categorical features vs target: use bar charts.\n"
    "- Group columns logically by chart type to avoid clutter.\n"
    "- Exclude any model performance or evaluation visualizations (e.g., confusion matrix, ROC curve, model comparison).\n\n"
    "Respond ONLY in the following exact dictionary format with no additional text:\n\n"
    "result = {\n"
    "    1: {'col': [col_names_as_list], 'chart': [chart_type_as_list]},\n"
    "    2: {'col': [col_names_as_list], 'chart': [chart_type_as_list]},\n"
    "    3: {...},\n"
    "    ...\n"
    "}\n\n"
    "For example:\n"
    "result = {\n"
    "    1: {'col': ['age', 'thalach'], 'chart': ['scatter']},\n"
    "    2: {'col': ['oldpeak', 'thalach'], 'chart': ['scatter']},\n"
    "    3: {'col': ['sex', 'cp', 'exang', 'slope', 'ca', 'thal'], 'chart': ['bar']},\n"
    "    4: {'col': ['age', 'trestbps', 'chol', 'thalach', 'oldpeak'], 'chart': ['heatmap']},\n"
    "    5: {'col': ['date', 'sales'], 'chart': ['line-chart']},\n"
    "    6: {'col': ['age', 'target'], 'chart': ['boxplot']},\n"
    "    7: {'col': ['thalach', 'target'], 'chart': ['boxplot']},\n"
    "    8: {'col': ['oldpeak', 'target'], 'chart': ['boxplot']}\n"
    "}\n\n"
)



def call_gpt_api(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "sonar-pro",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.5
    }
    response = requests.post(API_URL, json=payload, headers=headers)
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]


def parse_gpt_visualization_response(response_text: str) -> dict:
    """
    Improved parser extracting dictionaries for GPT 'result' output.
    Supports multiline and balanced nested braces.
    """
    result = {'result': {}}
    
    # Find 'result = {', extract the dictionary enclosed by balanced braces
    match1 = re.search(r"result\s*=\s*{", response_text)
    if match1:
        start = match1.end()-1
        dict_str = extract_balanced_braces(response_text, start)
        if dict_str and dict_str.startswith("{") and dict_str.endswith("}"):
            try:
                parsed_dict = ast.literal_eval(dict_str)
                result['result'] = {int(k): v for k, v in parsed_dict.items()}
            except Exception as e:
                print("Error parsing result with balanced braces:", e)
                result['result'] = {}  # fallback
        else:
            print("Failed to extract a valid dictionary from GPT response.")
    else:
        print("No 'result =' statement found in GPT response.")
    
    return result

# Make sure your extract_balanced_braces implementation is robust
def extract_balanced_braces(text, start):
    """
    Extracts a balanced {...} dictionary string from text, given a starting '{' index.
    """
    stack = []
    for idx in range(start, len(text)):
        if text[idx] == '{':
            stack.append(idx)
        elif text[idx] == '}':
            stack.pop()
            if not stack:
                # Found the matching closing brace
                return text[start:idx+1]
    return None  # Unbalanced or not found


if __name__ == "__main__":
    # Example dummy DataFrame for testing
    file_location= '/home/master_node/GenSight/uploaded_files/data.csv'
    df = pd.read_csv(file_location)

    problem_type = "classification"

    # Create prompt from dataframe and model info
    prompt = create_visuvalization_summary_prompt(df, problem_type)
    print("Prompt sent to GPT:\n", prompt)

    # Call the API and get response (uncomment below when API key is set)
    response_text = call_gpt_api(prompt)
    print("\nRaw GPT response:\n", response_text)

    # For testing without API call, you can assign response_text manually with a sample output

    # Parse the GPT response
    parsed_result = parse_gpt_visualization_response(response_text)
    print("\nParsed visualization dictionaries:\n", parsed_result)
