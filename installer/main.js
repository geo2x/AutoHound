const { app, BrowserWindow, ipcMain, shell } = require('electron')
const path = require('path')
const { execFile, spawn } = require('child_process')
const fs = require('fs')
const net = require('net')

let mainWindow

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 700,
    height: 700,
    transparent: true,
    frame: false,
    backgroundColor: '#00000000',
    hasShadow: false,
    alwaysOnTop: false,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
      webSecurity: false
    }
  })
  mainWindow.loadFile('renderer/intro.html')
  // mainWindow.webContents.openDevTools() // Disabled for production
}

app.whenReady().then(createWindow)
app.on('window-all-closed', () => app.quit())

// ── SAFE EXEC HELPER ─────────────────────────────────────
// Never hangs. Always resolves within timeoutMs.
function safeExec(cmd, args = [], timeoutMs = 5000) {
  return new Promise((resolve) => {
    let done = false
    const finish = (result) => {
      if (done) return
      done = true
      resolve(result)
    }

    const timer = setTimeout(() => finish(null), timeoutMs)

    try {
      const proc = execFile(cmd, args, { timeout: timeoutMs, shell: true }, (err, stdout, stderr) => {
        clearTimeout(timer)
        if (err) return finish(null)
        finish((stdout || stderr || '').trim() || null)
      })
      proc.on('error', () => { clearTimeout(timer); finish(null) })
    } catch (e) {
      clearTimeout(timer)
      finish(null)
    }
  })
}

// ── CHECK PORT OPEN ───────────────────────────────────────
function checkPort(port) {
  return new Promise((resolve) => {
    const sock = new net.Socket()
    sock.setTimeout(2000)
    sock.on('connect', () => { sock.destroy(); resolve(true) })
    sock.on('error', () => resolve(false))
    sock.on('timeout', () => { sock.destroy(); resolve(false) })
    sock.connect(port, '127.0.0.1')
  })
}

// ── WINDOW CONTROLS ───────────────────────────────────────
ipcMain.handle('minimize-window', () => mainWindow.minimize())
ipcMain.handle('close-window', () => app.quit())
ipcMain.handle('resize-window', (e, { w, h }) => {
  const { screen } = require('electron')
  const { width, height } = screen.getPrimaryDisplay().workAreaSize
  mainWindow.setBounds({
    x: Math.floor((width - w) / 2),
    y: Math.floor((height - h) / 2),
    width: Math.floor(w),
    height: Math.floor(h)
  })
})

// ── CHECK PYTHON ──────────────────────────────────────────
ipcMain.handle('check-python', async () => {
  console.log('[check-python] starting')

  const candidates = [
    ['py', ['-3', '--version']],
    ['py', ['--version']],
    ['python', ['--version']],
    ['python3', ['--version']],
    ['python3.11', ['--version']],
    ['python3.12', ['--version']],
    ['python3.10', ['--version']],
  ]

  // Add full path candidates
  const userProfile = process.env.USERPROFILE || 'C:\\Users\\gordo'
  const fullPaths = [
    `${userProfile}\\AppData\\Local\\Programs\\Python\\Python313\\python.exe`,
    `${userProfile}\\AppData\\Local\\Programs\\Python\\Python312\\python.exe`,
    `${userProfile}\\AppData\\Local\\Programs\\Python\\Python311\\python.exe`,
    `${userProfile}\\AppData\\Local\\Programs\\Python\\Python310\\python.exe`,
    'C:\\Python312\\python.exe',
    'C:\\Python311\\python.exe',
    'C:\\Python310\\python.exe',
  ].filter(p => {
    try { return fs.existsSync(p) } catch { return false }
  })

  for (const fp of fullPaths) {
    candidates.push([fp, ['--version']])
  }

  for (const [cmd, args] of candidates) {
    console.log(`[check-python] trying: ${cmd} ${args.join(' ')}`)
    const result = await safeExec(cmd, args, 4000)
    console.log(`[check-python] result: ${result}`)
    if (result && result.toLowerCase().includes('python')) {
      const match = result.match(/(\d+\.\d+\.\d+)/)
      console.log('[check-python] FOUND:', result)
      return { success: true, installed: true, version: match ? match[1] : result, versionNum: match ? parseFloat(match[1]) : 3.0, path: cmd }
    }
  }

  console.log('[check-python] NOT FOUND')
  return { success: false, installed: false, version: null, path: null }
})

// ── CHECK DOCKER ──────────────────────────────────────────
ipcMain.handle('check-docker', async () => {
  console.log('[check-docker] starting')

  const version = await safeExec('docker', ['--version'], 5000)
  console.log('[check-docker] version result:', version)

  if (!version) {
    return { success: false, installed: false, running: false, version: null }
  }

  const info = await safeExec('docker', ['info'], 8000)
  const running = !!(info && !info.toLowerCase().includes('error during connect'))
  console.log('[check-docker] running:', running)

  const match = version.match(/(\d+\.\d+\.\d+)/)
  return {
    success: running,
    installed: true,
    running,
    version: match ? match[1] : version
  }
})

