# RestoM - Premium Restaurant Management System

A complete mono-repo containing the frontend UI and Flask API backend for the RestoM Restaurant Management System.

## Project Structure

```
RestoM-COMPLETE-BACKEND/
├── backend/            # Flask API Backend
│   ├── app/            # Application source code
│   ├── uploads/        # Uploaded menu item images and media
│   ├── requirements.txt# Python package dependencies
│   ├── run.py          # Backend server entrypoint
│   └── .env            # Environment configuration (ignored by Git)
├── frontend/           # Static HTML/CSS/JS Frontend
│   ├── assets/         # Images and visual resources
│   ├── css/            # Stylings
│   ├── js/             # Frontend application logic
│   └── index.html      # Landing & Login Page
├── .gitignore          # Git exclusion rules
└── README.md           # Project documentation
```

---

## Getting Started

### Prerequisites
1. **Python 3.8+** (Installed and in PATH).
2. **MySQL Database Server** (e.g., via XAMPP/WAMP or local installation) running on port `3306`.
3. Create a database named `restaurant_management_system` in your MySQL server.

---

### Backend Setup and Running

1. Navigate to the `backend` directory:
   ```bash
   cd backend
   ```

2. Activate the virtual environment:
   * **Windows (PowerShell)**:
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
   * **Windows (Command Prompt)**:
     ```cmd
     .\venv\Scripts\activate.bat
     ```
   * **Linux/macOS**:
     ```bash
     source venv/bin/activate
     ```

3. Install dependencies (if not already installed):
   ```bash
   pip install -r requirements.txt
   ```

4. Configure the environment:
   * Edit `.env` to specify your database connection details and optional SMTP configurations:
     ```ini
     DATABASE_URL=mysql+pymysql://root:YOUR_PASSWORD@localhost:3306/restaurant_management_system
     ```

5. Run the server:
   ```bash
   python run.py
   ```
   The Flask API will run on **`http://localhost:5000`**.

---

### Frontend Setup and Running

Since the frontend is built using static HTML/CSS/JS, it can be served using any local HTTP web server.

1. Serve the `frontend` directory using a simple server.
   * **Using Python**:
     ```bash
     cd frontend
     python -m http.server 8000
     ```
2. Open **`http://localhost:8000/index.html`** in your browser.

*Note: The frontend is configured in [frontend/js/api.js](file:///c:/Users/Administrator/Desktop/RestoM-COMPLETE-BACKEND/frontend/js/api.js) to communicate with the backend. When deploying to production (Render), update the `LIVE_BACKEND_URL` variable at the top of `api.js` to point to your live Render backend Web Service.*
