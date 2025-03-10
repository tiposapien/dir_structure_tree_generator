# 🗂️ ASCII Tree Diagram Generator

I use tree diagrams to inform AI assistants when developing. This script was created in order to easily copy and provide the project structure. It's a **cross-platform** Python-based GUI application for **visualizing, selecting, and copying directory structures**.

 - Readme.md created by ChatGPT 4o  
 - Code created by ChatGPT o1  

✅ **Supports collapsible folders**  
✅ **Intuitive checkbox toggling via `[•]` format**  
✅ **Hidden file toggle** (`dotfiles & Windows hidden attributes`)  
✅ **Copy checked files/folders**  
✅ **Expandable & customizable**

## 📸 Screenshot
*(Example output when viewing a directory tree)*  

```
[•] Tree: my_project/
[•]    ├──  src/
[•]    │   ├──  main.py
[•]    │   ├──  utils.py
[•]    │   └──  config.yaml
[•]    ├──  static/
[•]    │   ├──  css/
[•]    │   │   └──  styles.css
[•]    │   ├──  js/
[•]    │   │   └──  scripts.js
[•]    ├──  README.md
[•]    ├──  requirements.txt
[•]    └──  .gitignore
```

---

## 🚀 Features

### 🌳 **Directory Tree Visualization**
- Automatically **sorts directories first**, then files (both alphabetically).
- **Collapsible folders**: Click on folder names or arrows (`► ▼`).
- **Expandable UI**: Resize the window dynamically.

### ✅ **Check/Uncheck Files & Folders**
- **Click `[•]`** to check/uncheck files or folders.
- **Clicking a folder's `[•]`** toggles all children.
- **If a child is checked, its parent is auto-checked**.

### 🔍 **Hidden Files Toggle**
- **Unix dotfiles (`.hidden`) and Windows hidden files** can be toggled.
- Uses `inotify` (Linux) or `ctypes` (Windows) to detect hidden attributes.

### 📋 **Clipboard Copying**
- **Click the "📋 Copy" button** to copy only checked files/folders.
- **If nothing is checked**, a `"Nothing to copy"` message appears.

---

## 📥 Installation

### **1️⃣ Install Dependencies**
This script runs on **Python 3.8+**. Install dependencies:

```sh
pip install tk
```

*(Tkinter typically built into Python, but ensure it's installed on Linux.)*

### **3️⃣ Run the Application**
```sh
python tree_viewer.py /path/to/directory 
```
(pythonw ... on mac)  
*(If no path is provided, it defaults to the current directory.)*

---

## 🛠️ Usage

### **📂 Opening a Directory**
```sh
pythonw tree_viewer.py /users/osemrosi/projects/
```
- Opens the **`projects`** directory tree.

### **📜 Copying Checked Files**
- **Check files/folders** by clicking `[•]`.
- **Press 📋 Copy** – Selected paths are copied to your clipboard.

### **⚙️ Toggle Hidden Files**
- **Check "Include hidden files"** to show **dotfiles & hidden attributes**.

### **⟳ Refresh**
- Click the **"⟳ Re-run"** button to refresh the file list.

---

## ⚡ Operations

| Action                    | Shortcut                      |
|---------------------------|------------------------------|
| **Expand/Collapse Folder** | Click `►` or `▼` |
| **Check/Uncheck File** | Click `[•]` |
| **Copy Selection** | Click **📋 Copy** |
| **Refresh Tree** | Click **⟳ Re-run** |
| **Toggle Hidden Files** | Check/Uncheck `Include hidden files` |
| **Scroll** | Mouse Wheel / Touchpad |

---

## Testing
- tested on mac, not yet run on windows or linux
- MacOS Sequoia 15.3.1
- Python 3.12.4 

---

## 📝 License
MIT License © 2025 TipoSapien

