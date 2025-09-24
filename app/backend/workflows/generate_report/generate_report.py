import os
import base64

# Configuration
IMAGE_FOLDER = "/home/master_node/GenSight/plots"
OUTPUT_DIR = "/home/master_node/GenSight/eda_report"

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

def generate_html(eda_summary, image_insights, summary_text):
    """Generate the main HTML file with embedded data"""
    # Encode all images to base64
    image_data = {}
    for img_name, _ in image_insights:
        src_path = os.path.join(IMAGE_FOLDER, img_name)
        image_data[img_name] = encode_image(src_path)
    
    # Create HTML content
    html_content = f"""
<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>GenSight Data Insights Report</title>
    <link rel="stylesheet" href="/static/style.css" />
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
    # Add image cards with base64 images or placeholder text
    for img_name, insight in image_insights:
        img_base64 = image_data.get(img_name)
        if img_base64:
            html_content += f"""
                <div class="image-card">
                    <h3>{img_name}</h3>
                    <img src="{img_base64}" alt="{img_name}" class="report-image" />
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

    # Continue after images section
    html_content += f"""
            </div>
        </section>

        <section class="section">
            <h2>Summary Insights</h2>
            <p>{summary_text}</p>
        </section>
    </div>

    <script>
        class ReportGenerator {{
            constructor() {{
                this.downloadBtn = document.getElementById('downloadPdf');
                this.setupEventListeners();
                this.jspdf = window.jspdf;
                if (!this.jspdf) {{
                    console.error("jsPDF library not loaded");
                }}
            }}

            setupEventListeners() {{
                if (!this.downloadBtn) {{
                    console.error("Download button not found");
                    return;
                }}
                this.downloadBtn.addEventListener('click', () => {{
                    this.generatePDF();
                }});
            }}

            async generatePDF() {{
                try {{
                    this.showLoading();
                    this.downloadBtn.disabled = true;
                    this.downloadBtn.textContent = 'Generating PDF...';

                    const pdfBlob = await this.generateClientSidePdf();
                    this.downloadPdf(pdfBlob, 'GenSight_Report.pdf');
                    
                }} catch (error) {{
                    console.error('PDF generation error:', error);
                    alert('Error generating PDF: ' + error.message);
                }} finally {{
                    this.hideLoading();
                    this.downloadBtn.disabled = false;
                    this.downloadBtn.textContent = 'Download as PDF';
                }}
            }}

            async generateClientSidePdf() {{
                return new Promise(async (resolve, reject) => {{
                    try {{
                        const {{ jsPDF }} = this.jspdf;
                        const doc = new jsPDF('p', 'mm', 'a4');
                        const pageWidth = doc.internal.pageSize.getWidth();
                        const pageHeight = doc.internal.pageSize.getHeight();
                        const margin = 20;
                        const contentWidth = pageWidth - (margin * 2);
                        let currentY = margin;

                        doc.setFont('helvetica');
                        doc.setFontSize(10);

                        this.addHeader(doc, pageWidth);
                        currentY += 15;

                        let edaPara = document.querySelector('.section:nth-child(1) p');
                        let edaText = edaPara ? edaPara.textContent : "";
                        currentY = this.processTextSection(doc, 'EDA Overview', edaText, currentY, margin, contentWidth, pageHeight);

                        let imageSection = document.querySelector('.section:nth-child(2)');
                        if (imageSection) {{
                            currentY = await this.processImageSection(doc, imageSection, currentY, margin, contentWidth, pageHeight);
                        }}

                        let summaryPara = document.querySelector('.section:nth-child(3) p');
                        let summaryText = summaryPara ? summaryPara.textContent : "";
                        currentY = this.processTextSection(doc, 'Summary Insights', summaryText, currentY, margin, contentWidth, pageHeight);

                        const pdfBlob = doc.output('blob');
                        resolve(pdfBlob);
                    }} catch (error) {{
                        reject(error);
                    }}
                }});
            }}

            addHeader(doc, pageWidth) {{
                doc.setFontSize(20);
                doc.setFont('helvetica', 'bold');
                doc.setTextColor(44, 62, 80);
                doc.text('GenSight Data Insights Report', pageWidth / 2, 15, {{ align: 'center' }});

                doc.setDrawColor(52, 152, 219);
                doc.setLineWidth(0.5);
                doc.line(20, 18, pageWidth - 20, 18);

                doc.setFontSize(10);
                doc.setFont('helvetica', 'normal');
            }}

            processTextSection(doc, title, content, startY, margin, contentWidth, pageHeight) {{
                let currentY = startY;

                if (currentY > pageHeight - 30) {{
                    doc.addPage();
                    currentY = margin;
                }}

                doc.setFontSize(16);
                doc.setFont('helvetica', 'bold');
                doc.setTextColor(44, 62, 80);
                doc.text(title, margin, currentY);
                currentY += 8;

                doc.setDrawColor(52, 152, 219);
                doc.setLineWidth(0.3);
                doc.line(margin, currentY - 2, margin + 50, currentY - 2);
                currentY += 5;

                doc.setFontSize(11);
                doc.setFont('helvetica', 'normal');
                doc.setTextColor(0, 0, 0);

                const lines = doc.splitTextToSize(content, contentWidth);
                for (let i = 0; i < lines.length; i++) {{
                    if (currentY > pageHeight - 10) {{
                        doc.addPage();
                        currentY = margin;
                    }}
                    doc.text(lines[i], margin, currentY);
                    currentY += 6;
                }}

                currentY += 10;
                return currentY;
            }}

            async processImageSection(doc, section, startY, margin, contentWidth, pageHeight) {{
                let currentY = startY;
                const imageCards = section.querySelectorAll('.image-card');

                if (currentY > pageHeight - 30) {{
                    doc.addPage();
                    currentY = margin;
                }}

                doc.setFontSize(16);
                doc.setFont('helvetica', 'bold');
                doc.setTextColor(44, 62, 80);
                doc.text('Image Insights', margin, currentY);
                currentY += 8;

                doc.setDrawColor(52, 152, 219);
                doc.setLineWidth(0.3);
                doc.line(margin, currentY - 2, margin + 50, currentY - 2);
                currentY += 10;

                for (const card of imageCards) {{
                    const title = card.querySelector('h3').textContent;
                    const insight = card.querySelector('p').textContent;
                    const img = card.querySelector('img');
                    const titleHeight = this.calculateTextHeight(doc, title, contentWidth, 12);
                    const insightHeight = this.calculateTextHeight(doc, insight, contentWidth, 10);
                    let imageHeight = 0;

                    if (img && img.src && !img.src.includes('data:image/svg')) {{
                        imageHeight = Math.min(80, (img.naturalHeight * contentWidth) / img.naturalWidth);
                    }}

                    const totalCardHeight = titleHeight + imageHeight + insightHeight + 15;

                    if (currentY + totalCardHeight > pageHeight - 10) {{
                        doc.addPage();
                        currentY = margin;
                    }}

                    doc.setFontSize(12);
                    doc.setFont('helvetica', 'bold');
                    doc.setTextColor(44, 62, 80);

                    const titleLines = doc.splitTextToSize(title, contentWidth);
                    for (let i = 0; i < titleLines.length; i++) {{
                        doc.text(titleLines[i], margin, currentY);
                        currentY += 5;
                    }}
                    currentY += 3;

                    if (img && img.src && !img.src.includes('data:image/svg')) {{
                        try {{
                            const imgData = await this.getImageData(img.src);
                            let imgWidth = contentWidth;
                            let imgHeight = (img.naturalHeight * contentWidth) / img.naturalWidth;
                            const maxImageHeight = 80;
                            if (imgHeight > maxImageHeight) {{
                                const ratio = maxImageHeight / imgHeight;
                                imgHeight = maxImageHeight;
                                imgWidth = imgWidth * ratio;
                            }}

                            if (currentY + imgHeight > pageHeight - 10) {{
                                doc.addPage();
                                currentY = margin;
                            }}

                            const imageX = margin + (contentWidth - imgWidth) / 2;
                            doc.addImage(imgData, 'PNG', imageX, currentY, imgWidth, imgHeight);

                            currentY += imgHeight + 5;
                        }} catch (error) {{
                            console.warn('Failed to add image:', error);
                            this.addErrorMessage(doc, margin, currentY, 'Image could not be loaded');
                            currentY += 10;
                        }}
                    }} else {{
                        this.addErrorMessage(doc, margin, currentY, 'Image not available');
                        currentY += 10;
                    }}

                    doc.setFontSize(10);
                    doc.setFont('helvetica', 'normal');
                    doc.setTextColor(0, 0, 0);

                    const insightLines = doc.splitTextToSize(insight, contentWidth);
                    for (let i = 0; i < insightLines.length; i++) {{
                        if (currentY > pageHeight - 10) {{
                            doc.addPage();
                            currentY = margin;
                        }}
                        doc.text(insightLines[i], margin, currentY);
                        currentY += 5;
                    }}

                    if (currentY < pageHeight - 15) {{
                        doc.setDrawColor(200, 200, 200);
                        doc.setLineWidth(0.1);
                        doc.line(margin, currentY + 2, margin + contentWidth, currentY + 2);
                        currentY += 10;
                    }} else {{
                        doc.addPage();
                        currentY = margin;
                    }}
                }}

                return currentY;
            }}

            calculateTextHeight(doc, text, maxWidth, fontSize) {{
                doc.setFontSize(fontSize);
                const lines = doc.splitTextToSize(text, maxWidth);
                return lines.length * (fontSize * 0.35);
            }}

            addErrorMessage(doc, x, y, message) {{
                doc.setFontSize(10);
                doc.setFont('helvetica', 'italic');
                doc.setTextColor(231, 76, 60);
                doc.text(message, x, y);
            }}

            async getImageData(url) {{
                return new Promise((resolve, reject) => {{
                    const img = new Image();
                    img.crossOrigin = 'Anonymous';
                    img.onload = () => {{
                        const canvas = document.createElement('canvas');
                        const ctx = canvas.getContext('2d');
                        canvas.width = img.width;
                        canvas.height = img.height;
                        ctx.drawImage(img, 0, 0);

                        try {{
                            resolve(canvas.toDataURL('image/jpeg', 0.8));
                        }} catch (e) {{
                            resolve(canvas.toDataURL('image/png'));
                        }}
                    }};
                    img.onerror = () => reject(new Error('Image load error for ' + url));
                    img.src = url;
                }});
            }}

            downloadPdf(blob, filename) {{
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                a.download = filename;
                document.body.appendChild(a);
                a.click();

                // Clean up
                setTimeout(() => {{
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                }}, 100);
            }}

            showLoading() {{
                let loading = document.getElementById('loading');
                if (!loading) {{
                    loading = document.createElement('div');
                    loading.id = 'loading';
                    loading.className = 'loading';
                    loading.innerHTML = `
                        <div class="spinner"></div>
                        <p>Generating PDF... This may take a moment</p>
                    `;
                    document.body.appendChild(loading);
                }}
                loading.style.display = 'block';
            }}

            hideLoading() {{
                const loading = document.getElementById('loading');
                if (loading) {{
                    loading.style.display = 'none';
                }}
            }}
        }}

        document.addEventListener('DOMContentLoaded', () => {{
            new ReportGenerator();
        }});
    </script>
</body>

</html>
"""
    
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    with open(os.path.join(OUTPUT_DIR, "report.html"), "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print("✅ HTML report generated: report.html")
