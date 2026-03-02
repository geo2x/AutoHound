/**
 * AutoHound — Attack Path Intelligence Engine
 * Copyright (c) 2026 Gordon Prescott. All rights reserved.
 * ACH Research Division
 */

// Particle system for background - Purple Flame Effect
function initParticles() {
  const canvas = document.getElementById('particles');
  const ctx = canvas.getContext('2d');
  
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
  
  const particles = [];
  const maxParticles = 150;
  let time = 0;
  
  // Purple flame color palette
  const flameColors = [
    { name: 'base', r: 45, g: 0, b: 87 },      // #2D0057 - very dark purple
    { name: 'mid', r: 106, g: 13, b: 173 },    // #6A0DAD - deep purple
    { name: 'upper', r: 139, g: 47, b: 201 },  // #8B2FC9 - bright purple
    { name: 'tip', r: 199, g: 125, b: 255 },   // #C77DFF - light purple
    { name: 'flicker', r: 224, g: 176, b: 255 } // #E0B0FF - lavender white
  ];
  
  class FlameParticle {
    constructor() {
      this.reset();
    }
    
    reset() {
      // Start at bottom of screen at random x position
      this.x = Math.random() * canvas.width;
      this.y = canvas.height + Math.random() * 20;
      this.startY = this.y;
      
      // Size starts 8-12px, shrinks as it rises
      this.baseSize = Math.random() * 4 + 8;
      this.size = this.baseSize;
      
      // Move UPWARD (negative vy)
      this.vy = -(Math.random() * 1.5 + 1.5);
      this.vx = (Math.random() - 0.5) * 0.8; // Slight horizontal drift
      
      // Wobble parameters
      this.offset = Math.random() * Math.PI * 2;
      this.wobbleSpeed = Math.random() * 0.05 + 0.05;
      
      // Opacity starts at 0.9, fades to 0
      this.opacity = 0.9;
      this.age = 0;
      this.maxAge = Math.random() * 150 + 100;
    }
    
    update() {
      this.age++;
      
      // Move upward
      this.y += this.vy;
      
      // Wobble left/right
      this.x += this.vx + Math.sin(time * this.wobbleSpeed + this.offset) * 0.5;
      
      // Calculate progress (0 to 1)
      const progress = this.age / this.maxAge;
      
      // Shrink as it rises
      this.size = this.baseSize * (1 - progress * 0.6);
      
      // Fade opacity
      this.opacity = 0.9 * (1 - progress);
      
      // Reset if too old or off screen
      if (this.age >= this.maxAge || this.y < -50) {
        this.reset();
      }
    }
    
    draw() {
      const progress = this.age / this.maxAge;
      
      // Choose color based on height/progress
      let color;
      if (progress < 0.2) {
        color = flameColors[0]; // base - dark purple
      } else if (progress < 0.4) {
        color = flameColors[1]; // mid - deep purple
      } else if (progress < 0.6) {
        color = flameColors[2]; // upper - bright purple
      } else if (progress < 0.8) {
        color = flameColors[3]; // tip - light purple
      } else {
        color = flameColors[4]; // flicker - lavender white
      }
      
      ctx.save();
      ctx.globalAlpha = this.opacity;
      
      // Draw flame shape using bezier curve (teardrop)
      const size = this.size;
      const x = this.x;
      const y = this.y;
      
      // Create gradient for flame
      const gradient = ctx.createLinearGradient(x, y, x, y + size * 4);
      gradient.addColorStop(0, `rgb(${color.r}, ${color.g}, ${color.b})`);
      gradient.addColorStop(0.5, `rgb(${Math.min(255, color.r + 30)}, ${Math.min(255, color.g + 30)}, ${Math.min(255, color.b + 30)})`);
      gradient.addColorStop(1, `rgb(${color.r}, ${color.g}, ${color.b})`);
      
      ctx.fillStyle = gradient;
      
      // Teardrop/flame shape using bezier curves
      ctx.beginPath();
      ctx.moveTo(x, y);
      ctx.bezierCurveTo(x - size, y + size * 2, x - size, y + size * 3, x, y + size * 4);
      ctx.bezierCurveTo(x + size, y + size * 3, x + size, y + size * 2, x, y);
      ctx.closePath();
      ctx.fill();
      
      // Add subtle glow
      if (progress > 0.5) {
        ctx.shadowBlur = 10;
        ctx.shadowColor = `rgba(${color.r}, ${color.g}, ${color.b}, ${this.opacity * 0.5})`;
        ctx.fill();
      }
      
      ctx.restore();
    }
  }
  
  // Initialize particles
  for (let i = 0; i < maxParticles; i++) {
    const particle = new FlameParticle();
    // Spread initial positions
    particle.age = Math.random() * particle.maxAge;
    particle.y = canvas.height - (Math.random() * canvas.height);
    particles.push(particle);
  }
  
  function animate() {
    time++;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Spawn 3-5 new flames per frame along bottom edge
    const spawnCount = Math.floor(Math.random() * 3) + 3;
    for (let i = 0; i < spawnCount && particles.length < maxParticles; i++) {
      particles.push(new FlameParticle());
    }
    
    // Occasionally spawn smaller flames from mid-screen
    if (Math.random() < 0.1) {
      const midFlame = new FlameParticle();
      midFlame.y = canvas.height * 0.5 + (Math.random() - 0.5) * 100;
      midFlame.baseSize = Math.random() * 3 + 4;
      midFlame.size = midFlame.baseSize;
      particles.push(midFlame);
    }
    
    // Update and draw all particles
    particles.forEach((particle, index) => {
      particle.update();
      particle.draw();
    });
    
    // Remove excess particles
    while (particles.length > maxParticles) {
      particles.shift();
    }
    
    requestAnimationFrame(animate);
  }
  
  animate();
  
  // Handle window resize
  window.addEventListener('resize', () => {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  });
}

