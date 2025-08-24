# Rikshaw Finder - Quick Start

## 1) Creat & activate a virtual environment

python -m venv .venv

# windows
.\\.venv\\scripts\\activate

# macOS/Linux
Source .venv/bin/activate

## 2) Install deependencies

pipp install -r requirements.txt

## 3) Run the backend
cd backend
python app.py

# API at http://localhost:5000

## 4) Open the frontends
- User site: open `frontend_user/index.html` in a browser (or VS code Live Server)
- Driver app: open `frontend_driver?index.html`

## 5} seed a couple of drivers (one-time for testing)

Use your browser console on any page:

fetch('http://localhost:5000/api/driver/register',{method:'POST',headers:{'content-Type': 'application/json'},body:JSON.stringify({name:'Raju', phone: '90000000001', vehicle_no:'MH12 XY9876', lat:18.531, lon:73.844, availabel:1})})

## Notes
- ₹1 subscription is **mocked**; replace with Razorpay/UPI for production.
- No authentication in MVP. Add JWT/auth & rate limits before deployment.
- Keep API URL consistent frontend(default httpss://localhost:5000)
