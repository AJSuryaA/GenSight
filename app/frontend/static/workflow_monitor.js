// Workflow Monitor JavaScript
document.addEventListener('DOMContentLoaded', function () {
  const workflowCanvas = document.getElementById('workflowCanvas');
  const connectionLayer = document.getElementById('connectionLayer');
  const zoomInBtn = document.getElementById('zoomInBtn');
  const zoomOutBtn = document.getElementById('zoomOutBtn');
  const resetZoomBtn = document.getElementById('resetZoomBtn');
  const resetViewBtn = document.getElementById('resetViewBtn');
  const liveViewBtn = document.getElementById('liveViewBtn');
  const liveViewPanel = document.getElementById('liveViewPanel');
  const processContainer = document.getElementById('processContainer');
  const scrollIndicator = document.getElementById('scrollIndicator');

  const urlParams = new URLSearchParams(window.location.search);
  const taskId = urlParams.get('task_id');

  let scale = 0.8;
  let posX = 400;
  let posY = 730;
  let isDragging = false;
  let startX, startY;
  let lastFileSize = 0;
  let logMonitoringInterval = null;
  let processStates = {};
  let processQueue = [];
  let isProcessingQueue = false;
  let autoScroll = true;

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
    { from: 1, to: 2 },//
    { from: 2, to: "panel-left", breakY: 170, fromSide: "left", toSide: "top" },
    { from: 2, to: "panel-right", breakY: 250, fromSide: "right", toSide: "top" },
    { from: 3, to: 4, fromSide: "bottom", toSide: "top" },
    { from: 5, to: 6, fromSide: "right", toSide: "left" },
    { from: 5, to: 7, fromSide: "bottom", toSide: "top" },
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
    { from: 18, to: "panel-ai3", fromSide: "bottom", toSide: "top" },
    { from: 19, to: 20, breakY: 450, fromSide: "right", toSide: "left" },
    { from: "panel-ai3", to: 21, fromSide: "bottom", toSide: "top" }
  ];

  // Initialize the workflow
  function initWorkflow() {
    renderWorkflow();
    setupEventListeners();
    updateTransform();

    // Start log monitoring
    startLogMonitoring();

    // Start processing if task ID is present
    if (taskId) {
      setTimeout(() => {
        startProcessing(taskId);
        monitorProcessing(taskId);
      }, 1000);
    }
  }

  // Function to start log monitoring
  function startLogMonitoring() {
    // Clear any existing interval
    if (logMonitoringInterval) {
      clearInterval(logMonitoringInterval);
    }

    // Check for log updates every 3 seconds
    logMonitoringInterval = setInterval(checkLogUpdates, 3000);

    // Initial check
    checkLogUpdates();
  }

  // Function to check for log updates
  function checkLogUpdates() {
    fetch('/logs/mylog.jsonl', {
      cache: 'no-store',
      headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
      }
    })
      .then(response => {
        if (!response.ok) throw new Error('Failed to fetch log file');
        return response.text();
      })
      .then(text => {
        if (!text) return;

        // Check if file size has changed
        if (text.length === lastFileSize) return;

        // Process only new content
        const newContent = text.slice(lastFileSize);
        lastFileSize = text.length;

        // Process each line individually
        const lines = newContent.split('\n');

        lines.forEach(line => {
          if (line.trim()) {
            try {
              // Try to parse as JSON
              const logEntry = JSON.parse(line);
              processLogEntry(logEntry);
            } catch (e) {
              // If not valid JSON, display as raw text
              appendRawLog(line);
            }
          }
        });
      })
      .catch(error => {
        console.error('Error fetching logs:', error);
      });
  }

  function blinkNode(nodeId) {
    const nodeElement = document.getElementById(`node-${nodeId}`);
    if (nodeElement) {
      nodeElement.classList.add('blink-highlight-node');
      console.log(`Blinking node ${nodeId}`);
    } else {
      console.warn(`Node ${nodeId} not found for blinking`);
    }
  }

  function stopBlinkNode(nodeId) {
    const nodeElement = document.getElementById(`node-${nodeId}`);
    if (nodeElement) {
      nodeElement.classList.remove('blink-highlight-node');
      console.log(`Stopped blinking node ${nodeId}`);
    }
  }

  function highlightNodeGreen(nodeId) {
    const nodeElement = document.getElementById(`node-${nodeId}`);
    if (nodeElement) {
      nodeElement.classList.add('green-highlight-node');
      console.log(`Highlighted node ${nodeId} in green`);
    } else {
      console.warn(`Node ${nodeId} not found for green highlight`);
    }
  }

  function removeGreenHighlightNode(nodeId) {
    const nodeElement = document.getElementById(`node-${nodeId}`);
    if (nodeElement) {
      nodeElement.classList.remove('green-highlight-node');
      console.log(`Removed green highlight from node ${nodeId}`);
    }
  }

  // Process a log entry and display it with proper formatting
  function processLogEntry(logEntry) {
    // Extract process name and messages
    const processName = Object.keys(logEntry)[0];
    const messages = logEntry[processName];

    // Check if "final" is present at the 3rd index (index 3)
    if (messages.length > 3 && messages[3] === "final") {
      console.log(`Final process detected: ${processName}`);

      // Extract the values from index 0, 2, and 4
      const index0 = Object.keys(logEntry)[0];
      const index2 = messages[2];
      const functionName = messages[4];

      // Add to queue as a final item (but don't redirect immediately)
      processQueue.push({
        type: 'final',
        name: processName,
        functionName: functionName,
        arg1: index0,
        arg2: index2,
        messages: messages // Include messages for printing
      });
    }
    // Check if "none" is present at the 3rd index (index 3)
    else if (messages.length > 3 && messages[3] === "none") {
      console.log(`Redirecting process ${processName} because "none" found at index 3`);

      // Extract the values from index 0, 2, and 4
      const index0 = Object.keys(logEntry)[0];
      const index2 = messages[2];
      const functionName = messages[4];

      // Add to function queue
      processQueue.push({
        type: 'function',
        name: processName,
        functionName: functionName,
        arg1: index0,
        arg2: index2
      });
    } else {
      // Add to process queue for normal printing
      processQueue.push({
        type: 'process',
        name: processName,
        messages: messages
      });
    }

    // Start processing queue if not already running
    if (!isProcessingQueue) {
      processQueueSequentially();
    }
  }

  // Function to trigger specific functions based on the function name
  // Function to trigger specific functions based on the function name
  function triggerFunction(functionName, arg1, arg2) {
    console.log(`Triggering function: ${functionName} with args: ${arg1}, ${arg2}`);

    // Remove any parentheses and extract the clean function name
    const cleanFunctionName = functionName.replace(/\(.*\)/, '').trim();

    // Map function names to actual function calls
    switch (cleanFunctionName) {
      case "blinkNode":
        if (arg1) {
          // Remove green highlight from this specific node first
          removeGreenHighlightNode(arg1);
          blinkNode(arg1);
        }
        break;

      case "highlightNodeGreen":
        if (arg1) {
          // Stop blinking on this specific node first
          stopBlinkNode(arg1);
          highlightNodeGreen(arg1);
        }
        break;

      case "setConnectionYellowGlow":
        if (arg1 && arg2) setConnectionYellowGlow(arg1, arg2);
        break;

      case "setConnectionGreen":
        if (arg1 && arg2) setConnectionGreen(arg1, arg2);
        break;

      case "stopBlinkNode":
        if (arg1) stopBlinkNode(arg1);
        break;

      case "removeGreenHighlightNode":
        if (arg1) removeGreenHighlightNode(arg1);
        break;

      case "redirecthtml":
        // Handle redirecthtml if it comes as a function
        redirecthtml();
        break;

      default:
        console.warn(`Unknown function: ${functionName}`);
        // Try to call it anyway if it exists in global scope
        if (typeof window[cleanFunctionName] === 'function') {
          window[cleanFunctionName](arg1, arg2);
        }
        break;
    }
  }

  // Process the queue sequentially with delays
  async function processQueueSequentially() {
    isProcessingQueue = true;

    while (processQueue.length > 0) {
      const item = processQueue.shift();

      if (item.type === 'process') {
        // Normal process - wait for it to complete
        await renderProcess(item.name, item.messages);

        // Wait before processing next item
        await new Promise(resolve => setTimeout(resolve, 500));
      }
      else if (item.type === 'function') {
        // Function call - execute immediately
        triggerFunction(item.functionName, item.arg1, item.arg2);

        // Small delay before next item
        await new Promise(resolve => setTimeout(resolve, 100));
      }
      else if (item.type === 'final') {
        console.log("Processing final log item...");

        // First, print the final process messages normally
        await renderProcess(item.name, item.messages);

        // Then trigger the function if specified
        if (item.functionName && item.functionName !== "print entirely") {
          triggerFunction(item.functionName, item.arg1, item.arg2);
        }

        // Wait a bit to ensure everything is displayed
        await new Promise(resolve => setTimeout(resolve, 1000));

        // Now stop monitoring and redirect (this is the last item)
        redirecthtml();

        // Break the loop since this is the final item
        break;
      }
    }

    isProcessingQueue = false;
  }

  // Render a process with its messages
  async function renderProcess(processName, messages) {
    return new Promise(async (resolve) => {
      // Get or create process container
      let processElement = document.getElementById(`process-${processName}`);
      if (!processElement) {
        processElement = createProcessContainer(processName);
      }

      // Update status to running (YELLOW)
      const statusElement = processElement.querySelector('.process-status');
      statusElement.textContent = 'Running';
      statusElement.className = 'process-status process-running';

      // Get the process content area
      const processContent = processElement.querySelector('.process-content');

      // Clear previous content
      processContent.innerHTML = '';

      // Process messages with delays
      for (let i = 0; i < messages.length; i++) {
        const message = messages[i];

        // Skip control messages
        if (message === "print entirely" || message === "type effect" || message === "final" || message === "none") {
          continue;
        }

        // Check if next message is a control instruction
        const nextMessage = i + 1 < messages.length ? messages[i + 1] : null;
        const hasTypeEffect = nextMessage === "type effect";

        // Add message with appropriate effect
        if (hasTypeEffect) {
          await appendMessageWithTypeEffect(processContent, message);
          i++; // Skip the control message
        } else {
          await appendMessage(processContent, message);
        }
      }

      // Update status to completed (GREEN)
      statusElement.textContent = 'Completed';
      statusElement.className = 'process-status process-completed';

      // Auto-scroll to bottom if enabled
      if (autoScroll) {
        scrollToBottom();
      }

      // Resolve the promise to indicate completion
      resolve();
    });
  }

  // Create a process container
  function createProcessContainer(processName) {
    const processElement = document.createElement('div');
    processElement.className = 'process-container';
    processElement.id = `process-${processName}`;

    processElement.innerHTML = `
          <div class="process-header">
            <div>
              <i class="fas fa-cogs"></i>
              ${processName}
            </div>
            <span class="process-status">Waiting</span>
          </div>
          <div class="process-content"></div>
        `;

    processContainer.appendChild(processElement);

    // Auto-scroll to bottom if enabled
    if (autoScroll) {
      scrollToBottom();
    }

    return processElement;
  }

  // Append a message with type effect
  async function appendMessageWithTypeEffect(container, message) {
    return new Promise(resolve => {
      const messageLine = document.createElement('div');
      messageLine.className = 'log-line log-info';

      // Create message content with cursor
      const messageContent = document.createElement('span');
      messageContent.textContent = '';

      // Create blinking cursor
      const cursor = document.createElement('span');
      cursor.className = 'blink-cursor';

      messageLine.appendChild(messageContent);
      messageLine.appendChild(cursor);
      container.appendChild(messageLine);

      // Scroll to bottom if auto-scroll is enabled
      if (autoScroll) {
        scrollToBottom();
      }

      // Type out the message character by character
      let i = 0;
      const typeInterval = setInterval(() => {
        if (i < message.length) {
          messageContent.textContent += message.charAt(i);
          i++;

          // Keep scrolling to bottom as text expands if auto-scroll is enabled
          if (autoScroll) {
            scrollToBottom();
          }
        } else {
          clearInterval(typeInterval);
          messageLine.removeChild(cursor);
          resolve();
        }
      }, 10); // Adjust typing speed here (milliseconds per character)
    });
  }

  // Append a message normally
  async function appendMessage(container, message) {
    return new Promise(resolve => {
      const messageLine = document.createElement('div');
      messageLine.className = 'log-line log-info';
      messageLine.textContent = message;

      container.appendChild(messageLine);

      // Scroll to bottom if auto-scroll is enabled
      if (autoScroll) {
        scrollToBottom();
      }

      // Resolve after a short delay
      setTimeout(resolve, 100);
    });
  }

  // Function to scroll to bottom
  function scrollToBottom() {
    processContainer.scrollTop = processContainer.scrollHeight;
  }

  // Function to append raw log text
  function appendRawLog(text) {
    const rawLogElement = document.createElement('div');
    rawLogElement.className = 'log-line log-info';
    rawLogElement.textContent = text;
    processContainer.appendChild(rawLogElement);

    // Scroll to bottom if auto-scroll is enabled
    if (autoScroll) {
      scrollToBottom();
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
      })
      .catch(error => {
        console.error('Error starting processing:', error);
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

          // Continue monitoring if not completed
          if (data.status !== 'completed' && data.status !== 'error') {
            setTimeout(checkStatus, 2000); // Check every 2 seconds
          }
        })
        .catch(error => {
          console.error('Error checking status:', error);
          setTimeout(checkStatus, 5000); // Retry after 5 seconds on error
        });
    };

    checkStatus();
  }

  // Function to update workflow UI based on status
  function updateWorkflowUI(status) {
    // This function can be expanded to update nodes/connections based on status
    console.log('Updating workflow UI for status:', status);
  }

  function setConnectionColor(fromId, toId, color = "yellow-glow") {
    const pathId = `conn-${fromId}-${toId}`;
    const path = document.getElementById(pathId);
    if (!path) {
      console.warn(`Connection path not found: ${pathId}`);
      return;
    }

    // Remove all known connection styling classes
    path.classList.remove("flowline-yellow-glow", "workflow-line-green", "workflow-line-yellow");

    // Add new class based on color argument
    switch (color.toLowerCase()) {
      case "yellow-glow":
        path.classList.add("flowline-yellow-glow");
        break;
      case "green":
        path.classList.add("workflow-line-green");
        break;
      case "yellow":
        path.classList.add("workflow-line-yellow");
        break;
      default:
        // fallback: no special class
        break;
    }

    console.log(`Set connection ${fromId}-${toId} to ${color}`);
  }

  function setConnectionYellowGlow(fromId, toId) {
    setConnectionColor(fromId, toId, "yellow-glow");
  }

  function setConnectionGreen(fromId, toId) {
    setConnectionColor(fromId, toId, "green");
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
    diamondElement.style.left = `${node.x - node.size / 2}px`;
    diamondElement.style.top = `${node.y - node.size / 2}px`;
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
      if (side === "top") return { x: node.x, y: node.y - node.size / 2 };
      if (side === "bottom") return { x: node.x, y: node.y + node.size / 2 };
      if (side === "left") return { x: node.x - node.size / 2, y: node.y };
      if (side === "right") return { x: node.x + node.size / 2, y: node.y };
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
    return { x: node.x + node.width / 2, y: node.y + node.height / 2 };
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
    path.setAttribute("stroke", "#ffffff");
    path.setAttribute("stroke-width", "2");
    path.setAttribute("id", `conn-${fromId}-${toId}`);
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
      const isNowVisible = liveViewPanel.style.display === 'block';
      if (isNowVisible) {
        liveViewPanel.style.display = 'none';
        document.body.classList.remove('live-view-open');
      } else {
        liveViewPanel.style.display = 'block';
        document.body.classList.add('live-view-open');
      }
    });

    // Scroll to bottom button - Fixed positioning
    scrollIndicator.addEventListener('click', () => {
      autoScroll = true;
      scrollToBottom();
      scrollIndicator.classList.remove('visible');
    });

    // Check if user has scrolled up
    processContainer.addEventListener('scroll', () => {
      const isAtBottom = processContainer.scrollHeight - processContainer.clientHeight <= processContainer.scrollTop + 50;

      if (isAtBottom) {
        autoScroll = true;
        scrollIndicator.classList.remove('visible');
      } else {
        autoScroll = false;
        scrollIndicator.classList.add('visible');
      }
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
    posX = 400;
    posY = 730;
    updateTransform();
  }

  // Update canvas transform
  function updateTransform() {
    workflowCanvas.style.transform = `translate(${posX}px, ${posY}px) scale(${scale})`;
  }

  function redirecthtml() {
    console.log("All logs processed. Stopping log monitoring and redirecting...");

    // Stop log monitoring (but don't touch the queue processing)
    if (logMonitoringInterval) {
      clearInterval(logMonitoringInterval);
      logMonitoringInterval = null;
    }

    // Call Flask endpoint to redirect to report after a delay
    setTimeout(() => {
      fetch('/eda_report', {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ taskId: taskId })
      })
        .then(resp => {
          if (resp.redirected) {
            window.location.href = resp.url;
          }
          return resp.json();
        })
        .then(data => {
          if (data.redirectUrl) {
            window.location.href = data.redirectUrl;
          }
        })
        .catch(error => {
          console.error('Error redirecting to report:', error);
          // Fallback redirect after 3 seconds
          setTimeout(() => {
            window.location.href = '/eda_report';
          }, 3000);
        });
    }, 2000); // 2 second delay to ensure everything is visible
  }

  // Initialize the workflow
  initWorkflow();
});