// Screen management
function showScreen(screenId) {
  document.querySelectorAll('.screen').forEach(screen => {
    screen.classList.remove('active');
  });
  document.getElementById(screenId).classList.add('active');
}

// Screen 1: Splash - auto advance after 3 seconds
setTimeout(() => {
  showScreen('screen-verify');
  runSystemCheck();
}, 3000);

// Screen 2: System verification
let failedChecks = [];

async function runSystemCheck() {
  const { ipcRenderer } = require('electron');
  const checks = ['docker', 'python', 'disk', 'apikey', 'bloodhound'];
  failedChecks = [];
  
  for (let i = 0; i < checks.length; i++) {
    await new Promise(resolve => setTimeout(resolve, 400));
    
    const checkItem = document.querySelector(`[data-check="${checks[i]}"]`);
    checkItem.classList.remove('pending');
    
    let result;
    try {
      switch(checks[i]) {
        case 'docker':
          result = await ipcRenderer.invoke('check-docker');
          break;
        case 'python':
          result = await ipcRenderer.invoke('check-python');
          break;
        case 'disk':
          result = await ipcRenderer.invoke('check-disk-space');
          break;
        case 'apikey':
          result = await ipcRenderer.invoke('check-api-key');
          break;
        case 'bloodhound':
          result = await ipcRenderer.invoke('check-bloodhound');
          break;
      }
      
      if (result.success) {
        checkItem.classList.add('detected');
        
        if (checks[i] === 'disk') {
          checkItem.querySelector('.check-status').textContent = `${result.freeSpaceGB} GB FREE`;
        } 
        else if (checks[i] === 'python') {
          checkItem.querySelector('.check-status').textContent = `PYTHON ${result.versionNum} — DETECTED`;
          checkItem.classList.add('running'); // Gold color
        } 
        else if (checks[i] === 'docker') {
          if (result.running) {
            checkItem.querySelector('.check-status').textContent = 'RUNNING';
            checkItem.classList.add('running'); // Gold color
          } else if (result.installed) {
            checkItem.querySelector('.check-status').textContent = 'NOT RUNNING';
            checkItem.classList.remove('detected');
            checkItem.classList.add('warning'); // Yellow color
            // Add inline "Start Docker" button
            const startBtn = document.createElement('button');
            startBtn.className = 'inline-action-btn';
            startBtn.textContent = 'START DOCKER';
            startBtn.onclick = async () => {
              startBtn.textContent = 'STARTING...';
              startBtn.disabled = true;
              await ipcRenderer.invoke('start-docker-desktop');
              // Wait 30 seconds then recheck
              setTimeout(async () => {
                const recheck = await ipcRenderer.invoke('check-docker');
                if (recheck.running) {
                  checkItem.querySelector('.check-status').textContent = 'RUNNING';
                  checkItem.classList.remove('warning');
                  checkItem.classList.add('detected', 'running');
                  startBtn.remove();
                } else {
                  startBtn.textContent = 'RETRY';
                  startBtn.disabled = false;
                }
              }, 30000);
            };
            checkItem.appendChild(startBtn);
          } else {
            checkItem.querySelector('.check-status').textContent = 'DETECTED';
          }
        }
        else if (checks[i] === 'bloodhound') {
          if (result.running) {
            checkItem.querySelector('.check-status').textContent = 'ALREADY RUNNING';
            checkItem.classList.add('running'); // Gold color
          } else if (result.installed) {
            checkItem.querySelector('.check-status').textContent = 'FOUND';
            checkItem.classList.add('running'); // Gold color
          } else {
            checkItem.querySelector('.check-status').textContent = 'DETECTED';
          }
        } 
        else {
          checkItem.querySelector('.check-status').textContent = 'DETECTED';
        }
      } else {
        checkItem.classList.add('failed');
        
        if (checks[i] === 'apikey') {
          checkItem.querySelector('.check-status').textContent = 'NOT CONFIGURED';
        } else if (checks[i] === 'docker' && result.installed === false) {
          checkItem.querySelector('.check-status').textContent = 'NOT FOUND';
          // Add download button
          const dlBtn = document.createElement('button');
          dlBtn.className = 'inline-action-btn';
          dlBtn.textContent = 'DOWNLOAD DOCKER';
          dlBtn.onclick = () => {
            ipcRenderer.invoke('install-docker');
          };
          checkItem.appendChild(dlBtn);
        } else if (checks[i] === 'python' && result.installed === false) {
          checkItem.querySelector('.check-status').textContent = 'NOT FOUND';
          // Add download button
          const dlBtn = document.createElement('button');
          dlBtn.className = 'inline-action-btn';
          dlBtn.textContent = 'DOWNLOAD PYTHON';
          dlBtn.onclick = () => {
            ipcRenderer.invoke('open-url', 'https://www.python.org/downloads/');
          };
          checkItem.appendChild(dlBtn);
        } else {
          checkItem.querySelector('.check-status').textContent = 'NOT FOUND';
        }
        
        failedChecks.push(checks[i]);
      }
    } catch (error) {
      checkItem.classList.add('failed');
      checkItem.querySelector('.check-status').textContent = 'ERROR';
      failedChecks.push(checks[i]);
    }
  }
  
  // Show errors if any critical failures
  if (failedChecks.includes('docker')) {
    showError('Docker Desktop is required to run BloodHound CE. Please install Docker Desktop and restart the installer.', 'docker');
  } else if (failedChecks.includes('python')) {
    showError('Python 3.11+ is required. Please install Python and restart the installer.', 'python');
  } else if (failedChecks.includes('apikey')) {
    showApiKeyError();
  } else {
    // Enable continue button
    document.getElementById('btn-continue').disabled = false;
  }
}

