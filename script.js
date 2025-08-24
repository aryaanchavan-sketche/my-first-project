const API = "http://localhost:8000"; // Update to your backend URL in production
let userPos = null;
const q = (s) => document.querySelector(s);

async function checkSub() {
    const phone = q("#phone").value.trim();
    if (!phone) {
        q("#subStatus").textContent = "Enter your phone, then subscribe.";
        return;
    }
    // Example: Replace with your actual subscription status endpoint
    try {
        const r = await fetch(`${API}/api/users/me`, {
            headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
        });
        const d = await r.json();
        q("#subStatus").textContent = d.subscription_active ? "Subscription: ACTIVE" : "Subscription: INACTIVE";
    } catch (e) {
        q("#subStatus").textContent = "Error checking subscription.";
    }
}

q("#subscribeBtn").onclick = async () => {
    // Example: Replace with your actual subscribe endpoint
    try {
        const r = await fetch(`${API}/api/users/subscribe`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ phone: q("#phone").value.trim() })
        });
        const d = await r.json();
        alert(d.message || "Subscribed");
        checkSub();
    } catch (e) {
        alert("Subscription failed");
    }
};

q("#phone").addEventListener("input", checkSub);

q("#locationBtn").onclick = () => {
    if (!navigator.geolocation)
        return alert("Geolocation not supported");
    navigator.geolocation.getCurrentPosition(
        (p) => {
            userPos = { lat: p.coords.latitude, lng: p.coords.longitude };
            q("#lat").value = userPos.lat;
            q("#lng").value = userPos.lng;
            alert(`Location set: ${userPos.lat.toFixed(4)}, ${userPos.lng.toFixed(4)}`);
        },
        (err) => alert("Location error: " + err.message),
        { enableHighAccuracy: true }
    );
};

q("#searchBtn").onclick = async () => {
    if (!userPos) return alert("Use MY Location first");
    const rad = Number(q("#radius").value) || 5;
    try {
        const r = await fetch(`${API}/api/drivers/nearby?lat=${userPos.lat}&lng=${userPos.lng}&radius_km=${rad}`);
        const d = await r.json();
        renderDrivers(d.drivers || []);
    } catch (e) {
        alert("Failed to fetch drivers");
    }
};

function renderDrivers(list) {
    const div = q("#drivers");
    div.innerHTML = "";
    if (!list.length) {
        div.textContent = 'No drivers in this radius.';
        return;
    }
    list.forEach(dr => {
        const el = document.createElement('div');
        el.className = 'driver-card';
        el.innerHTML = `
        <div>
        <div><strong>${dr.name}</strong> • ${dr.vehicle_no || '_'} </div>
        <div class="driver-meta">${dr.phone} • ${dr.distance_km} km away</div>
        </div>
        <div class="actions">
        <button class="bookBtn">Book</button>
        </div>`;
        el.querySelector('.bookBtn').onclick = () => bookDriver(dr.id);
        div.appendChild(el);
    });
}

async function bookDriver(driverId) {
    const name = q('#name').value.trim();
    const phone = q('#phone').value.trim();
    const notes = q('#notes') ? q('#notes').value.trim() : "";
    if (!name || !phone) return alert('Enter your name and phone');
    if (!userPos) return alert('Set your location first');
    try {
        const r = await fetch(`${API}/api/bookings`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_name: name, user_phone: phone, driver_id: driverId, pickup_lat: userPos.lat, pickup_lng: userPos.lng, notes })
        });
        const d = await r.json();
        alert(d.message || 'Booking created!');
    } catch (e) {
        alert('Booking failed');
    }
}

q('#subStatus').textContent = 'Enter phone and subscribe (mock) or search directly.';