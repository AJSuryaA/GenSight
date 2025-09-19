import os
import base64

# Configuration
IMAGE_FOLDER = "/home/master_node/GenSight/plots"
OUTPUT_DIR = "/home/master_node/GenSight/reports"

# Get available images
available_images = sorted([f for f in os.listdir(IMAGE_FOLDER) if f.endswith('.png')])
print("Available images:", available_images)


def encode_image(image_path):
    """Encode image to base64 for embedding in HTML"""
    if os.path.exists(image_path):
        with open(image_path, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode('utf-8')
        return f"data:image/png;base64,{encoded}"
    return None

def generate_html(eda_summary, image_insights, summary_text ):
    """Generate the main HTML file with embedded data"""
    # Encode all images to base64
    image_data = {}
    for img_name, _ in image_insights:
        src_path = os.path.join(IMAGE_FOLDER, img_name)
        image_data[img_name] = encode_image(src_path)
    
    # Create HTML content
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GenSight Data Insights Report</title>
    <link rel="stylesheet" href="/app/frontend/static/style.css">
    <!-- Include jsPDF and html2canvas for client-side PDF generation -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
</head>
<body>
    <div class="header">
        <h1>GenSight Data Insights Report</h1>
        <button id="downloadPdf" class="download-btn">Download as PDF</button>
    </div>

    <div class="container">
        <section class="section">
            <h2>EDA Overview</h2>
            <p>{eda_summary}</p>
        </section>

        <section class="section">
            <h2>Image Insights</h2>
            <div class="image-gallery">
"""
    
    for img_name, insight in image_insights:
        img_data = image_data.get(img_name)
        if img_data:
            html_content += f"""
                <div class="image-card">
                    <h3>{img_name}</h3>
                    <img src="{img_data}" alt="{img_name}" class="report-image">
                    <p>{insight}</p>
                </div>
            """
        else:
            html_content += f"""
                <div class="image-card">
                    <h3>{img_name}</h3>
                    <p class="image-missing">Image not available</p>
                    <p>{insight}</p>
                </div>
            """
    
    html_content += f"""
            </div>
        </section>

        <section class="section">
            <h2>Summary Insights</h2>
            <p>{summary_text}</p>
        </section>
    </div>

    <script src="/app/frontend/static/script.js"></script>
</body>
</html>
    """
    
    # Save HTML file
    with open(os.path.join(OUTPUT_DIR, "report.html"), "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print("✅ HTML report generated: report.html")