function showError(message, checkType) {
  const errorContainer = document.getElementById('error-container');
  const errorMessage = errorContainer.querySelector('.error-message');
  errorMessage.textContent = message;
  errorContainer.style.display = 'block';
  
  const btnRetry = document.getElementById('btn-retry');
  const btnSkip = document.getElementById('btn-skip');
  
  // Critical failures can't be skipped
  if (checkType === 'docker' || checkType === 'python') {
    btnSkip.style.display = 'none';
    btnRetry.textContent = 'DOWNLOAD ' + checkType.toUpperCase();
    btnRetry.onclick = async () => {
      const { ipcRenderer } = require('electron');
      if (checkType === 'docker') {
        await ipcRenderer.invoke('install-docker');
      } else if (checkType === 'python') {
        await ipcRenderer.invoke('open-url', 'https://www.python.org/downloads/');
      }
    };
  } else {
    btnSkip.style.display = 'inline-block';
    btnRetry.textContent = 'RETRY';
    btnRetry.onclick = async () => {
      errorContainer.style.display = 'none';
      await runSystemCheck();
    };
    btnSkip.onclick = () => {
      errorContainer.style.display = 'none';
      document.getElementById('btn-continue').disabled = false;
    };
  }
}

function showApiKeyError() {
  const errorContainer = document.getElementById('error-container');
  const errorMessage = errorContainer.querySelector('.error-message');
  errorMessage.innerHTML = `
    <p>Anthropic API key not configured.</p>
    <div class="api-key-input-container">
      <div class="api-key-input-wrapper">
        <input type="text" id="api-key-input" class="api-key-input" placeholder="sk-ant-api03-...">
        <span class="api-key-status-dot" id="api-key-status-dot"></span>
      </div>
      <div class="api-key-buttons">
        <button id="btn-test-key" class="btn-test-key">TEST KEY</button>
      </div>
      <div id="api-key-validation" class="api-key-validation" style="display: none;"></div>
    </div>
  `;
  errorContainer.style.display = 'block';
  
  const btnRetry = document.getElementById('btn-retry');
  const btnSkip = document.getElementById('btn-skip');
  const apiKeyInput = document.getElementById('api-key-input');
  const statusDot = document.getElementById('api-key-status-dot');
  const btnTestKey = document.getElementById('btn-test-key');
  const validationDiv = document.getElementById('api-key-validation');
  
  // Update status dot on input
  apiKeyInput.addEventListener('input', () => {
    const value = apiKeyInput.value.trim();
    statusDot.classList.remove('valid', 'invalid');
    validationDiv.style.display = 'none';
    
    if (value.startsWith('sk-ant-')) {
      statusDot.classList.add('valid');
    } else if (value.length > 0) {
      statusDot.classList.add('invalid');
    }
  });
  
  // Test key button
  btnTestKey.onclick = async () => {
    const apiKey = apiKeyInput.value.trim();
    
    if (!apiKey.startsWith('sk-ant-')) {
      validationDiv.textContent = '[ INVALID ] - Must start with sk-ant-';
      validationDiv.className = 'api-key-validation invalid';
      validationDiv.style.display = 'block';
      return;
    }
    
    btnTestKey.disabled = true;
    validationDiv.textContent = 'Testing API key...';
    validationDiv.className = 'api-key-validation testing';
    validationDiv.style.display = 'block';
    
    try {
      // Make a simple test API call
      const response = await fetch('https://api.anthropic.com/v1/messages', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': apiKey,
          'anthropic-version': '2023-06-01'
        },
        body: JSON.stringify({
          model: 'claude-3-haiku-20240307',
          max_tokens: 10,
          messages: [{ role: 'user', content: 'test' }]
        })
      });
      
      if (response.ok || response.status === 200) {
        validationDiv.textContent = '[ VALID ] - API key works!';
        validationDiv.className = 'api-key-validation valid';
        statusDot.classList.remove('invalid');
        statusDot.classList.add('valid');
      } else {
        validationDiv.textContent = '[ INVALID ] - API key rejected by Anthropic';
        validationDiv.className = 'api-key-validation invalid';
        statusDot.classList.remove('valid');
        statusDot.classList.add('invalid');
      }
    } catch (error) {
      validationDiv.textContent = '[ ERROR ] - Could not test key: ' + error.message;
      validationDiv.className = 'api-key-validation invalid';
    } finally {
      btnTestKey.disabled = false;
    }
  };
  
  btnRetry.textContent = 'SAVE KEY';
  btnSkip.style.display = 'inline-block';
  
  btnRetry.onclick = async () => {
    const { ipcRenderer } = require('electron');
    const apiKey = apiKeyInput.value.trim();
    
    if (apiKey && apiKey.startsWith('sk-ant-')) {
      try {
        // Call the IPC handler to save the API key
        const result = await ipcRenderer.invoke('save-apikey', { apiKey });
        
        if (result.success) {
          errorContainer.style.display = 'none';
          // Recheck the system to verify the API key was saved
          await runSystemCheck();
        } else {
          validationDiv.textContent = '[ ERROR ] - Failed to save: ' + (result.error || 'Unknown error');
          validationDiv.className = 'api-key-validation invalid';
          validationDiv.style.display = 'block';
        }
      } catch (error) {
        validationDiv.textContent = '[ ERROR ] - Failed to save: ' + error.message;
        validationDiv.className = 'api-key-validation invalid';
        validationDiv.style.display = 'block';
      }
    } else {
      validationDiv.textContent = '[ INVALID ] - Must start with sk-ant-';
      validationDiv.className = 'api-key-validation invalid';
      validationDiv.style.display = 'block';
    }
  };
  
  btnSkip.onclick = () => {
    errorContainer.style.display = 'none';
    document.getElementById('btn-continue').disabled = false;
  };
}

