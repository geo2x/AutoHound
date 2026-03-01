/**
 * AutoHound — Attack Path Intelligence Engine
 * Copyright (c) 2026 Gordon Prescott. All rights reserved.
 * ACH Research Division
 */

// Particle system for background
function initParticles() {
  const canvas = document.getElementById('particles');
  const ctx = canvas.getContext('2d');
  
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
  
  const particles = [];
  const particleCount = 50;
  
  class Particle {
    constructor() {
      this.x = Math.random() * canvas.width;
      this.y = canvas.height + Math.random() * 100;
      this.size = Math.random() * 2 + 1;
      this.speedY = Math.random() * 0.5 + 0.3;
      this.opacity = Math.random() * 0.3;
    }
    
    update() {
      this.y -= this.speedY;
      if (this.y < -10) {
        this.y = canvas.height + 10;
        this.x = Math.random() * canvas.width;
      }
    }
    
    draw() {
      ctx.fillStyle = `rgba(139, 0, 0, ${this.opacity})`;
      ctx.beginPath();
      ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
      ctx.fill();
    }
  }
  
  for (let i = 0; i < particleCount; i++) {
    particles.push(new Particle());
  }
  
  function animate() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    particles.forEach(particle => {
      particle.update();
      particle.draw();
    });
    requestAnimationFrame(animate);
  }
  
  animate();
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
async function runSystemCheck() {
  const checks = ['docker', 'python', 'powershell', 'apikey', 'disk'];
  
  for (let i = 0; i < checks.length; i++) {
    await new Promise(resolve => setTimeout(resolve, 400));
    
    const checkItem = document.querySelector(`[data-check="${checks[i]}"]`);
    checkItem.classList.remove('pending');
    
    // Simulated results - will wire up real checks later
    const results = {
      docker: false,
      python: true,
      powershell: true,
      apikey: false,
      disk: true
    };
    
    if (results[checks[i]]) {
      checkItem.classList.add('detected');
      checkItem.querySelector('.check-status').textContent = 
        checks[i] === 'disk' ? '14.2 GB FREE' : 'DETECTED';
    } else {
      checkItem.classList.add('failed');
      checkItem.querySelector('.check-status').textContent = 
        checks[i] === 'apikey' ? 'NOT CONFIGURED' : 'NOT FOUND';
    }
  }
  
  // Enable continue button
  document.getElementById('btn-continue').disabled = false;
}

// Continue to installation
document.getElementById('btn-continue').addEventListener('click', () => {
  showScreen('screen-install');
  runInstallation();
});

// Screen 3: Installation process
async function runInstallation() {
  const terminal = document.querySelector('.status-terminal');
  const progressFill = document.querySelector('.progress-fill');
  
  const steps = [
    'Initializing installation environment...',
    'Pulling AutoHound containers...',
    'Configuring Neo4j graph database...',
    'Installing Python dependencies...',
    'Registering ACH Research Division software...',
    'Creating system shortcuts...',
    'Verifying component integrity...',
    'AutoHound deployed._'
  ];
  
  for (let i = 0; i < steps.length; i++) {
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    const line = document.createElement('div');
    line.className = 'terminal-line';
    if (i === steps.length - 1) {
      line.classList.add('active');
    }
    line.textContent = steps[i];
    terminal.appendChild(line);
    
    // Update progress
    const progress = ((i + 1) / steps.length) * 100;
    progressFill.style.width = progress + '%';
    
    // Scroll terminal
    terminal.scrollTop = terminal.scrollHeight;
  }
  
  // Move to complete screen
  setTimeout(() => {
    showScreen('screen-complete');
  }, 2000);
}

// Initialize on load
window.addEventListener('DOMContentLoaded', () => {
  initParticles();
});