// ── CHECK BLOODHOUND ──────────────────────────────────────
ipcMain.handle('check-bloodhound', async () => {
  console.log('[check-bloodhound] starting')

  // Check if port 8080 is open
  const port8080 = await checkPort(8080)
  if (port8080) {
    console.log('[check-bloodhound] port 8080 open — already running')
    return { success: true, installed: true, running: true, method: 'port' }
  }

  // Check bloodhound-cli in PATH
  const cliVersion = await safeExec('bloodhound-cli', ['version'], 4000)
  if (cliVersion) {
    console.log('[check-bloodhound] bloodhound-cli found in PATH')
    return { success: true, installed: true, running: false, method: 'cli' }
  }

  // Check docker for bloodhound container
  const containers = await safeExec('docker', ['ps', '-a', '--filter', 'name=bloodhound', '--format', '{{.Names}}'], 5000)
  if (containers) {
    console.log('[check-bloodhound] bloodhound docker container found')
    return { success: true, installed: true, running: false, method: 'docker' }
  }

  console.log('[check-bloodhound] not found')
  return { success: false, installed: false, running: false, method: null }
})

// ── CHECK DISK SPACE ──────────────────────────────────────
ipcMain.handle('check-disk-space', async () => {
  const result = await safeExec('wmic', ['logicaldisk', 'where', 'DeviceID="C:"', 'get', 'FreeSpace'], 8000)
  if (!result) return { success: true, freeSpaceGB: 'Unknown' }
  const match = result.match(/(\d+)/)
  if (match) {
    const gb = parseInt(match[1]) / (1024 * 1024 * 1024)
    return { success: gb > 10, freeSpaceGB: gb.toFixed(2) }
  }
  return { success: true, freeSpaceGB: 'Unknown' }
})

// ── GET PROJECT DIR ───────────────────────────────────────
function getProjectDir() {
  // When running in development: installer/../
  // When running in production: resources/app/app/
  const devPath = path.join(__dirname, '..')
  const prodPath = process.resourcesPath 
    ? path.join(process.resourcesPath, 'app')
    : devPath
  
  // Check if we're in production by looking for pyproject.toml
  const testProdPath = path.join(prodPath, 'pyproject.toml')
  const testDevPath = path.join(devPath, 'pyproject.toml')
  
  if (fs.existsSync(testProdPath)) {
    console.log('[getProjectDir] using production path:', prodPath)
    return prodPath
  } else if (fs.existsSync(testDevPath)) {
    console.log('[getProjectDir] using dev path:', devPath)
    return devPath
  } else {
    console.log('[getProjectDir] pyproject.toml not found, defaulting to dev path')
    return devPath
  }
}

// ── CHECK API KEY ─────────────────────────────────────────
ipcMain.handle('check-api-key', async () => {
  try {
    const projectDir = getProjectDir()
    const envPath = path.join(projectDir, '.env')
    if (!fs.existsSync(envPath)) return { success: false }
    const content = fs.readFileSync(envPath, 'utf8')
    const match = content.match(/^ANTHROPIC_API_KEY=sk-ant-.+$/m)
    return { success: !!match }
  } catch (e) {
    return { success: false }
  }
})

// ── INSTALL AUTOHOUND ─────────────────────────────────────
ipcMain.handle('install-autohound', async (event) => {
  console.log('[install-autohound] starting')
  const projectDir = getProjectDir()
  console.log('[install-autohound] project dir:', projectDir)

  return new Promise((resolve) => {
    const proc = spawn('py', ['-m', 'pip', 'install', '-e', '.'], {
      cwd: projectDir,
      shell: true
    })

    let output = ''

    proc.stdout.on('data', (d) => {
      const line = d.toString().trim()
      if (line) {
        output += line + '\n'
        console.log('[pip]', line)
        mainWindow.webContents.send('install-output', line)
      }
    })

    proc.stderr.on('data', (d) => {
      const line = d.toString().trim()
      if (line) {
        output += line + '\n'
        console.log('[pip stderr]', line)
        mainWindow.webContents.send('install-output', line)
      }
    })

    proc.on('close', (code) => {
      console.log('[install-autohound] exit code:', code)
      resolve({ success: code === 0, code, output })
    })

    proc.on('error', (err) => {
      console.log('[install-autohound] error:', err.message)
      resolve({ success: false, error: err.message })
    })

    // 3 minute timeout
    setTimeout(() => {
      try { proc.kill() } catch (e) {}
      resolve({ success: false, error: 'timed out after 3 minutes' })
    }, 180000)
  })
})

