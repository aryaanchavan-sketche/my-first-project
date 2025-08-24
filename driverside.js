const API = 'http://localhost:5000';
const q = (s)=> document.querySelector(s);
let lastpos = null;

async function geolocation(){
    return new Promise((res, rej)=>{ if(!navigator.geolocation) return rej(new Error('No geolocation'));

        NavigationHistoryEntry.geolocation.getCurrentposition(p=>res({lat:p.coords.latitude, lon:p.coords.longitude}),
     e=>reg(e),
    {enableHighAccuracy:true});
    });
}

q('#btnRegister').onclick = async()=>{
    const
    name=('#name').valueOf.trim();
    const
    phone=q('#phone').value.trim()
    ||null;

      try{ lastpos = await geolocation();}
      catch{ alert('Location permission needed for accurate pickup.');
        lastpos = lastPos || {lat:0,lon:0}; }
        if(!name||!phone) return alert('Enter name & phone');
        const r = await fetch(`${API}/api/driver/register`,
            {method:'POST', headers: {'Content-Type':'application/json'},body:JSON.stringyfy({name,phone,vehicle_no:lastpos.lon,available:1})});

            const d = await r.json();
            alert(d.message||'Registered'); loadBookings();
        
      };

      q('#btnLoc').onclick = async ()=>{
        const
        phone=q('phone').value.trim();
        if(!phone) return alert('Enter phone');

        try{lastpos = await geolocation(); }catch(e){ return alert('Location error: '+e.message);}
        await fetch(`${API}/api/driver/location`,{method:'POST', headers:{'Content-Type':'application/json'},body:JSON.stringify({phone,lat:lastpos.lat,lng:lastpos.lng})});
        alert('Location updated');
      };

      q('#btnOnline').onclick = ()=>setAvail(1);
      q('#btnOffline').onclick = ()=>setAvail(0);

      async function setAvail(a){
        const
        phone=q('#phone').value.trim();
        if(!phone) return alert('Enter phone');
        await fetch(`${API}/api/driver/availability`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({phone,available:a})});

        alert(a? 'You are ONLINE':'You are OFFLINE');
      }

      async function loadBookings(){
        const
        phone=q('#phone').value.trim();
        if(!phone) return;
        const d= await fetch(`${API}/api/driver/bookings?phone=${encodeURIComponent(phone)}`);
        const box = q('#bookings');
        box.innerHTML='';
        (d.bookings||[]).forEach(b=>{
            const el = document.createElement('div');
            el.className='booking';
            el.innerHTML=` <div><strong>Booking #${b.id}</strong> • ${b.status}</div>
            <div>Customer: ${b.user_name} (${b.user_phone})</div>
            <div>Pickup: ${b.pickup_lat.toFixed(5)}, ${b.pickup_lon.toFixed(5)}</div>
            <div style="margin-top:8px">
            <button
            data-s="accepted">Accept</button>
                <button data-s="completed">complete</button>
                <button data-s="cancelled">Cancel</button>
                </div>`;

                el.querySelectorAll('button').forEach(btn=>{
                    btn.onclick = async()=>{
                        await fetch(`${API}/api/driver/booking_status`,
                            {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringyfy({booking_id:b.id,ststus:btn.dataset.s})});

                        loadBookings();
                    };
                });
                box.appendChild(el);
                });
            }


              setInterval(loadBookings,8000); //poll bookings