// Continue to installation
document.getElementById('btn-continue').addEventListener('click', () => {
  showScreen('screen-install');
  runInstallation();
});

// Screen 3: Installation process
let currentStep = null;
let currentStepCommand = null;
let bloodhoundPassword = null; // Store captured password from bloodhound-cli

async function runInstallation() {
  const { ipcRenderer } = require('electron');
  const terminal = document.querySelector('.status-terminal');
  const progressFill = document.querySelector('.progress-fill');
  const errorContainer = document.getElementById('install-error-container');
  
  function addTerminalLine(text, isActive = false) {
    const line = document.createElement('div');
    line.className = 'terminal-line';
    if (isActive) line.classList.add('active');
    line.textContent = text;
    terminal.appendChild(line);
    terminal.scrollTop = terminal.scrollHeight;
  }
  
  // Timeout wrapper for IPC calls
  async function invokeWithTimeout(channel, args, timeoutMs = 30000) {
    return Promise.race([
      ipcRenderer.invoke(channel, args),
      new Promise((_, reject) => 
        setTimeout(() => reject(new Error(`${channel} timed out after ${timeoutMs}ms`)), timeoutMs)
      )
    ]);
  }
  
  let currentStepIndex = 0;
  
  async function runStep(description, ipcCommand, progress, stepIndex) {
    currentStep = description;
    currentStepCommand = ipcCommand;
    currentStepIndex = stepIndex;
    addTerminalLine(description);
    
    try {
      let result;
      if (ipcCommand) {
        // Use timeout wrapper with 30 second timeout
        result = await invokeWithTimeout(ipcCommand, null, 30000);
        
        if (!result.success) {
          addTerminalLine(`ERROR: ${result.error || 'Failed'}`, true);
          
          // Handle special error cases
          if (result.needsDockerStart) {
            showDockerNotRunningError(stepIndex);
            return false;
          } else if (result.needsBloodhoundCli) {
            showBloodhoundCliNotFoundError(result.downloadUrl, stepIndex);
            return false;
          }
          
          showInstallError(result.error || 'Installation step failed', ipcCommand, stepIndex);
          return false;
        }
        if (result.output) {
          addTerminalLine(result.output.substring(0, 200)); // Show first 200 chars
        }
      } else {
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
      
      progressFill.style.width = progress + '%';
      return true;
    } catch (error) {
      addTerminalLine(`ERROR: ${error.message}`, true);
      showInstallError(error.message, ipcCommand, stepIndex);
      return false;
    }
  }
  
  function showDockerNotRunningError() {
    const errorMessage = errorContainer.querySelector('.error-message');
    errorMessage.textContent = 'Docker installed but not running. Start Docker Desktop.';
    errorContainer.style.display = 'block';
    
    const btnRetry = document.getElementById('btn-install-retry');
    const btnSkip = document.getElementById('btn-install-skip');
    
    btnRetry.textContent = 'OPEN DOCKER DESKTOP';
    btnSkip.style.display = 'inline-block';
    
    btnRetry.onclick = async () => {
      await ipcRenderer.invoke('start-docker-desktop');
      errorContainer.style.display = 'none';
      addTerminalLine('Please wait for Docker to start, then retry...');
    };
    
    btnSkip.onclick = () => {
      errorContainer.style.display = 'none';
      addTerminalLine('Step skipped by user.');
    };
  }
  
  function showBloodhoundCliNotFoundError(downloadUrl) {
    const errorMessage = errorContainer.querySelector('.error-message');
    errorMessage.textContent = 'bloodhound-cli not found. Download BloodHound CE first.';
    errorContainer.style.display = 'block';
    
    const btnRetry = document.getElementById('btn-install-retry');
    const btnSkip = document.getElementById('btn-install-skip');
    
    btnRetry.textContent = 'DOWNLOAD BLOODHOUND CE';
    btnSkip.style.display = 'inline-block';
    
    btnRetry.onclick = async () => {
      await ipcRenderer.invoke('open-url', downloadUrl);
      addTerminalLine('Please install BloodHound CE, then retry...');
    };
    
    btnSkip.onclick = () => {
      errorContainer.style.display = 'none';
      addTerminalLine('Step skipped by user.');
    };
  }
  
  function showInstallError(message, stepCommand, stepIndex) {
    const errorMessage = errorContainer.querySelector('.error-message');
    errorMessage.textContent = message;
    errorContainer.style.display = 'block';
    
    const btnRetry = document.getElementById('btn-install-retry');
    const btnSkip = document.getElementById('btn-install-skip');
    
    btnRetry.onclick = async () => {
      console.log('[retry] retrying step', stepIndex);
      errorContainer.style.display = 'none';
      // Retry just this step - need to continue from here
      continueFromStep(stepIndex);
    };
    
    btnSkip.onclick = () => {
      console.log('[skip] skipping step', stepIndex);
      errorContainer.style.display = 'none';
      addTerminalLine('⚠ Step skipped by user');
      // Skip to next step
      continueFromStep(stepIndex + 1);
    };
  }
  
  function showDockerNotRunningError(stepIndex) {
    const errorMessage = errorContainer.querySelector('.error-message');
    errorMessage.textContent = 'Docker installed but not running. Start Docker Desktop.';
    errorContainer.style.display = 'block';
    
    const btnRetry = document.getElementById('btn-install-retry');
    const btnSkip = document.getElementById('btn-install-skip');
    
    btnRetry.textContent = 'OPEN DOCKER DESKTOP';
    btnSkip.style.display = 'inline-block';
    
    btnRetry.onclick = async () => {
      await ipcRenderer.invoke('start-docker-desktop');
      errorContainer.style.display = 'none';
      addTerminalLine('Please wait for Docker to start, then retry...');
    };
    
    btnSkip.onclick = () => {
      console.log('[skip] skipping docker step');
      errorContainer.style.display = 'none';
      addTerminalLine('⚠ Docker step skipped by user');
      continueFromStep(stepIndex + 1);
    };
  }
  
  function showBloodhoundCliNotFoundError(downloadUrl, stepIndex) {
    const errorMessage = errorContainer.querySelector('.error-message');
    errorMessage.textContent = 'bloodhound-cli not found. Download BloodHound CE first.';
    errorContainer.style.display = 'block';
    
    const btnRetry = document.getElementById('btn-install-retry');
    const btnSkip = document.getElementById('btn-install-skip');
    
    btnRetry.textContent = 'DOWNLOAD BLOODHOUND CE';
    btnSkip.style.display = 'inline-block';
    
    btnRetry.onclick = async () => {
      await ipcRenderer.invoke('open-url', downloadUrl);
      addTerminalLine('Please install BloodHound CE, then retry...');
    };
    
    btnSkip.onclick = () => {
      console.log('[skip] skipping bloodhound step');
      errorContainer.style.display = 'none';
      addTerminalLine('⚠ BloodHound step skipped by user');
      continueFromStep(stepIndex + 1);
    };
  }
  
  // Clear initial line
  terminal.innerHTML = '';
  
  // Run installation steps
  const progressText = document.querySelector('.progress-text');
  
  const deploySteps = [
    { description: 'Initializing installation environment...', command: null, progress: 10 },
    { description: 'Starting BloodHound CE containers...', command: 'start-bloodhound', progress: 25, checkSkip: async () => {
      const bhCheck = await ipcRenderer.invoke('check-bloodhound');
      if (bhCheck && bhCheck.running) {
        addTerminalLine('BloodHound CE already running, skipping startup...');
        return true;
      }
      return false;
    }},
    { description: 'Installing AutoHound Python package...', command: 'install-autohound', progress: 45 },
    { description: 'Verifying AutoHound CLI...', command: 'verify-autohound', progress: 65 },
    { description: 'Saving API configuration...', command: 'save-apikey', progress: 80 },
    { description: 'Creating desktop shortcuts...', command: 'create-shortcut', progress: 95 },
    { description: 'Finalizing installation...', command: null, progress: 100 }
  ];
  
  let autohoundInstallPath = null;
  
  async function continueFromStep(stepIndex) {
    console.log('[continueFromStep] starting from step', stepIndex);
    
    if (stepIndex >= deploySteps.length) {
      console.log('All steps complete!');
      await new Promise(resolve => setTimeout(resolve, 500));
      addTerminalLine('AutoHound deployed._', true);
      setTimeout(() => {
        showScreen('screen-complete');
        displayAutohoundPath();
      }, 2000);
      return;
    }
    
    for (let i = stepIndex; i < deploySteps.length; i++) {
      const step = deploySteps[i];
      
      // Check if this step should be skipped
      if (step.checkSkip && await step.checkSkip()) {
        progressFill.style.width = step.progress + '%';
        if (progressText) progressText.textContent = step.progress + '%';
        continue;
      }
      
      const success = await runStep(step.description, step.command, step.progress, i);
      if (progressText) progressText.textContent = step.progress + '%';
      
      if (!success) {
        console.log(`Step ${i} failed - waiting for user action`);
        return;
      }
    }
    
    console.log('All steps complete!');
    await new Promise(resolve => setTimeout(resolve, 500));
    addTerminalLine('AutoHound deployed._', true);
    setTimeout(() => {
      showScreen('screen-complete');
      displayAutohoundPath();
    }, 2000);
  }
  
  async function displayAutohoundPath() {
    const pathElement = document.getElementById('autohound-path');
    if (!pathElement) return;
    
    // Query the verify handler to get the path
    try {
      const result = await ipcRenderer.invoke('verify-autohound');
      if (result && result.success) {
        if (result.path) {
          pathElement.textContent = result.path;
        } else if (result.version) {
          pathElement.textContent = `py -m autohound (${result.version})`;
        } else {
          pathElement.textContent = 'Installed successfully';
        }
      } else {
        pathElement.textContent = 'Not detected (may need PATH refresh)';
      }
    } catch (e) {
      pathElement.textContent = 'Detection failed';
    }
  }
  
  // Start installation from step 0
  continueFromStep(0);
}

// Window controls
document.getElementById('btn-minimize')?.addEventListener('click', async () => {
  const { ipcRenderer } = require('electron');
  await ipcRenderer.invoke('minimize-window');
});

document.getElementById('btn-close')?.addEventListener('click', async () => {
  const { ipcRenderer } = require('electron');
  await ipcRenderer.invoke('close-window');
});

// Complete screen buttons
document.getElementById('btn-launch')?.addEventListener('click', async () => {
  const { ipcRenderer } = require('electron');
  await ipcRenderer.invoke('open-url', 'http://localhost:8080');
});

document.getElementById('btn-docs')?.addEventListener('click', async () => {
  const { ipcRenderer } = require('electron');
  await ipcRenderer.invoke('open-url', 'https://github.com/geo2x/AutoHound');
});

document.getElementById('btn-finish')?.addEventListener('click', async () => {
  const { ipcRenderer } = require('electron');
  await ipcRenderer.invoke('close-window');
});

// Initialize on load
window.addEventListener('DOMContentLoaded', () => {
  initParticles();
  
  // Setup window controls after DOM loaded
  const btnMinimize = document.getElementById('btn-minimize');
  const btnClose = document.getElementById('btn-close');
  
  if (btnMinimize) {
    btnMinimize.addEventListener('click', async () => {
      const { ipcRenderer } = require('electron');
      await ipcRenderer.invoke('minimize-window');
    });
  }
  
  if (btnClose) {
    btnClose.addEventListener('click', async () => {
      const { ipcRenderer } = require('electron');
      await ipcRenderer.invoke('close-window');
    });
  }
  
  // Listen for bloodhound password from main process
  const { ipcRenderer } = require('electron');
  ipcRenderer.on('bloodhound-password', (event, password) => {
    console.log('[renderer] received bloodhound password:', password);
    bloodhoundPassword = password;
    
    // Update the password field on complete screen if it exists
    const passwordElement = document.getElementById('bloodhound-password');
    if (passwordElement) {
      passwordElement.textContent = password;
      passwordElement.style.fontSize = '13px';
      passwordElement.style.fontWeight = 'bold';
    }
  });
  
  // Listen for bloodhound output to display in complete screen terminal
  ipcRenderer.on('bloodhound-output', (event, line) => {
    const completeTerminal = document.getElementById('complete-terminal');
    if (completeTerminal) {
      const termLine = document.createElement('div');
      termLine.className = 'terminal-line';
      termLine.textContent = line;
      completeTerminal.appendChild(termLine);
      completeTerminal.scrollTop = completeTerminal.scrollHeight;
    }
  });
});
