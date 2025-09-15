import re
import json


def extract_section(text: str, header: str, next_header: str = None) -> str:
    # Case-insensitive extraction from header to next_header or end of text
    if next_header:
        pattern = rf"(?i){re.escape(header)}(.*?)(?={re.escape(next_header)})"
    else:
        pattern = rf"(?i){re.escape(header)}(.*)"
    match = re.search(pattern, text, flags=re.DOTALL)
    return match.group(1).strip() if match else ""

def split_into_paragraphs(text: str) -> list:
    # Split text by empty lines or multiple line breaks into paragraphs
    paragraphs = re.split(r'\n\s*\n', text)
    return [p.strip() for p in paragraphs if p.strip()]

def extract_insights(text: str) -> dict:
    # Extract sections based on your output format
    eda = extract_section(text, "EDA overview :", "summary insights:")
    summary = extract_section(text, "summary insights:", None)

    # Extract per-image insights by splitting lines and detecting image filenames (assumed *.png lines)
    image_insights = {}
    lines = text.splitlines()
    current_image = None
    buffer = []

    for line in lines:
        line_strip = line.strip()
        if line_strip.endswith(".png"):
            # Save previous image insights
            if current_image and buffer:
                image_insights[current_image] = "\n".join(buffer).strip()
            current_image = line_strip
            buffer = []
        else:
            if current_image:
                buffer.append(line)
    # save last image insights
    if current_image and buffer:
        image_insights[current_image] = "\n".join(buffer).strip()

    # split paragraphs
    eda_points = split_into_paragraphs(eda)
    summary_points = split_into_paragraphs(summary)

    return {
        "EDA_Overview": eda_points,
        "Image_Insights": image_insights,
        "Summary_Insights": summary_points
    }



def main():
    # Replace this with the actual Gemini API output text (or load from a file)
    gemini_output_text = """
Gemini API Analysis Result:
 EDA overview :
The dataset consists of 14 features, all of which are numerical with float64 data types. There are no missing values across any of the columns, simplifying the preprocessing steps. Several features such as sex, cp, fbs, restecg, exang, slope, ca, thal, and the heart disease presence variable itself have a limited number of unique values, suggesting they represent categorical or ordinal data. Features like age, trestbps, chol, thalach, and oldpeak have a broader range of unique values, indicating they are continuous or high-cardinality discrete. The sample data shows that all features have been scaled or normalized, with most values ranging around zero, likely through standardization. The outcome variable, heart disease presence, is binary, represented by 0.0 and 1.0, indicating the absence or presence of the condition, respectively.

2_boxplot_age_target.png
Individuals across a wide range of scaled age values exhibit a high likelihood of heart disease presence, with the outcome variable predominantly showing 1.0. However, some specific age groups (e.g., very young or very old in the scaled range) show a mixed outcome or a lower likelihood of heart disease presence (values centered around 0.0 or 0.5).

6_bar_cp_target.png
The type of chest pain, represented by 'cp', significantly influences the likelihood of heart disease presence. The scaled 'cp' values 0.032 and 1.002 are associated with the highest mean heart disease presence (around 80%), indicating these specific chest pain types are strong indicators of the condition. In contrast, the 'cp' value -0.9385 is associated with the lowest mean heart disease presence (around 28%).

4_boxplot_oldpeak_target.png
The 'oldpeak' feature shows a varied relationship with heart disease presence. Many lower 'oldpeak' values (e.g., between -0.9 and -0.2) are associated with a high likelihood of heart disease presence. Conversely, higher 'oldpeak' values (e.g., above 1.0) generally correspond to a lower likelihood of heart disease presence, with the outcome often being 0.0. Some 'oldpeak' values show a mixed distribution, indicating a less clear association.

3_pair-plot_age_trestbps_chol_thalach_oldpeak.png
The individual distributions of the features show that 'age', 'trestbps', and 'thalach' are somewhat normally distributed, while 'chol' is positively skewed, and 'oldpeak' is heavily positively skewed with a concentration at lower values. From the scatter plots, a noticeable negative correlation exists between 'age' and 'thalach' (as age increases, maximum heart rate tends to decrease). Other feature pairs generally exhibit weak or no clear linear correlations.

3_boxplot_thalach_target.png
The maximum heart rate achieved, 'thalach', shows a complex relationship with heart disease presence. Many 'thalach' values are strongly associated with either a high (1.0) or low (0.0) likelihood of the condition. Lower 'thalach' values appear to have a mixed or lower heart disease presence, while higher 'thalach' values often correspond to a higher heart disease presence. However, some high 'thalach' values also show a lower likelihood, suggesting a non-linear interaction.

1_heatmap_age_thalach_oldpeak_ca_cp_thal_target.png
The heatmap reveals correlations between features and with heart disease presence. Features positively correlated with heart disease presence are 'cp' (0.43), 'thalach' (0.42), and 'slope' (0.35). Features negatively correlated with heart disease presence include 'exang' (-0.44), 'oldpeak' (-0.43), 'ca' (-0.39), 'thal' (-0.34), 'sex' (-0.28), and 'age' (-0.23). 'chol' and 'fbs' show very weak linear correlation with heart disease presence. Among the features themselves, notable correlations include a negative relationship between 'age' and 'thalach' (-0.40), and a strong negative correlation between 'oldpeak' and 'slope' (-0.58). 'exang' is also negatively correlated with 'thalach' (-0.38).

5_boxplot_ca_target.png
The number of major vessels colored by fluoroscopy, 'ca', shows a strong inverse relationship with heart disease presence. For the two lowest scaled 'ca' values (-0.714 and 0.312, likely representing fewer affected vessels in the original data), the heart disease presence is very high, consistently at 1.0. Conversely, for the higher scaled 'ca' values (1.340, 2.368, and 3.396, likely representing more affected vessels), the heart disease presence is predominantly 0.0, indicating a very low likelihood of the condition. This suggests that higher scaled 'ca' values are associated with a lower likelihood of heart disease presence.

7_bar_thal_target.png
The 'thal' feature, likely related to thalassemia, exhibits varying associations with heart disease presence across its categories. The scaled 'thal' value -0.512 has the highest mean heart disease presence (around 79%). The scaled 'thal' value -3.784 shows a moderate mean heart disease presence (around 50%). The other two 'thal' categories, -2.148 and 1.123, show progressively lower mean heart disease presence (around 33% and 24% respectively). This indicates that specific 'thal' categories are significant indicators for the presence or absence of heart disease.

summary insights:
The dataset is clean with no missing values and features that have undergone scaling. The outcome variable, indicating heart disease presence, is binary. Key indicators for a higher likelihood of heart disease include certain types of chest pain ('cp' values 0.032 and 1.002), specific maximum heart rates ('thalach' values particularly in the mid-to-high range), and lower 'oldpeak' values. Conversely, a higher likelihood of the condition is observed for lower scaled 'ca' values (likely representing fewer affected vessels) and specific 'thal' values (e.g., -0.512). Features like 'exang', 'oldpeak', 'ca', and 'thal' show a negative correlation with heart disease presence, implying that higher values of these scaled features (or specific categories) are associated with a lower probability of the condition. Age has a weak negative correlation with heart disease presence and a more notable negative correlation with 'thalach'. The relationship between several features and heart disease presence, particularly 'age', 'oldpeak', and 'thalach', is complex and not strictly linear, as indicated by the boxplots.
"""
    # Call the extraction function (make sure it's defined or imported)
    insights = extract_insights(gemini_output_text)

    import json
    print(json.dumps(insights, indent=2))


if __name__ == "__main__":
    main()

