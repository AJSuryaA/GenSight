document.addEventListener('DOMContentLoaded', function() {
  const workflowCanvas = document.getElementById('workflowCanvas');
  const connectionLayer = document.getElementById('connectionLayer');
  const zoomInBtn = document.getElementById('zoomInBtn');
  const zoomOutBtn = document.getElementById('zoomOutBtn');
  const resetZoomBtn = document.getElementById('resetZoomBtn');
  const resetViewBtn = document.getElementById('resetViewBtn');
  const liveViewBtn = document.getElementById('liveViewBtn');
  const liveViewPanel = document.getElementById('liveViewPanel');
  const liveViewContent = document.getElementById('liveViewContent');
  
  const urlParams = new URLSearchParams(window.location.search);
  const taskId = urlParams.get('task_id');
  
  let scale = 0.8;
  let posX = 100;
  let posY = 100;
  let isDragging = false;
  let startX, startY;

  liveViewPanel.style.display = "none";
  
  // Define the workflow nodes based on the provided PDF
  const workflowNodes = [
    { 
      id: "user-label", 
      type: "text",
      content: "USER", 
      x: 450, 
      y: 25
    },
    { 
      id: 1, 
      title: "File upload", 
      x: 430, 
      y: 40, 
      width: 140,
      height: 40
    },
    { 
      id: 2, 
      type: "diamond",
      title: "pandas / pyspark", 
      x: 500, 
      y: 170, 
      size: 80
    },
    { 
      id: 3, 
      title: "File upload: local", 
      x: 190, 
      y: 310, 
      width: 160,
      height: 40
    },
    { 
      id: 4, 
      title: "EDA", 
      x: 190, 
      y: 385, 
      width: 160,
      height: 40
    },
    { 
      id: 5, 
      title: "Hadoop Status", 
      x: 620, 
      y: 310, 
      width: 160,
      height: 40
    },
    { 
      id: 6, 
      title: "Start hdfs, yarn", 
      x: 820, 
      y: 310, 
      width: 140,
      height: 40
    },
    { 
      id: 7, 
      title: "File upload: hdfs", 
      x: 620, 
      y: 385, 
      width: 160,
      height: 40
    },
    { 
      id: 8, 
      title: "EDA", 
      x: 620, 
      y: 460, 
      width: 160,
      height: 40
    },
    { 
      id: "panel-left", 
      type: "panel",
      x: 160, 
      y: 280, 
      width: 220,
      height: 180
    },
    { 
      id: "panel-right", 
      type: "panel",
      x: 590, 
      y: 280, 
      width: 400,
      height: 255
    },
    { 
      id: 9, 
      title: "AI - 1", 
      description: "Data cleaning",
      x: 340, 
      y: 645, 
      width: 100,
      height: 50
    },
    { 
      id: 10, 
      title: "Phrase AI data", 
      x: 500, 
      y: 645, 
      width: 160,
      height: 50
    },
    { 
      id: "panel-ai1", 
      type: "panel",
      x: 300, 
      y: 620, 
      width: 400,
      height: 100
    },
    { 
      id: 11, 
      title: "Data cleaning", 
      x: 220, 
      y: 800, 
      width: 160,
      height: 40
    },
    { 
      id: 12, 
      title: "Save cleaned data", 
      x: 220, 
      y: 875, 
      width: 160,
      height: 40
    },
    { 
      id: 13, 
      title: "Data cleaning", 
      x: 640, 
      y: 800, 
      width: 160,
      height: 40
    },
    { 
      id: 14, 
      title: "Save cleaned data", 
      x: 640, 
      y: 875, 
      width: 160,
      height: 40
    },
    { 
      id: 15, 
      title: "AI - 2", 
      description: "Visualization",
      x: 340, 
      y: 1025, 
      width: 100,
      height: 50
    },
    { 
      id: 16, 
      title: "Phrase AI data", 
      x: 500, 
      y: 1025, 
      width: 160,
      height: 50
    },
    { 
      id: "panel-ai2", 
      type: "panel",
      x: 300, 
      y: 1000, 
      width: 400,
      height: 100
    },
    { 
      id: 17, 
      title: "Visualization", 
      x: 420, 
      y: 1170, 
      width: 160,
      height: 40
    },
    { 
      id: 18, 
      title: "Save plots", 
      x: 420, 
      y: 1245, 
      width: 160,
      height: 40
    },
    { 
      id: 19, 
      title: "AI - 3", 
      description: "Insights",
      x: 340, 
      y: 1375, 
      width: 100,
      height: 50
    },
    { 
      id: 20, 
      title: "Phrase AI data", 
      x: 500, 
      y: 1375, 
      width: 160,
      height: 50
    },
    { 
      id: "panel-ai3", 
      type: "panel",
      x: 300, 
      y: 1350, 
      width: 400,
      height: 100
    },
    { 
      id: 21, 
      title: "Generate report", 
      x: 420, 
      y: 1520, 
      width: 160,
      height: 40
    }
  ];
  
  // Define connections between nodes
  const connections = [
    { from: 1, to: 2 },
    { from: 2, to: "panel-left", breakY: 170, fromSide: "left", toSide: "top" },
    { from: 2, to: "panel-right", breakY: 250, fromSide: "right", toSide: "top" },
    { from: 3, to: 4, fromSide: "bottom", toSide: "top" },
    { from: 5, to: 6,  fromSide: "right", toSide: "left" },
    { from: 5, to: 7,  fromSide: "bottom", toSide: "top" },
    { from: 6, to: 7, fromSide: "bottom", toSide: "right" },
    { from: 7, to: 8, fromSide: "bottom", toSide: "top" },
    { from: "panel-left", to: "panel-ai1", breakY: 580, fromSide: "bottom", toSide: "top-20" },
    { from: "panel-right", to: "panel-ai1", breakY: 580, fromSide: "bottom", toSide: "top-80" },
    { from: 9, to: 10, breakY: 400, fromSide: "right", toSide: "left" },
    { from: "panel-ai1", to: 11, breakY: 765, fromSide: "bottom-20", toSide: "top" },
    { from: "panel-ai1", to: 13, breakY: 765, fromSide: "bottom-80", toSide: "top" },
    { from: 11, to: 12, fromSide: "bottom", toSide: "top" },
    { from: 13, to: 14, fromSide: "bottom", toSide: "top" },
    { from: 12, to: "panel-ai2", breakY: 960, fromSide: "bottom", toSide: "top-20" },
    { from: 14, to: "panel-ai2", breakY: 960, fromSide: "bottom", toSide: "top-80" },
    { from: 15, to: 16, breakY: 600, fromSide: "right", toSide: "left" },
    { from: "panel-ai2", to: 17, fromSide: "bottom", toSide: "top" },
    { from: 17, to: 18, fromSide: "bottom", toSide: "top" },
    { from: 18, to: "panel-ai3",  fromSide: "bottom", toSide: "top" },
    { from: 19, to: 20 , breakY: 450, fromSide: "right", toSide: "left" },
    { from: "panel-ai3", to: 21, fromSide: "bottom", toSide: "top" }
  ];

  // Initialize the workflow
  function initWorkflow() {
    renderWorkflow();
    setupEventListeners();
    updateTransform();
    
    // Start processing if task ID is present
    if (taskId) {
      setTimeout(() => {
        startProcessing(taskId);
        monitorProcessing(taskId);
      }, 1000);
    }
  }
  
  // Function to start processing
  function startProcessing(taskId) {
    fetch(`/start_processing/${taskId}`, {
      method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
      console.log('Processing started:', data);
      addLiveViewMessage('Processing started...');
    })
    .catch(error => {
      console.error('Error starting processing:', error);
      addLiveViewMessage('Error starting processing: ' + error.message, 'error');
    });
  }
  
  // Function to monitor processing status
  function monitorProcessing(taskId) {
    const checkStatus = () => {
      fetch(`/processing_status/${taskId}`)
        .then(response => response.json())
        .then(data => {
          console.log('Processing status:', data.status);
          
          // Update UI based on status
          updateWorkflowUI(data.status);
          addLiveViewMessage(`Status: ${data.status}`);
          
          // Continue monitoring if not completed
          if (data.status !== 'completed' && data.status !== 'error') {
            setTimeout(checkStatus, 2000); // Check every 2 seconds
          } else if (data.status === 'completed') {
            addLiveViewMessage('Processing completed successfully!', 'success');
          } else if (data.status === 'error') {
            addLiveViewMessage(`Error: ${data.error}`, 'error');
          }
        })
        .catch(error => {
          console.error('Error checking status:', error);
          addLiveViewMessage('Error checking status: ' + error.message, 'error');
          setTimeout(checkStatus, 5000); // Retry after 5 seconds on error
        });
    };
    
    checkStatus();
  }
  
  // Function to update workflow UI based on status
  function updateWorkflowUI(status) {
    // Implement your UI updates here based on processing status
    console.log('Updating UI for status:', status);
    
    // Example: Highlight nodes based on status
    const statusNodeMap = {
      'uploaded': [1],
      'processing': [2, 3, 4, 5, 6, 7, 8],
      'completed': Array.from({length: 21}, (_, i) => i + 1) // All nodes
    };
    
    // Reset all nodes first
    document.querySelectorAll('.node, .diamond').forEach(node => {
      node.classList.remove('active', 'completed', 'error');
    });
    
    // Highlight nodes based on current status
    if (statusNodeMap[status]) {
      statusNodeMap[status].forEach(nodeId => {
        const nodeElement = document.getElementById(`node-${nodeId}`);
        if (nodeElement) {
          nodeElement.classList.add('active');
        }
      });
    }
  }
  
  // Function to add messages to live view panel
  function addLiveViewMessage(message, type = 'info') {
    if (!liveViewContent) return;
    
    const messageElement = document.createElement('div');
    messageElement.className = `live-message ${type}`;
    messageElement.innerHTML = `
      <span class="timestamp">${new Date().toLocaleTimeString()}</span>
      <span class="message">${message}</span>
    `;
    
    liveViewContent.appendChild(messageElement);
    liveViewContent.scrollTop = liveViewContent.scrollHeight;
  }
  
  // Render workflow nodes and connections
  function renderWorkflow() {
    // Clear canvas
    connectionLayer.innerHTML = '';
    
    // Create panels first (so they appear behind nodes)
    workflowNodes.filter(node => node.type === "panel").forEach(panel => {
      createPanel(panel);
    });
    
    // Create nodes
    workflowNodes.filter(node => node.type !== "panel").forEach(node => {
      if (node.type === "diamond") {
        createDiamond(node);
      } else if (node.type === "text") {
        createText(node);
      } else {
        createNode(node);
      }
    });
    
    // Create connections next
    connections.forEach(conn => {
      createConnection(conn.from, conn.to, conn.breakY, conn.fromSide, conn.toSide);
    });
  }
  
  // Create a node element
  function createNode(node) {
    const nodeElement = document.createElement('div');
    nodeElement.className = 'node';
    nodeElement.style.left = `${node.x}px`;
    nodeElement.style.top = `${node.y}px`;
    nodeElement.style.width = `${node.width}px`;
    nodeElement.style.height = `${node.height}px`;
    nodeElement.id = `node-${node.id}`;
    nodeElement.dataset.id = node.id;
    
    let html = `<div class="node-title">${node.title}</div>`;
    if (node.description) {
      html += `<div class="node-description">${node.description}</div>`;
    }
    
    nodeElement.innerHTML = html;
    workflowCanvas.appendChild(nodeElement);
  }
  
  // Create a diamond element
  function createDiamond(node) {
    const diamondElement = document.createElement('div');
    diamondElement.className = 'diamond';
    diamondElement.style.left = `${node.x - node.size/2}px`;
    diamondElement.style.top = `${node.y - node.size/2}px`;
    diamondElement.style.width = `${node.size}px`;
    diamondElement.style.height = `${node.size}px`;
    diamondElement.id = `node-${node.id}`;
    diamondElement.dataset.id = node.id;
    
    const content = document.createElement('div');
    content.className = 'diamond-content';
    content.innerHTML = node.title;
    
    diamondElement.appendChild(content);
    workflowCanvas.appendChild(diamondElement);
  }
  
  // Create a text element
  function createText(node) {
    const textElement = document.createElement('div');
    textElement.style.position = 'absolute';
    textElement.style.left = `${node.x}px`;
    textElement.style.top = `${node.y}px`;
    textElement.style.color = '#8b949e';
    textElement.style.fontSize = '12px';
    textElement.style.textAnchor = 'middle';
    textElement.textContent = node.content;
    textElement.style.transform = 'translate(-50%, 0)';
    
    workflowCanvas.appendChild(textElement);
  }
  
  // Create a panel element
  function createPanel(panel) {
    const panelElement = document.createElement('div');
    panelElement.className = 'panel';
    panelElement.style.left = `${panel.x}px`;
    panelElement.style.top = `${panel.y}px`;
    panelElement.style.width = `${panel.width}px`;
    panelElement.style.height = `${panel.height}px`;
    
    workflowCanvas.appendChild(panelElement);
  }
  
  // Get anchor point for a node
  function getAnchor(node, side) {
    if (node.type === "diamond") {
      if (side === "top") return { x: node.x, y: node.y - node.size/2 };
      if (side === "bottom") return { x: node.x, y: node.y + node.size/2 };
      if (side === "left") return { x: node.x - node.size/2, y: node.y };
      if (side === "right") return { x: node.x + node.size/2, y: node.y };
    } else {
      if (side.startsWith("top")) {
        let fraction = parseFloat(side.split("-")[1]) / 100 || 0.5; 
        return { x: node.x + node.width * fraction, y: node.y };
      }
      if (side.startsWith("bottom")) {
        let fraction = parseFloat(side.split("-")[1]) / 100 || 0.5;
        return { x: node.x + node.width * fraction, y: node.y + node.height };
      }
      if (side.startsWith("left")) {
        let fraction = parseFloat(side.split("-")[1]) / 100 || 0.5;
        return { x: node.x, y: node.y + node.height * fraction };
      }
      if (side.startsWith("right")) {
        let fraction = parseFloat(side.split("-")[1]) / 100 || 0.5;
        return { x: node.x + node.width, y: node.y + node.height * fraction };
      }
    }
    return { x: node.x + node.width/2, y: node.y + node.height/2 };
  }
  
  // Create a connection between nodes
  function createConnection(fromId, toId, breakY, fromSide = "bottom", toSide = "top") {
    const fromNode = workflowNodes.find(n => n.id === fromId);
    const toNode = workflowNodes.find(n => n.id === toId);
    
    if (!fromNode || !toNode) return;
    
    const start = getAnchor(fromNode, fromSide);
    const end = getAnchor(toNode, toSide);
    
    // Calculate intermediate points for right-angle connections
    let d = "";
    
    if (fromSide.startsWith("bottom") && toSide.startsWith("top")) {
      // Vertical to vertical connection
      const midY = breakY || ((start.y + end.y) / 2);
      d = `M ${start.x} ${start.y} L ${start.x} ${midY} L ${end.x} ${midY} L ${end.x} ${end.y}`;
    } else if (fromSide.startsWith("right") && toSide.startsWith("left")) {
      // Horizontal to horizontal connection
      const midX = breakY || ((start.x + end.x) / 2);
      d = `M ${start.x} ${start.y} L ${midX} ${start.y} L ${midX} ${end.y} L ${end.x} ${end.y}`;
    } else if (fromSide.startsWith("right") && toSide.startsWith("top")) {
      // Horizontal to vertical connection
      d = `M ${start.x} ${start.y} L ${end.x} ${start.y} L ${end.x} ${end.y}`;
    } else if (fromSide.startsWith("bottom") && toSide.startsWith("left")) {
      // Vertical to horizontal connection
      d = `M ${start.x} ${start.y} L ${start.x} ${end.y} L ${end.x} ${end.y}`;
    } else if (fromSide.startsWith("bottom") && toSide.startsWith("right")) {
      // Vertical to horizontal connection (right side)
      d = `M ${start.x} ${start.y} L ${start.x} ${end.y} L ${end.x} ${end.y}`;
    } else {
      // Default right-angle connection
      const midY = breakY || ((start.y + end.y) / 2);
      d = `M ${start.x} ${start.y} L ${start.x} ${midY} L ${end.x} ${midY} L ${end.x} ${end.y}`;
    }
    
    const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
    path.setAttribute("d", d);
    path.setAttribute("fill", "none");
    path.setAttribute("stroke", "#bbbbbb");
    path.setAttribute("stroke-width", "4");
    connectionLayer.appendChild(path);
  }
  
  // Setup event listeners for zoom and pan
  function setupEventListeners() {
    // Zoom with buttons
    zoomInBtn.addEventListener('click', () => adjustZoom(0.1));
    zoomOutBtn.addEventListener('click', () => adjustZoom(-0.1));
    resetZoomBtn.addEventListener('click', resetZoom);
    resetViewBtn.addEventListener('click', resetView);
    
    // Zoom with mouse wheel
    workflowCanvas.addEventListener('wheel', (e) => {
      e.preventDefault();
      adjustZoom(e.deltaY * -0.002);
    });
    
    // Pan with mouse drag
    workflowCanvas.addEventListener('mousedown', (e) => {
      if (e.button === 0) {
        isDragging = true;
        startX = e.clientX - posX;
        startY = e.clientY - posY;
        workflowCanvas.style.cursor = 'grabbing';
      }
    });
    
    document.addEventListener('mousemove', (e) => {
      if (isDragging) {
        posX = e.clientX - startX;
        posY = e.clientY - startY;
        updateTransform();
      }
    });
    
    document.addEventListener('mouseup', () => {
      isDragging = false;
      workflowCanvas.style.cursor = 'default';
    });
    
    // Toggle live view panel
    liveViewBtn.addEventListener('click', () => {
      liveViewPanel.style.display = liveViewPanel.style.display === 'none' ? 'block' : 'none';
    });
  }
  
  // Adjust zoom level
  function adjustZoom(amount) {
    scale += amount;
    scale = Math.min(Math.max(0.3, scale), 3);
    updateTransform();
  }
  
  // Reset zoom level
  function resetZoom() {
    scale = 0.8;
    updateTransform();
  }
  
  // Reset view (zoom and position)
  function resetView() {
    scale = 0.8;
    posX = 100;
    posY = 100;
    updateTransform();
  }
  
  // Update canvas transform
  function updateTransform() {
    workflowCanvas.style.transform = `translate(${posX}px, ${posY}px) scale(${scale})`;
  }
  
  // Initialize the workflow
  initWorkflow();
});