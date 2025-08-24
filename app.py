import os, sqlite3, math, random, secrets, hmac, hashlib, logging
from datetime import datetime, timedelta
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import jwt
from dotenv import load_dotenv
from db_init import init_db

try:
    import razorpay
except Exception:
    razorpay = None

# Load environment variables
load_dotenv()
DB_PATH = Path(__file__).parent / "rikshaw.db"
SECRET = os.getenv('APP_SECRET', "dev_secret_change_me")
JWT_AUD = 'rikshaw'
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = SECRET
socketio = SocketIO(app, cors_allowed_origins='*')

# Razorpay client (live) if keys provided
rz_client = None
if RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET and razorpay:
    rz_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

# ---helpers---

def get_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logging.error(f"Database connection failed: {e}")
        raise

#Haversine distance in km

def haversine(lat1, lng1, lat2, lng2):
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(phi2 - phi1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    return 2*R*math.atan2(math.sqrt(a), math.sqrt(1 - a))

#Dynamic fare model

def estimate_fare_km(distance_km: float, hour: int):
    base = 20
    per_km = 10
    surge = 1.25 if (8<= hour <= 11 or 17 <= 20) else 1.0 
    traffic = 0.9 + random.random()*0.4 #0.9-1.3
    fare = (base + per_km * distance_km) * surge * traffic
    return round(max(30, fare), 2)

# CO2 saved (approx) for shared rides

def co2_saved_shared(distance_km: float, passengers: int):
    if passengers < 2:
        return 0.0
    solo = 0.1 * distance_km
    shared = solo / passengers
    return round(solo - shared, 3)

# Slight movement simulation so markers feel alive (when no live GPS)

def simulate_driver_movement(rows):
    out = []
    for r in rows:
        lat = r['lat'] + random.uniform(-0.0005, 0.0005)
        lng = r['lng'] + random.uniform(-0.0005, 0.0005)
        out.append({**dict(r), 'lat': lat, 'lng': lng})
    return out

# Auth helpers

def issue_token(user_id, phone):
    payload = {
        'sub': str(user_id), 'phone': phone, 'aud': JWT_AUD,
        'iat': datetime.utcnow(), 'exp': datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, SECRET, algorithm='HS256')

def current_user():
    auth = request.headers.get('Authorization', '').split('Bearer ')
    if len(auth) != 2:
        return None
    token = auth[1]
    try:
        payload = jwt.decode(token, SECRET, algorithms=['HS256'], audience=JWT_AUD)
        return int(payload['sub'])
    except Exception:
        return None

# --- routes ---

@app.get('/api/health')
def health():
    return {'ok': True}

# OTP login (demo SMS)
@app.post('/api/otp/request')
def otp_request():
    data = request.get_json(force=True)
    phone = data.get('phone')
    name = data.get('name') or 'User'
    if not phone or not isinstance(phone, str) or len(phone) < 8:
        return jsonify({'error': 'Valid phone required'}), 400
    code = f"{random.randint(100000, 999999)}"
    exp = datetime.utcnow() + timedelta(minutes=5)
    try:
        con = get_db(); cur = con.cursor()
        cur.execute('INSERT OR IGNORE INTO users(phone, name) VALUES(?, ?)', (phone, name))
        cur.execute('REPLACE INTO otps(phone, code, expires_at) VALUES(?, ?, ?)', (phone, code, exp.isoformat()))
        con.commit(); con.close()
        logging.info(f"[MOCK OTP] to {phone}: {code}")
        return jsonify({'sent': True})
    except Exception as e:
        logging.error(f"OTP request failed: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.post('/api/otp/verify')
def otp_verify():
    data = request.get_json(force=True)
    phone = data.get('phone')
    code = data.get('code')
    if not phone or not code:
        return jsonify({'error': 'phone and code required'}), 400
    try:
        con = get_db(); cur = con.cursor()
        cur.execute('SELECT code, expires_at FROM otps WHERE phone=?', (phone,))
        row = cur.fetchone()
        if not row:
            con.close(); return jsonify({'error': 'otp not requested'}), 400
        if row['code'] != code:
            con.close(); return jsonify({'error': 'invalid code'}), 400
        if datetime.fromisoformat(row['expires_at']) < datetime.utcnow():
            con.close(); return jsonify({'error': 'code expired'}), 400
        cur.execute('SELECT * FROM users WHERE phone=?', (phone,)); u = cur.fetchone()
        token = issue_token(u['id'], phone)
        con.close()
        return jsonify({'token': token, 'user': {'id': u['id'], 'phone': phone, 'name': u['name'], 'subscription_active': bool(u['subscription_active'])}})
    except Exception as e:
        logging.error(f"OTP verify failed: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# Subscription payment (mock + pluggable verification)
@app.post('/api/pay/create_order')
def pay_create_order():
    user_id = current_user()
    if not user_id:
        return {'error': 'unauthorized'}, 401
    amount_rupees = 1  # ₹1
    amount_paise = amount_rupees * 100
    con = get_db(); cur = con.cursor()
    if rz_client:
        try:
            order = rz_client.order.create({"amount": amount_paise, "currency": "INR", "receipt": f"sub_{user_id}_{secrets.token_hex(4)}", "payment_capture": 1})
            cur.execute("INSERT INTO payments(user_id, provider, order_id, amount, status) VALUES(?,?,?,?,?)", (user_id, "razorpay", order["id"], amount_rupees, "created"))
            con.commit(); con.close()
            return {
                "provider": "razorpay",
                "order_id": order["id"],
                "amount": amount_rupees,
                "currency": "INR",
                "key_id": RAZORPAY_KEY_ID,
            }
        except Exception as e:
            con.close()
            return {"error": f"Razorpay order creation failed: {e}"}, 500
    else:
        # mock order (no gateway)
        order_id = secrets.token_hex(8)
        cur.execute("INSERT INTO payments(user_id, provider, order_id, amount, status) VALUES(?,?,?,?,?)", (user_id, "mock", order_id, amount_rupees, "created"))
        con.commit(); con.close()
        return {"provider": "mock", "order_id": order_id, "amount": amount_rupees}
    
@app.post('/api/pay/verify')
def pay_verify():
    user_id = current_user()
    if not user_id:
        return {'error': 'unauthorized'}, 401
    d = request.get_json(force=True)
    con = get_db();cur =con.cursor()
    if rz_client: #Except: razorpay_order_id, razorpay_payment_id,razorpay_signature
        try:
            rz_client.utility.verify_payment_signature({
                "razorpay_order_id": d["razorpay_order_id"],
                "razorpay_payment_id":d["razorpay_payment_id"],
                "razorpay_signature":d["razorpay_signature"],
            })
        except Exception as e:
            con.close()
            return{"ok": False,"error":f"verification failed: {e}"},400
        cur.execute("UPDATE payments SET status='paid' WHERE order_id=?", (d["razorpay_order_id"],))
        cur.execute("UPDATE users SET subscription_active=1 WHERE id=?", (user_id,))
        con.commit(); con.close()
        return{"ok": True, "subscription_active": True}
    #mock pathway
    order_id = d.get('order_id')
    if not order_id:
        con.close()
        return {'error': 'order_id required'}, 400
    # If you integrate Razorpay/Paytm, verify signature here. For now, mark paid.
    cur.execute('UPDATE payments SET status="paid" WHERE order_id=?', (order_id,))
    cur.execute('UPDATE users SET subscription_active=1 WHERE id=?', (user_id,))
    con.commit(); con.close()
    return {'ok': True, 'subscription_active': True}

@app.get('/api/users/me')
def me():
    user_id = current_user()
    if not user_id:
        return {'error': 'unauthorized'}, 401
    con = get_db(); cur = con.cursor()
    cur.execute('SELECT * FROM users WHERE id=?', (user_id,)); u = cur.fetchone(); con.close()
    return {'id': u['id'], 'name': u['name'], 'phone': u['phone'], 'subscription_active': bool(u['subscription_active'])}

@app.get('/api/drivers/nearby')
def drivers_nearby():
    try:
        lat = float(request.args['lat']); lng = float(request.args['lng'])
    except Exception:
        return {'error': 'lat & lng required'}, 400
    radius = float(request.args.get('radius_km', 5))
    con = get_db(); cur = con.cursor()
    cur.execute('SELECT * FROM drivers WHERE active=1')
    rows = cur.fetchall(); con.close()
    rows = simulate_driver_movement(rows)
    drivers = []
    for r in rows:
        d = haversine(lat, lng, r['lat'], r['lng'])
        if d <= radius:
            drivers.append({
                'id': r['id'], 'name': r['name'], 'phone': r['phone'], 'vehicle_no': r['vehicle_no'],
                'lat': r['lat'], 'lng': r['lng'], 'distance_km': round(d,2), 'trips_completed': r.get('trips_completed', 0)
            })
    drivers.sort(key=lambda x: x["distance_km"])
    return{"drivers": drivers}

@app.get("/api/fare-estimated")
def fare_estimated():
    try:
        lat1 = float(request.args["start_lat"])
        lng1 = float(request.args["start_lng"])
        lat2 = float(request.args["end_lat"])
        lng2 = float(request.args["end_lng"])
    except Exception:
        return{
            "error": "start_lat,start_lng,end_lat,end_lng required"}, 400
    d_km = haversine(lat1,lng1,lat2,lng2)
    fare= estimate_fare_km(d_km,datetime.now().hour)
    return {"distance_km": round(d_km,2),"fare_estimated": fare}
    
@app.post("/api/bookings")
def creat_booking():
    d = request.get_json(force=True)
    phone = d.get("user_phone")
    driver_id = d.get("driver_id")
    share = 1 if d.get("shared") else 0
    pickup_lat = d.get("pickup_lat")
    pickup_lng = d.get("pickup_lng")
    end_lat = d.get("end_lat")
    end_lng = d.get("end_lng")
    # Input validation
    if not phone or not driver_id or pickup_lat is None or pickup_lng is None:
        return jsonify({"error": "user_phone, driver_id, pickup_lat, and pickup_lng required"}), 400
    try:
        con = get_db(); cur = con.cursor()
        cur.execute("SELECT * FROM users WHERE phone=?", (phone,)); u = cur.fetchone()
        if not u:
            con.close(); return jsonify({"error": "user not found"}), 404
        cur.execute("INSERT INTO bookings(user_name, user_phone, driver_id, pickup_lat, pickup_lng, notes, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (u["name"], phone, driver_id, pickup_lat, pickup_lng, d.get("notes", ""), "created"))
        con.commit()
        cur.execute("SELECT * FROM bookings WHERE user_phone=? ORDER BY created_at DESC", (phone,))
        rows = [dict(r) for r in cur.fetchall()]
        con.close()
        return jsonify({"bookings": rows})
    except Exception as e:
        logging.error(f"Booking creation failed: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.get("/api/leaderboard")
def leaderboard():
    con = get_db(); cur = con.cursor()
    cur.execute("SELECT id, name, trips_completed FROM drivers WHERE active=1 ORDER BY trips_completed DESC, id ASC LIMIT 10")
    rows = [dict(r) for r in cur.fetchall()]
    con.close(); return {"leaders": rows}
    
    #Driver live GPS update (used by driver app)

@app.post("/api/drivers/update_location")

def driver_update_location():
    d = request.get_json(force=True)
    driver_id = d.get("driver_id")
    lat = d.get("lat")
    lng = d.get("lng")
    active = d.get("active", 1)
    if not driver_id or lat is None or lng is None:
        return jsonify({"error": "driver_id, lat, lng required"}), 400
    try:
        con = get_db(); cur = con.cursor()
        cur.execute("UPDATE drivers SET lat=?, lng=?, active=? WHERE id=?", (lat, lng, int(bool(active)), driver_id))
        con.commit(); con.close()
        socketio.emit("driver: location", {"driver_id": driver_id, "lat": lat, "lng": lng, "active": bool(active)})
        return jsonify({"ok": True})
    except Exception as e:
        logging.error(f"Driver location update failed: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.post('/api/mock/sms')
def mock_sms():
    d = request.get_json(force=True) 
    to, body = d.get("to"), d.get("body")
    if not to or not body:
        return{"error":"to and body required"},400
    print(f"[MOCK SMS] to {to}: {body}")
    return {"ok":True}

@app.get("/api/share_lookup")
def share_lookup():
    token = request.args.get("token")
    if not token:
        return{"error": "token required"},400
    con = get_db(); cur = con.cursor()
    cur.execute("SELECT b.*, d.name as driver_name, d.phone as driver_phone FROM bookings b JOIN drivers d ON d.id=b.driver_id WHERE share_token=?", (token,))
    row = cur.fetchone();con.close()
    if not row:
        return{"error": "not found"}, 404
    return {
        "booking_id": row["id"],
        "status": row["status"],
        "shared": bool(row["shared"]),
        "driver_name": row["driver_name"],
        "driver_phone": row["driver_phone"],
        "fare_estimated": row["fare_estimated"],
        "co2_saved_kg": row["co2_saved_kg"]
    }
    
if __name__=="__main__":
    init_db()
    socketio.run(app, port=8000, debug=True)

# Route definitions should be above this block

@app.post("/api/users/register")
def register():
    d = request.get_json(); name, phone = d["name"], d["phone"]
    con=get_db(); cur = cur.cursor()
    try:
        cur.execute("INSERT INTO users(name,phone) VALUES(?,?)", (name, phone))
        con.commit()
    except Exception:
        pass
    cur.execute("SELECT * FROM users WHERE phone=?", (phone,))
    u = cur.fetchone()
    con.close()
    return dict(id=u["id"], name=u["name"], phone=u["phone"], subscription_active=bool(u["subscription_active"]))
@app.post("/api/users/subscribe")
def subscribe():
   phone=request.get_json()["phone"]
   con=get_db(); cur=con.cursor()
   cur.execute("UPDATE users SET subscription_active=1 WHERE phone=?",(phone,))
   cur.execute("SELECT * from users WHERE phone=?", (phone,))
   u=cur.fetchone();con.close()
   return {"subscription_active":bool(u["subscription_active"])}

if __name__=="__main__":
    init_db()
    app.run(port=8000,debug=True)
    
