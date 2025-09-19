const fileInput = document.getElementById('fileUpload');
const fileNameSpan = document.getElementById('file-name');
const fileInfoBox = document.getElementById('file-info-box');
const removeFileBtn = document.getElementById('remove-file-btn');
const uploadBoxMain = document.getElementById('upload-box-main');
const responseContainer = document.getElementById('response-container');
const commandInput = document.getElementById('command-line'); // matches HTML
const submitBtn = document.getElementById('process-btn');      // matches HTML
const uploadForm = document.getElementById('upload-form');

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

async function uploadWithTimeout(resource, options = {}) {
  const { timeout = 10000 } = options;
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeout);
  const response = await fetch(resource, {
    ...options,
    signal: controller.signal  
  });
  clearTimeout(id);
  return response;
}

uploadForm.addEventListener('submit', async function(event) {
  event.preventDefault(); 

  if (fileInput.files.length === 0) {
    alert("Please select a file to upload");
    return;
  }

  const file = fileInput.files[0];
  const formData = new FormData();
  formData.append('file', file);

  const commandVal = commandInput.value.trim();
  if (commandVal) {
    formData.append('command', commandVal);
  }

  try {
    submitBtn.disabled = true;
    submitBtn.textContent = 'Uploading...';

    const response = await uploadWithTimeout('/upload', {
      method: 'POST',
      body: formData,
      timeout: 15000,
    });

    if (response.ok) {
      const data = await response.json();
      if (data.redirect_url) {
        // Navigate to workflow monitor first
        window.location.href = data.redirect_url;
      } else {
        window.location.href = '/workflow_monitor';
      }
    } else {
      const errorData = await response.json();
      responseContainer.innerHTML = `<p style="color:red;">Upload failed: ${errorData.error || response.statusText}</p>`;
    }
  } catch (error) {
    if (error.name === 'AbortError') {
      responseContainer.innerHTML = `<p style="color:red;">Upload timed out.</p>`;
    } else {
      responseContainer.innerHTML = `<p style="color:red;">Upload failed: ${error.message}</p>`;
    }
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = 'Analyze Data';
  }
});