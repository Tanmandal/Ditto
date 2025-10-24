# 🧬 Ditto — Smart URL Shortener (Frontend)

**Ditto** is a beautiful, modern URL shortener frontend built using [Flet](https://flet.dev/), a Python framework for building real-time reactive web apps.
It connects to the backend API — **[Short-URL](https://github.com/Tanmandal/Short-URL)** — built with FastAPI, to provide an intuitive, secure, and full-featured interface for creating and managing short links.

---

## 🚀 Features

* ✂️ **Create Short URLs** — Instantly shrink long links using a custom alias.
* 🔒 **Password Protection** — Secure your links with optional passwords.
* ⚙️ **Manage Aliases** —

  * View link stats (hits, creation date, status)
  * Change target URL
  * Pause/Resume a link
  * Reset hit count
  * Change password
  * Delete alias permanently
* 🔁 **Auto Token Refresh** — Automatically refreshes access tokens after expiry.
* 🎨 **Minimal UI** — Clean, dark-themed design with real-time feedback.

---

## 🛠️ Tech Stack

| Layer        | Technology                                          |
| ------------ | --------------------------------------------------- |
| **Frontend** | [Flet](https://flet.dev/)                           |
| **Backend**  | [FastAPI](https://fastapi.tiangolo.com/)            |
| **Language** | Python 3.10+                                        |
| **API Repo** | [Short-URL](https://github.com/Tanmandal/Short-URL) |

---

## 📦 Installation

### 1. Clone the repositories

```bash
# Backend (Short-URL)
git clone https://github.com/Tanmandal/Short-URL.git
cd Short-URL
python -m venv venv
source venv/bin/activate    # or venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn main:app --reload
```

Your API should now be running at:

```
http://127.0.0.1:8000
```

---

### 2. Run the frontend (Ditto)

```bash
# Clone frontend
git clone https://github.com/Tanmandal/Ditto.git
cd Ditto

# Install dependencies
pip install flet

# Start the app
python ditto.py
```

You can also specify the API endpoint by changing:

```python
API_BASE_URL = "https://short-url.leapcell.app"
```

to your local or deployed API URL.

---

## 🧭 Usage

1. **Create a short link** — Enter a long URL and a custom alias, optionally set a password.
2. **Copy and share** the generated short link.
3. **Login to manage** — Enter the alias and password to manage your existing link.
4. Perform actions such as:

   * Update the target URL
   * Pause/Resume redirect
   * Reset hit count
   * Change alias password
   * Delete alias permanently

---

## ⚡ API Endpoints Used

| Action            | Method   | Endpoint              |
| ----------------- | -------- | --------------------- |
| Health Check      | `GET`    | `/health`             |
| Create Short URL  | `POST`   | `/create`             |
| Login             | `POST`   | `/login`              |
| Validate Token    | `GET`    | `/validate_token`     |
| Refresh Token     | `GET`    | `/refresh_token`      |
| Get Alias Details | `GET`    | `/details`            |
| Change URL        | `PATCH`  | `/change_url?url=...` |
| Pause/Resume      | `PATCH`  | `/pause` / `/resume`  |
| Reset Hits        | `PATCH`  | `/reset_hits`         |
| Change Password   | `POST`   | `/change_password`    |
| Delete Alias      | `DELETE` | `/delete/{alias}`     |

---

## 💻 Screens Overview

| Screen                  | Description                                                 |
| ----------------------- | ----------------------------------------------------------- |
| **Home / Create Alias** | Create new short URLs and view generated links              |
| **Login Page**          | Authenticate to manage existing aliases                     |
| **Manage Alias**        | Edit URL, change password, reset hits, pause/resume, delete |
| **Service Down Page**   | Shown when API health check fails                           |

---

## 🧠 How It Works

* Uses **async HTTP requests** (via `fetch` for web and `urllib` for desktop).
* Automatically refreshes expired JWT tokens every 8 minutes.
* Unified session handling through the `SessionData` class.
* Fully reactive UI — page content dynamically switches between views.

---

## 🧰 Requirements

* Python ≥ 3.10
* Flet ≥ 0.28.3

---

## 🧑‍💻 Author

**[Tanmandal](https://github.com/Tanmandal)**
Creator of both **Ditto (frontend)** and **Short-URL (backend)** projects.

## 📜 License

This project is open source under the **MIT License**.
See [LICENSE](LICENSE) for more information.