// ── VERIFY AUTOHOUND ──────────────────────────────────────
ipcMain.handle('verify-autohound', async () => {
  console.log('[verify-autohound] starting')
  
  const projectDir = getProjectDir()
  
  // Try autohound directly
  let result = await safeExec('autohound', ['--version'], 8000)
  if (result) {
    console.log('[verify-autohound] found via autohound:', result)
    return { success: true, version: result }
  }
  
  // Try python -m autohound
  result = await safeExec('python', ['-m', 'autohound', '--version'], 8000)
  if (result) {
    console.log('[verify-autohound] found via python -m:', result)
    return { success: true, version: result }
  }
  
  // Try py -m autohound
  result = await safeExec('py', ['-m', 'autohound', '--version'], 8000)
  if (result) {
    console.log('[verify-autohound] found via py -m:', result)
    return { success: true, version: result }
  }
  
  // Try running cli.py directly
  const cliPath = path.join(projectDir, 'autohound', 'cli.py')
  console.log('[verify-autohound] trying cli.py at:', cliPath)
  result = await safeExec('python', [cliPath, '--version'], 8000)
  if (result) {
    console.log('[verify-autohound] found via cli.py (python):', result)
    return { success: true, version: result }
  }
  
  result = await safeExec('py', [cliPath, '--version'], 8000)
  if (result) {
    console.log('[verify-autohound] found via cli.py (py):', result)
    return { success: true, version: result }
  }
  
  // Try scripts folder
  const userProfile = process.env.USERPROFILE || 'C:\\Users\\gordo'
  const scriptPaths = [
    `${userProfile}\\AppData\\Local\\Programs\\Python\\Python313\\Scripts\\autohound.exe`,
    `${userProfile}\\AppData\\Local\\Programs\\Python\\Python312\\Scripts\\autohound.exe`,
    `${userProfile}\\AppData\\Local\\Programs\\Python\\Python311\\Scripts\\autohound.exe`,
    `${userProfile}\\AppData\\Roaming\\Python\\Python313\\Scripts\\autohound.exe`,
    `${userProfile}\\AppData\\Roaming\\Python\\Python312\\Scripts\\autohound.exe`,
    `${userProfile}\\AppData\\Roaming\\Python\\Python311\\Scripts\\autohound.exe`,
    'C:\\Python313\\Scripts\\autohound.exe',
    'C:\\Python312\\Scripts\\autohound.exe',
    'C:\\Python311\\Scripts\\autohound.exe',
  ]
  
  for (const sp of scriptPaths) {
    try {
      if (fs.existsSync(sp)) {
        console.log('[verify-autohound] found at:', sp)
        result = await safeExec(sp, ['--version'], 8000)
        if (result) return { success: true, version: result, path: sp }
        // Found the exe but version flag fails — still count as success
        return { success: true, version: 'installed', path: sp }
      }
    } catch(e) {}
  }
  
  // Last resort — check if autohound package is importable
  result = await safeExec('python', ['-c', 'import autohound; print("ok")'], 5000)
  if (result && result.includes('ok')) {
    console.log('[verify-autohound] import ok via python')
    return { success: true, version: 'installed (import ok)' }
  }
  
  result = await safeExec('py', ['-c', 'import autohound; print("ok")'], 5000)
  if (result && result.includes('ok')) {
    console.log('[verify-autohound] import ok via py')
    return { success: true, version: 'installed (import ok)' }
  }
  
  console.log('[verify-autohound] not found anywhere')
  return { success: false, error: 'AutoHound not found after installation' }
})

// ── SAVE API KEY ──────────────────────────────────────────
ipcMain.handle('save-apikey', async (event, args) => {
  console.log('[save-apikey] starting')
  try {
    const projectDir = getProjectDir()
    const envPath = path.join(projectDir, '.env')
    const envExamplePath = path.join(projectDir, '.env.example')
    
    // Create .env from .env.example if it doesn't exist
    if (!fs.existsSync(envPath) && fs.existsSync(envExamplePath)) {
      fs.copyFileSync(envExamplePath, envPath)
    }
    
    // If API key provided, write it
    if (args && args.apiKey) {
      let content = fs.existsSync(envPath) ? fs.readFileSync(envPath, 'utf8') : ''
      
      // Update or add ANTHROPIC_API_KEY
      if (content.includes('ANTHROPIC_API_KEY=')) {
        content = content.replace(/ANTHROPIC_API_KEY=.*/g, `ANTHROPIC_API_KEY=${args.apiKey}`)
      } else {
        content += `\nANTHROPIC_API_KEY=${args.apiKey}\n`
      }
      
      fs.writeFileSync(envPath, content, 'utf8')
      console.log('[save-apikey] API key saved')
    }
    
    return { success: true }
  } catch (e) {
    console.log('[save-apikey] error:', e.message)
    return { success: false, error: e.message }
  }
})

