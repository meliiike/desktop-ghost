# 👻 Desktop Ghost — Your Companion on the Desktop

A cute, animated desktop pet built with **Python + PyQt6** that lives on top of your
screen, walks around, and doubles as a lightweight productivity assistant. Drag it,
drop files on it, ask it questions with AI, set reminders, keep daily tasks, and open
your favorite links — all from a little floating ghost.

---

## ✨ Features

### The ghost itself
- **Lives on your desktop** as a frameless, always-on-top, transparent window.
- **Animated states**: idle, walk, jump, and sleep, driven by sprite frames.
- **Autonomous behavior**: wanders, turns, does small jumps, and occasionally speaks.
- **Draggable**: grab it and move it anywhere; double-click to make it jump.
- **Speech bubbles** with random friendly messages.
- **3 characters** (`ghost1`, `ghost2`, `ghost3`), each with its own color theme.
- **Resizable** (Small / Medium / Large / Extra Large / Custom).
- **Sleep / wake** toggle and a "go to ground" command.

### Productivity tools (right-click menu)
- **✨ Ask AI** — chat with Google **Gemini 2.5 Flash**. You can **attach a file**
  (`.txt`, `.pdf`, `.docx`, `.pptx`) and ask questions about its contents.
- **⏰ Reminders** — schedule reminders either *after a duration* or *at a clock time*.
- **📋 Daily Tasks** — a simple to-do list with add / complete / next-task nudges.
- **📁 File Basket** — drop files onto the ghost to "hold" them, drag them back out,
  and **convert between formats**.
- **🔗 Quick Links** — save and open your favorite websites in the browser.

### File conversion (in the File Basket)
Supports converting between:

| From \ To | PDF | DOCX | PPTX | TXT |
|-----------|:---:|:----:|:----:|:---:|
| **PDF**   |  —  |  ✅  |  ✅  | ✅  |
| **DOCX**  | ✅  |  —   |      | ✅  |
| **PPTX**  | ✅  |      |  —   | ✅  |
| **TXT**   | ✅  |  ✅  |      | —   |

Conversion uses **ConvertAPI** online when available, with **offline fallbacks**
(`pdf2docx`, `docx2pdf`, `pypdf`, `python-docx`, `python-pptx`, `reportlab`).

### Handy shortcuts (Windows)
Hold a key and **left-click** the ghost:
- **Q** → Quick Links
- **F** → File Basket
- **A** → Ask AI

*(On macOS/Linux, use the right-click menu instead.)*

---

## 🛠️ Tech Stack

- **Python 3.13**
- **PyQt6** — GUI, window, animation, drag & drop
- **google-genai** — Gemini AI integration
- **pypdf · python-docx · python-pptx · pdf2docx · reportlab** — document handling
- **convertapi · docx2pdf** — online/offline conversion helpers
- **python-dotenv** — loading API keys from `.env`
- **pyobjc** *(macOS only)* — native window behavior

---

## 📦 Installation

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd project-3-groupp9
```

### 2. Create a virtual environment (recommended)
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

> **Note:** the code also uses `python-dotenv`, `convertapi`, and `docx2pdf`, which
> are not yet in `requirements.txt`. If you hit an import error, install them too:
> ```bash
> pip install python-dotenv convertapi docx2pdf
> ```

### 4. Set up your API keys
Create a file named **`.env`** in the project root:
```env
GEMINI_API_KEY=your_gemini_api_key_here
CONVERTAPI_SECRET=your_convertapi_secret_here   # optional, for online conversion
```
- Get a Gemini key from **Google AI Studio**.
- `CONVERTAPI_SECRET` is optional — without it, conversions fall back to offline libraries.

---

## 🚀 Running

```bash
python main.py
```

A little ghost should appear at the bottom of your screen. **Right-click it** to open
the Quick Menu and explore all the features. Try **Demo Mode** for a guided tour!

---

## 📂 Project Structure

```
project-3-groupp9/
├── main.py                    # Entry point — starts the app
├── ghost_window.py            # Main ghost window: visuals, menu, drag/drop, animation
├── ghost_movement.py          # Movement logic: walking, jumping, idle behavior
├── speech_bubble.py           # Floating speech-bubble widget
├── requirements.txt
├── .gitignore
├── assets/                    # Sprite frames for each character
│   ├── ghost1/                # idle / walk / jump / sleep PNGs
│   ├── ghost2/
│   └── ghost3/
└── features/
    ├── ask_ai.py              # AI chat dialog + file attachment/reading
    ├── gemini_ai.py           # Gemini API client wrapper
    ├── file_basket.py         # File holding, drag-out, and format conversion
    ├── quick_links.py         # Bookmark manager
    ├── reminder_manager.py    # Timed reminders
    └── task_manager.py        # Daily task list
```

User data (settings, reminders, tasks, quick links) is stored as JSON files in a
`user_data/` folder created at runtime.

---

## 🖥️ Platform Notes

- **Windows** — full support, including the keyboard + click shortcuts.
- **macOS** — extra native window handling keeps the ghost visible across spaces and
  full-screen apps (via `pyobjc`). Keyboard shortcuts fall back to the menu.
- **Linux** — should run with PyQt6; window-stacking behavior may vary by desktop
  environment.

---

## 🔑 Requirements Summary

- Python **3.13+**
- A **Gemini API key** (for the Ask AI feature)
- *(Optional)* a **ConvertAPI secret** for online file conversion

---

## 👥 Authors

- Gökçe
- Melike

---

## 📝 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.
