# MULTI-CHECKER BOT — DEPLOY GUIDE
## MADE BY @NUTFRR

---

## CHECKERS INCLUDED

| Checker | What it captures |
|---------|-----------------|
| 🎮 Xbox Full | Gamertag, Gamerscore, Game Pass Ultimate/PC, Gold, expiry, country, account age |
| 🎯 Fortnite | V-Bucks, skin count, rare skins, emotes, pickaxes, Battle Pass level |
| ⛏️ Minecraft | Java/Bedrock ownership, username, UUID, cape |
| 🎫 Game Pass | All subscription tiers, all expiry dates, EA Play detection |
| 🕹️ EA | EA Play / EA Pro, game library count, country |

---

## RENDER DEPLOY (5 min)

### 1. Push to GitHub
```bash
git init
git add .
git commit -m "multi checker bot"
git remote add origin https://github.com/YOUR/REPO.git
git push -u origin main
```

### 2. Create Render Web Service
- https://render.com → New → Web Service → Connect GitHub repo
- Render auto-detects `render.yaml`

### 3. Set Environment Variables
| Key | Value |
|-----|-------|
| `BOT_TOKEN` | From @BotFather |
| `ADMIN_ID` | Your Telegram ID (get from @userinfobot) |
| `WEBHOOK_URL` | `https://YOUR-APP-NAME.onrender.com` |

### 4. Done
Bot sets webhook automatically on startup.

---

## LOCAL DEV (polling mode)
```bash
pip install -r requirements.txt
export BOT_TOKEN=your_token
export ADMIN_ID=your_id
export DB_PATH=./dev.db
python main.py
```

---

## BOT COMMANDS

| Command | Description |
|---------|-------------|
| `/start` | Main menu |
| `/status` | Your account info |
| `/redeem CODE` | Redeem premium code |
| `/help` | Help & commands |

### Admin Commands
| Command | Description |
|---------|-------------|
| `/gencode USES DAYS` | Generate code (e.g. `/gencode 1 30`) |
| `/revoke CODE` | Revoke a code |
| `/addpremium USER_ID DAYS` | Directly add premium |
| `/ban USER_ID` | Ban a user |
| `/unban USER_ID` | Unban a user |
| `/broadcast MESSAGE` | Send to all users |

---

## HOW CHECKING WORKS

1. User taps **Checkers** → picks a checker
2. Selects thread speed (Fast/Turbo/Safe)
3. Sends `.txt` file or pastes `email:password` combos
4. Bot shows live progress every 5 seconds
5. Each hit card sent instantly to chat
6. `.txt` hits file auto-sent when done

---

## FILE STRUCTURE

```
multichkr/
├── main.py               — entry point
├── requirements.txt
├── Dockerfile
├── render.yaml
├── bot/
│   ├── handlers.py       — all TG handlers + checker task runner
│   ├── keyboards.py      — inline keyboards
│   └── messages.py       — message templates + hit cards
├── checkers/
│   ├── utils.py          — combo parser, shared constants
│   ├── xbox_checker.py   — Xbox Full Capture
│   ├── fortnite_checker.py — Fortnite API
│   ├── minecraft_checker.py — Minecraft Xbox + MC API
│   ├── gamepass_checker.py  — Game Pass all tiers
│   └── ea_checker.py     — EA Xbox + EA API
└── db/
    └── database.py       — SQLite database layer
```

---

**Credits: @NUTFRR**