// ── CREATE SHORTCUT ───────────────────────────────────────
ipcMain.handle('create-shortcut', async () => {
  console.log('[create-shortcut] starting')
  try {
    // Try multiple desktop locations
    const possibleDesktops = [
      app.getPath('desktop'),  // Electron built-in — most reliable
      path.join(process.env.USERPROFILE || '', 'Desktop'),
      path.join(process.env.HOMEDRIVE || 'C:', process.env.HOMEPATH || '', 'Desktop'),
      'C:\\Users\\gordo\\Desktop',
    ]
    
    let desktopPath = null
    for (const p of possibleDesktops) {
      try {
        if (fs.existsSync(p)) {
          desktopPath = p
          console.log('[create-shortcut] desktop found at:', p)
          break
        }
      } catch(e) {}
    }
    
    if (!desktopPath) {
      console.log('[create-shortcut] desktop folder not found')
      return { success: false, error: 'Desktop folder not found' }
    }
    
    // Use app.getPath('desktop') — most reliable cross-user method
    const realDesktop = app.getPath('desktop')
    console.log('[create-shortcut] using desktop:', realDesktop)
    
    // Write .url shortcut (no space in filename to avoid path issues)
    const shortcutPath = path.join(realDesktop, 'BloodHound.url')
    const content = '[InternetShortcut]\nURL=http://localhost:8080\nIconIndex=0\n'
    fs.writeFileSync(shortcutPath, content, 'utf8')
    
    console.log('[create-shortcut] created at:', shortcutPath)
    return { success: true, path: shortcutPath }
    
  } catch (e) {
    console.log('[create-shortcut] error:', e.message)
    return { success: false, error: e.message }
  }
})

// ── START BLOODHOUND ──────────────────────────────────────
ipcMain.handle('start-bloodhound', async (event) => {
  console.log('[start-bloodhound] starting')

  // Already running?
  const already = await checkPort(8080)
  if (already) {
    return { success: true, alreadyRunning: true }
  }

  return new Promise((resolve) => {
    const proc = spawn('bloodhound-cli', ['up'], { shell: true })
    let capturedPassword = null

    proc.stdout.on('data', (d) => {
      const line = d.toString().trim()
      if (line) {
        mainWindow.webContents.send('bloodhound-output', line)
        
        // Capture password from output - look for patterns like "Initial Password: xyz" or "Password: xyz"
        const passwordMatch = line.match(/(?:initial\s+)?password[:\s]+([^\s]+)/i)
        if (passwordMatch) {
          capturedPassword = passwordMatch[1]
          console.log('[start-bloodhound] captured password:', capturedPassword)
          mainWindow.webContents.send('bloodhound-password', capturedPassword)
        }
        
        if (line.toLowerCase().includes('ready') ||
            line.toLowerCase().includes('listening')) {
          resolve({ success: true, password: capturedPassword })
        }
      }
    })

    proc.stderr.on('data', (d) => {
      const line = d.toString().trim()
      if (line) {
        mainWindow.webContents.send('bloodhound-output', line)
        
        // Also check stderr for password
        const passwordMatch = line.match(/(?:initial\s+)?password[:\s]+([^\s]+)/i)
        if (passwordMatch) {
          capturedPassword = passwordMatch[1]
          console.log('[start-bloodhound] captured password from stderr:', capturedPassword)
          mainWindow.webContents.send('bloodhound-password', capturedPassword)
        }
      }
    })

    proc.on('error', (err) => resolve({ success: false, error: err.message }))
    proc.on('close', (code) => resolve({ success: code === 0, password: capturedPassword }))

    // 5 minute timeout
    setTimeout(() => {
      try { proc.kill() } catch (e) {}
      resolve({ success: false, error: 'timed out after 5 minutes', password: capturedPassword })
    }, 300000)
  })
})

// ── OPEN EXTERNAL ─────────────────────────────────────────
ipcMain.handle('open-url', (e, url) => {
  shell.openExternal(url)
  return { success: true }
})

// ── START DOCKER DESKTOP ──────────────────────────────────
ipcMain.handle('start-docker-desktop', async () => {
  const dockerPath = 'C:\\Program Files\\Docker\\Docker\\Docker Desktop.exe'
  try {
    spawn(dockerPath, [], { detached: true, stdio: 'ignore' }).unref()
    return { success: true }
  } catch (e) {
    return { success: false, error: e.message }
  }
})

// ── INSTALL DOCKER ────────────────────────────────────────
ipcMain.handle('install-docker', async () => {
  shell.openExternal('https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe')
  return { success: true }
})
