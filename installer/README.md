# AutoHound Installer

**ACH Research Division**  
Copyright (c) 2026 Gordon Prescott. All rights reserved.

## Building the Installer

### Prerequisites
- Node.js 18+ and npm
- Windows OS (for .exe build)

### Setup
```powershell
cd installer
npm install
```

### Development
```powershell
npm start
```

### Build Production Installer
```powershell
npm run build
```

This will create `AutoHound_Setup.exe` in the `dist/` directory.

## Phase 1 Status (Current)
✅ Full UI/UX with all 4 screens  
✅ Berserk/ACH dark fantasy theme  
✅ Eclipse background with particle system  
✅ Animated progress indicators  
✅ Custom typography (Cinzel + JetBrains Mono)  
✅ Gold borders, crimson accents  

## Phase 2 TODO (Next Session)
⏳ Wire up actual system checks (Docker, Python, PowerShell)  
⏳ Execute real installation commands  
⏳ Create autohound.ico  
⏳ Download and embed fonts locally  
⏳ Test build process  

## Font Requirements
Download these fonts and place in `assets/fonts/`:
- Cinzel-Bold.ttf (from Google Fonts)
- JetBrainsMono-Regular.ttf (from JetBrains)

## Icon Requirements
Create `assets/autohound.ico` with ACH branding (blood red, dark theme).

---

**AutoHound** — Original work by Gordon Prescott  
**ACH Research Division** — 2026
