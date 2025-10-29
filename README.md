# Karu the Fox 🦊

Karu is a clever and friendly virtual desktop pet . Built with Python and PySide6, Karu can chat with you, play music, and react to your presence.

<!-- *(Suggestion: Record a 5-10 second GIF of Karu walking, sleeping, and the chat window opening, and place it here!)*
`![Karu Demo GIF](link-to-your-demo-gif.gif)` -->

---

## ✨ Features

* **Interactive AI Chat:** Have a real conversation with Karu, powered by the Google Gemini API. Karu has a unique, supportive, and slightly sassy personality.
* **Built-in Music Player:** A sleek, self-contained music player that scans your local `music/` folder and remembers your volume and song settings.
* **Dynamic Onboarding:** On first launch, Karu greets you and asks about your day with a simple mood survey.
* **Desktop Animations:** Karu doesn't just sit there—it walks, sleeps, pauses, and reacts to being dragged around.
* **System Tray Menu:** A right-click system tray icon gives you quick access to all of Karu's features, including the chat, music player, and exit button.

---

<!-- ## 🖼️ Screenshots

*(Replace these with actual screenshots of your app)*

| Chat Window | Music Player |
| :---: | :---: |
| `` | `` |

--- -->

## 💻 Technology Stack

* **Python 3**
* **PySide6** (Qt for Python) for the application framework and UI.
* **Google Gemini API** for the generative AI chat functionality.

---

## 🚀 Getting Started

Follow these steps to set up and run the project on your local machine.

### 1. Prerequisites

Make sure you have **Python 3.10** or newer installed.

### 2. Clone the Repository

```bash
git clone [https://github.com/your-username/karu-the-fox.git](https://github.com/your-username/karu-the-fox.git)
cd karu-the-fox
```

### 3. Set Up a Virtual Environment

It's highly recommended to use a virtual environment.

* **Windows:**
    ```bash
    python -m venv venv
    venv\Scripts\activate
    ```
* **macOS / Linux:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

### 4. Install Dependencies

Install all the required Python packages:

```bash
pip install -r requirements.txt
```

### 5. Configure the API key

This project uses the Gemini API, which requires a secret key.

1.  Copy the example `.env` file to create your own:
    ```bash
    # On Windows (Command Prompt)
    copy .env.example .env
    
    # On macOS/Linux
    cp .env.example .env
    ```
2.  Open the new `.env` file (it's hidden by default) in a text editor.
3.  Get your Gemini API key from the [Google AI Studio](https://aistudio.google.com/app/apikey).
4.  Paste your key into the file:
    ```
    # .env
    GEMINI_API_KEY=YOUR_API_KEY_GOES_HERE
    ```

### 6. (Optional) Add Your Music

The music player scans the `music/` folder. For the app to find your songs, you must follow a specific folder structure: