const fileInput = document.getElementById('fileUpload');
const fileNameSpan = document.getElementById('file-name');
const fileInfoBox = document.getElementById('file-info-box');
const removeFileBtn = document.getElementById('remove-file-btn');
const uploadBoxMain = document.getElementById('upload-box-main');
const commandInput = document.getElementById('command-input');
const submitBtn = document.getElementById('submit-btn');
const responseContainer = document.getElementById('response-container');

fileInput.addEventListener('change', function() {
  if (this.files.length > 0) {
    const fileName = this.files[0].name;
    fileNameSpan.textContent = fileName;
    fileInfoBox.style.display = 'flex';
    uploadBoxMain.style.display = 'none';
    responseContainer.innerHTML = ""; // Clear previous response
  }
});

removeFileBtn.addEventListener('click', function() {
  fileInput.value = '';
  fileInfoBox.style.display = 'none';
  uploadBoxMain.style.display = 'flex';
  responseContainer.innerHTML = ""; // Clear previous response
});

submitBtn.addEventListener('click', async function() {
  if (fileInput.files.length === 0) {
    alert("Please select a file to upload");
    return;
  }

  const formData = new FormData();
  formData.append('file', fileInput.files[0]);

  // Append optional command if provided
  const commandVal = commandInput.value.trim();
  if (commandVal) {
    formData.append('command', commandVal);
  }

  try {
    const response = await fetch('/upload', {
      method: 'POST',
      body: formData
    });

    if (response.ok) {
      const data = await response.json();
      responseContainer.innerHTML = `
        <h3>Upload Successful!</h3>
        <p><strong>Filename:</strong> ${data.filename}</p>
        <p><strong>Processing Mode:</strong> ${data.processing_mode}</p>
        <p><strong>Local Path:</strong> ${data.local_path}</p>
        <p><strong>HDFS Path:</strong> ${data.hdfs_path}</p>
      `;
    } else {
      const errorData = await response.json();
      responseContainer.innerHTML = `<p style="color:red;">Upload failed: ${errorData.error || response.statusText}</p>`;
    }
  } catch (error) {
    responseContainer.innerHTML = `<p style="color:red;">Upload failed: ${error.message}</p>`;
  }
});

