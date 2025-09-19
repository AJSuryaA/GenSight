class ReportGenerator {
    constructor() {
        this.downloadBtn = document.getElementById('downloadPdf');
        this.setupEventListeners();
        
        // Initialize jsPDF
        this.jspdf = window.jspdf;
    }

    setupEventListeners() {
        this.downloadBtn.addEventListener('click', () => {
            this.generatePDF();
        });
    }

    async generatePDF() {
        try {
            this.showLoading();
            this.downloadBtn.disabled = true;
            this.downloadBtn.textContent = 'Generating PDF...';

            // Generate PDF using jsPDF
            const pdfBlob = await this.generateClientSidePdf();
            this.downloadPdf(pdfBlob, 'GenSight_Report.pdf');
            
        } catch (error) {
            console.error('PDF generation error:', error);
            alert('Error generating PDF: ' + error.message);
        } finally {
            this.hideLoading();
            this.downloadBtn.disabled = false;
            this.downloadBtn.textContent = 'Download as PDF';
        }
    }

    async generateClientSidePdf() {
        return new Promise(async (resolve, reject) => {
            try {
                const { jsPDF } = this.jspdf;
                const doc = new jsPDF('p', 'mm', 'a4');
                const pageWidth = doc.internal.pageSize.getWidth();
                const pageHeight = doc.internal.pageSize.getHeight();
                const margin = 20;
                const contentWidth = pageWidth - (margin * 2);
                let currentY = margin;

                // Set default font
                doc.setFont('helvetica');
                doc.setFontSize(10);

                // Add header
                this.addHeader(doc, pageWidth);
                currentY += 15;

                // Process EDA Overview section
                currentY = this.processTextSection(
                    doc, 
                    'EDA Overview', 
                    document.querySelector('.section:nth-child(1) p').textContent,
                    currentY,
                    margin,
                    contentWidth,
                    pageHeight
                );

                // Process Image Insights section
                currentY = await this.processImageSection(
                    doc,
                    document.querySelector('.section:nth-child(2)'),
                    currentY,
                    margin,
                    contentWidth,
                    pageHeight
                );

                // Process Summary Insights section
                currentY = this.processTextSection(
                    doc, 
                    'Summary Insights', 
                    document.querySelector('.section:nth-child(3) p').textContent,
                    currentY,
                    margin,
                    contentWidth,
                    pageHeight
                );

                // Create blob from PDF
                const pdfBlob = doc.output('blob');
                resolve(pdfBlob);
                
            } catch (error) {
                reject(error);
            }
        });
    }

    addHeader(doc, pageWidth) {
        doc.setFontSize(20);
        doc.setFont('helvetica', 'bold');
        doc.setTextColor(44, 62, 80);
        doc.text('GenSight Data Insights Report', pageWidth / 2, 15, { align: 'center' });
        
        doc.setDrawColor(52, 152, 219);
        doc.setLineWidth(0.5);
        doc.line(20, 18, pageWidth - 20, 18);
        
        // Reset to normal font
        doc.setFontSize(10);
        doc.setFont('helvetica', 'normal');
    }

    processTextSection(doc, title, content, startY, margin, contentWidth, pageHeight) {
        let currentY = startY;

        // Check if we need a new page
        if (currentY > pageHeight - 30) {
            doc.addPage();
            currentY = margin;
        }

        // Add section title
        doc.setFontSize(16);
        doc.setFont('helvetica', 'bold');
        doc.setTextColor(44, 62, 80);
        doc.text(title, margin, currentY);
        currentY += 8;

        // Add underline
        doc.setDrawColor(52, 152, 219);
        doc.setLineWidth(0.3);
        doc.line(margin, currentY - 2, margin + 50, currentY - 2);
        currentY += 5;

        // Process content text
        doc.setFontSize(11);
        doc.setFont('helvetica', 'normal');
        doc.setTextColor(0, 0, 0);

        const lines = doc.splitTextToSize(content, contentWidth);
        
        for (let i = 0; i < lines.length; i++) {
            // Check if we need a new page
            if (currentY > pageHeight - 10) {
                doc.addPage();
                currentY = margin;
            }
            
            doc.text(lines[i], margin, currentY);
            currentY += 6;
        }

        currentY += 10; // Add space after section
        return currentY;
    }

    async processImageSection(doc, section, startY, margin, contentWidth, pageHeight) {
        let currentY = startY;
        const imageCards = section.querySelectorAll('.image-card');

        // Add section title
        if (currentY > pageHeight - 30) {
            doc.addPage();
            currentY = margin;
        }

        doc.setFontSize(16);
        doc.setFont('helvetica', 'bold');
        doc.setTextColor(44, 62, 80);
        doc.text('Image Insights', margin, currentY);
        currentY += 8;

        // Add underline
        doc.setDrawColor(52, 152, 219);
        doc.setLineWidth(0.3);
        doc.line(margin, currentY - 2, margin + 50, currentY - 2);
        currentY += 10;

        for (const card of imageCards) {
            const title = card.querySelector('h3').textContent;
            const insight = card.querySelector('p').textContent;
            const img = card.querySelector('img');

            // Calculate space needed for this image card
            const titleHeight = this.calculateTextHeight(doc, title, contentWidth, 12);
            const insightHeight = this.calculateTextHeight(doc, insight, contentWidth, 10);
            let imageHeight = 0;

            if (img && img.src && !img.src.includes('data:image/svg')) {
                // Estimate image height (max 80mm)
                imageHeight = Math.min(80, (img.naturalHeight * contentWidth) / img.naturalWidth);
            }

            const totalCardHeight = titleHeight + imageHeight + insightHeight + 15;

            // Check if we need a new page for this entire card
            if (currentY + totalCardHeight > pageHeight - 10) {
                doc.addPage();
                currentY = margin;
            }

            // Add image title
            doc.setFontSize(12);
            doc.setFont('helvetica', 'bold');
            doc.setTextColor(44, 62, 80);
            
            const titleLines = doc.splitTextToSize(title, contentWidth);
            for (let i = 0; i < titleLines.length; i++) {
                doc.text(titleLines[i], margin, currentY);
                currentY += 5;
            }
            currentY += 3;

            if (img && img.src && !img.src.includes('data:image/svg')) {
                try {
                    // Get image data
                    const imgData = await this.getImageData(img.src);
                    
                    // Calculate image dimensions to fit content width
                    let imgWidth = contentWidth;
                    let imgHeight = (img.naturalHeight * contentWidth) / img.naturalWidth;
                    
                    // Limit image height to prevent it from being too large
                    const maxImageHeight = 80;
                    if (imgHeight > maxImageHeight) {
                        const ratio = maxImageHeight / imgHeight;
                        imgHeight = maxImageHeight;
                        imgWidth = imgWidth * ratio;
                    }

                    // Check if image fits on current page
                    if (currentY + imgHeight > pageHeight - 10) {
                        doc.addPage();
                        currentY = margin;
                    }

                    // Add image (centered)
                    const imageX = margin + (contentWidth - imgWidth) / 2;
                    doc.addImage(
                        imgData, 
                        'PNG', 
                        imageX,
                        currentY, 
                        imgWidth, 
                        imgHeight
                    );
                    
                    currentY += imgHeight + 5;

                } catch (error) {
                    console.warn('Failed to add image:', error);
                    this.addErrorMessage(doc, margin, currentY, 'Image could not be loaded');
                    currentY += 10;
                }
            } else {
                // No image available
                this.addErrorMessage(doc, margin, currentY, 'Image not available');
                currentY += 10;
            }

            // Add insight text
            doc.setFontSize(10);
            doc.setFont('helvetica', 'normal');
            doc.setTextColor(0, 0, 0);

            const insightLines = doc.splitTextToSize(insight, contentWidth);
            
            for (let i = 0; i < insightLines.length; i++) {
                // Check if we need a new page for text
                if (currentY > pageHeight - 10) {
                    doc.addPage();
                    currentY = margin;
                }
                
                doc.text(insightLines[i], margin, currentY);
                currentY += 5;
            }

            // Add separator between images (if there's space)
            if (currentY < pageHeight - 15) {
                doc.setDrawColor(200, 200, 200);
                doc.setLineWidth(0.1);
                doc.line(margin, currentY + 2, margin + contentWidth, currentY + 2);
                currentY += 10;
            } else {
                doc.addPage();
                currentY = margin;
            }
        }

        return currentY;
    }

    calculateTextHeight(doc, text, maxWidth, fontSize) {
        doc.setFontSize(fontSize);
        const lines = doc.splitTextToSize(text, maxWidth);
        return lines.length * (fontSize * 0.35); // Approximate line height
    }

    addErrorMessage(doc, x, y, message) {
        doc.setFontSize(10);
        doc.setFont('helvetica', 'italic');
        doc.setTextColor(231, 76, 60);
        doc.text(message, x, y);
    }

    async getImageData(url) {
        return new Promise((resolve, reject) => {
            const img = new Image();
            img.crossOrigin = 'Anonymous';
            img.onload = () => {
                const canvas = document.createElement('canvas');
                const ctx = canvas.getContext('2d');
                canvas.width = img.width;
                canvas.height = img.height;
                ctx.drawImage(img, 0, 0);
                
                // Convert to JPEG for better PDF compression
                try {
                    resolve(canvas.toDataURL('image/jpeg', 0.8));
                } catch (e) {
                    // Fallback to PNG if JPEG fails
                    resolve(canvas.toDataURL('image/png'));
                }
            };
            img.onerror = reject;
            img.src = url;
        });
    }

    downloadPdf(blob, filename) {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        
        // Clean up
        setTimeout(() => {
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        }, 100);
    }

    showLoading() {
        let loading = document.getElementById('loading');
        if (!loading) {
            loading = document.createElement('div');
            loading.id = 'loading';
            loading.className = 'loading';
            loading.innerHTML = `
                <div class="spinner"></div>
                <p>Generating PDF... This may take a moment</p>
            `;
            document.body.appendChild(loading);
        }
        loading.style.display = 'block';
    }

    hideLoading() {
        const loading = document.getElementById('loading');
        if (loading) {
            loading.style.display = 'none';
        }
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    new ReportGenerator();
});