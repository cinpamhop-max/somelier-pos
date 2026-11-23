
from flask import Flask, request, jsonify, session, render_template_string
import sqlite3, os, secrets
from datetime import datetime
from functools import wraps

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(APP_DIR, "sommelier.db")
app = Flask(__name__)
app.secret_key = os.environ.get("SOMMELIER_SECRET", secrets.token_hex(32))
USERS = {
    "admin": {"pin": os.environ.get("SOMMELIER_ADMIN_PIN", "1234"), "role": "admin", "name": "Administrador"},
    "caja": {"pin": os.environ.get("SOMMELIER_CAJA_PIN", "2468"), "role": "cashier", "name": "Caja"},
    "mozo": {"pin": os.environ.get("SOMMELIER_MOZO_PIN", "1111"), "role": "waiter", "name": "Mozo"},
    "cocina": {"pin": os.environ.get("SOMMELIER_COCINA_PIN", "2222"), "role": "kitchen", "name": "Cocina"},
}
def db():
    con=sqlite3.connect(DB_PATH); con.row_factory=sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON"); return con
def init_db():
    con=db()
    con.executescript('''
    CREATE TABLE IF NOT EXISTS products(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,category TEXT NOT NULL DEFAULT 'General',price REAL NOT NULL DEFAULT 0,active INTEGER NOT NULL DEFAULT 1);
    CREATE TABLE IF NOT EXISTS tables_rest(id INTEGER PRIMARY KEY,label TEXT NOT NULL,active INTEGER NOT NULL DEFAULT 1);
    CREATE TABLE IF NOT EXISTS orders(id INTEGER PRIMARY KEY AUTOINCREMENT,table_id INTEGER NOT NULL,status TEXT NOT NULL DEFAULT 'open',waiter TEXT NOT NULL,created_at TEXT NOT NULL,closed_at TEXT,total REAL NOT NULL DEFAULT 0,payment_method TEXT,FOREIGN KEY(table_id) REFERENCES tables_rest(id));
    CREATE TABLE IF NOT EXISTS order_items(id INTEGER PRIMARY KEY AUTOINCREMENT,order_id INTEGER NOT NULL,product_id INTEGER,product_name TEXT NOT NULL,qty INTEGER NOT NULL,unit_price REAL NOT NULL,notes TEXT DEFAULT '',status TEXT NOT NULL DEFAULT 'pending',created_at TEXT NOT NULL,FOREIGN KEY(order_id) REFERENCES orders(id));
    ''')
    if con.execute("SELECT COUNT(*) FROM tables_rest").fetchone()[0]==0:
        con.executemany("INSERT INTO tables_rest(id,label) VALUES(?,?)",[(i,f"Mesa {i}") for i in range(1,13)])
    if con.execute("SELECT COUNT(*) FROM products").fetchone()[0]==0:
        sample=[("Parrilla libre","Parrilla",30000),("Asado al plato","Parrilla",20000),("Vacío","Parrilla",0),("Picaña","Parrilla",0),("Papas Sommelier","Guarniciones",9000),("Mandioca frita","Guarniciones",6000),("Empanada de osobuco","Entradas",15000),("Empanada de humita","Entradas",14000),("Empanada caprese","Entradas",14000),("Sándwich de milanesa","Platos",15000),("Rabas","Entradas",13000),("Quilmes sin alcohol","Bebidas",3000),("Red Bull","Bebidas",4000),("Agua tónica","Bebidas",3000),("Agua","Bebidas",3000)]
        con.executemany("INSERT INTO products(name,category,price) VALUES(?,?,?)",sample)
    con.commit(); con.close()
def required(*roles):
    def deco(fn):
        @wraps(fn)
        def wrap(*a,**kw):
            if not session.get("user"): return jsonify(error="Iniciá sesión nuevamente."),401
            if roles and session.get("role") not in roles: return jsonify(error="No tenés permiso."),403
            return fn(*a,**kw)
        return wrap
    return deco

PAGE = r'''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Sommelier POS</title><meta name="theme-color" content="#101010"><link rel="manifest" href="/manifest.json"><meta name="apple-mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-status-bar-style" content="black">
<style>
:root{--bg:#101010;--panel:#1b1b1b;--gold:#c9a45c;--muted:#aaa;--line:#333}*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:#f4f0e8;font:15px Arial,sans-serif}header{background:#080808;border-bottom:1px solid #40351f;padding:15px 20px;display:flex;justify-content:space-between;align-items:center;position:sticky;top:0;z-index:5;gap:10px}
.brand{font-size:22px;letter-spacing:4px;color:var(--gold);font-weight:bold}.sub{font-size:11px;color:#aaa;letter-spacing:2px}
button{border:0;border-radius:8px;padding:11px 14px;background:var(--gold);color:#17130b;font-weight:bold;cursor:pointer}button.secondary{background:#333;color:#eee}button.danger{background:#813b3b;color:white}
main{max-width:1250px;margin:auto;padding:20px}.tabs{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:18px}.tabs button{background:#292929;color:#ddd}.tabs button.active{background:var(--gold);color:#111}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:12px}.box{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:15px}
.table-card{min-height:105px;text-align:left;display:flex;flex-direction:column;justify-content:space-between;background:#202020;color:white;border:1px solid #444}.table-card.busy{border-color:var(--gold)}
.row{display:flex;gap:10px;align-items:center;flex-wrap:wrap}.between{justify-content:space-between}.muted{color:var(--muted);font-size:13px}
input,select{background:#111;color:#fff;border:1px solid #444;border-radius:7px;padding:10px;width:100%;margin:5px 0 12px}label{font-size:13px;color:#ccc}
h2{color:var(--gold);font-size:20px}.layout{display:grid;grid-template-columns:1.2fr .8fr;gap:16px}.item{display:flex;justify-content:space-between;align-items:center;gap:8px;border-bottom:1px solid #333;padding:10px 0}.item:last-child{border:0}
.item button{padding:8px 11px}.total{font-size:25px;color:var(--gold);font-weight:bold}.hidden{display:none!important}.login{max-width:380px;margin:9vh auto}.login .brand{margin-bottom:25px}.small{font-size:12px;color:#aaa}
@media(max-width:750px){main{padding:12px}.layout{grid-template-columns:1fr}.brand{font-size:18px}}
</style></head><body><header><div><div class="brand">SOMMELIER</div><div class="sub">SISTEMA DE GESTIÓN</div></div><div class="row"><span id="who" class="muted"></span><button class="secondary" onclick="logout()">Salir</button></div></header><main>
<div id="login" class="login box hidden"><div class="brand">SOMMELIER</div><h2>Ingresar al sistema</h2><label>Usuario</label><select id="username"><option value="mozo">Mozo</option><option value="caja">Caja</option><option value="admin">Administrador</option><option value="cocina">Cocina</option></select><label>PIN</label><input id="pin" type="password" inputmode="numeric" placeholder="PIN"><button style="width:100%" onclick="doLogin()">Ingresar</button><p class="small">PIN inicial: mozo 1111 · caja 2468 · admin 1234 · cocina 2222</p><p id="loginerr"></p></div>
<div id="app" class="hidden"><div class="tabs" id="tabs"></div><section id="view"></section></div></main>
<script>
let me=null,currentTable=null,products=[],tables=[],activeTab='';
const money=n=>new Intl.NumberFormat('es-AR',{style:'currency',currency:'ARS',maximumFractionDigits:0}).format(n||0);
async function api(path,opts={}){let r=await fetch(path,{headers:{'Content-Type':'application/json'},...opts});let d=await r.json().catch(()=>({}));if(r.status===401){showLogin();throw Error(d.error||'Sesión vencida')}if(!r.ok)throw Error(d.error||'Error');return d}
function showLogin(){login.classList.remove('hidden');app.classList.add('hidden')}
async function doLogin(){try{me=await api('/api/login',{method:'POST',body:JSON.stringify({username:username.value,pin:pin.value})});start()}catch(e){loginerr.textContent=e.message}}
async function logout(){await fetch('/api/logout',{method:'POST'});me=null;showLogin()}
async function start(){login.classList.add('hidden');app.classList.remove('hidden');who.textContent=me.name+' · '+me.role;buildTabs();await loadData();go(me.role==='kitchen'?'Cocina':me.role==='waiter'?'Mesas':'Mesas')}
function buildTabs(){let a=me.role==='admin'?['Mesas','Caja','Cocina','Productos','Ventas']:me.role==='waiter'?['Mesas']:me.role==='kitchen'?['Cocina']:['Mesas','Caja','Ventas'];tabs.innerHTML=a.map(t=>`<button onclick="go('${t}')">${t}</button>`).join('')}
async function loadData(){let d=await api('/api/data');products=d.products;tables=d.tables}
function go(t){activeTab=t;document.querySelectorAll('.tabs button').forEach(b=>b.classList.toggle('active',b.textContent===t));if(t==='Mesas')renderTables();if(t==='Caja')renderCash();if(t==='Cocina')renderKitchen();if(t==='Productos')renderProducts();if(t==='Ventas')renderSales()}
async function renderTables(){await loadData();view.innerHTML=`<div class="row between"><div><h2>Mesas</h2><div class="muted">Elegí una mesa para cargar pedidos.</div></div><button class="secondary" onclick="renderTables()">Actualizar</button></div><div class="grid">${tables.map(t=>`<button class="table-card ${t.order_id?'busy':''}" onclick="openTable(${t.id})"><strong>${t.label}</strong><span>${t.order_id?'● Ocupada · '+money(t.total):'○ Disponible'}</span></button>`).join('')}</div>`}
async function openTable(id){currentTable=id;let d=await api('/api/table/'+id);renderOrder(d)}
function productLine(p){return `<div class="item"><div><b>${p.name}</b><div class="muted">${p.category} · ${money(p.price)}</div></div><button onclick="addItem(${p.id})">+ Agregar</button></div>`}
function itemLine(i){return `<div class="item"><div><b>${i.qty} × ${i.product_name}</b><div class="muted">${money(i.unit_price)} c/u ${i.notes?'· '+i.notes:''}</div><div class="small">Estado: ${i.status}</div></div><span>${money(i.qty*i.unit_price)}</span></div>`}
function renderOrder(d){let items=d.items||[];view.innerHTML=`<div class="row between"><div><h2>${d.table.label}</h2><div class="muted">${d.order?'Pedido #'+d.order.id+' · '+d.order.waiter:'Mesa'}</div></div><button class="secondary" onclick="go('Mesas')">← Volver</button></div><div class="layout"><div class="box"><h3>Menú</h3><div id="menuitems">${products.map(productLine).join('')}</div></div><div class="box"><h3>Pedido</h3><div id="orderitems">${items.map(itemLine).join('')||'<p class="muted">Sin productos todavía.</p>'}</div><label>Observación para el próximo producto</label><input id="notes" placeholder="Ej.: sin cebolla, bien cocido"><div class="row between"><span>Total</span><span class="total">${money(items.reduce((s,i)=>s+i.qty*i.unit_price,0))}</span></div><button style="width:100%" onclick="sendKitchen()">Enviar pedido a cocina</button></div></div>`}
async function addItem(pid){let note=notes.value;let d=await api('/api/order/add',{method:'POST',body:JSON.stringify({table_id:currentTable,product_id:pid,notes:note})});renderOrder(d)}
async function sendKitchen(){await api('/api/order/send',{method:'POST',body:JSON.stringify({table_id:currentTable})});alert('Pedido enviado a cocina');openTable(currentTable)}
async function renderCash(){let d=await api('/api/cash');view.innerHTML=`<h2>Caja · Mesas abiertas</h2><div class="grid">${d.orders.map(o=>`<button class="table-card busy" onclick="cashOrder(${o.id})"><strong>Mesa ${o.table_id}</strong><span>${money(o.total)}</span><span class="muted">Pedido #${o.id}</span></button>`).join('')||'<p class="muted">No hay mesas abiertas.</p>'}</div>`}
async function cashOrder(id){let d=await api('/api/order/'+id);view.innerHTML=`<button class="secondary" onclick="go('Caja')">← Caja</button><h2>Cobrar ${d.table.label}</h2>${d.items.map(itemLine).join('')}<hr><div class="total">Total: ${money(d.order.total)}</div><label>Forma de pago</label><select id="payment"><option>Efectivo</option><option>Tarjeta</option><option>Pix</option><option>Transferencia</option><option>Mixto</option></select><button style="width:100%" onclick="pay(${id})">Confirmar cobro y cerrar mesa</button>`}
async function pay(id){if(!confirm('¿Confirmar cobro y cerrar mesa?'))return;await api('/api/pay',{method:'POST',body:JSON.stringify({order_id:id,payment_method:payment.value})});alert('Cobro registrado');go('Caja')}
async function renderKitchen(){let d=await api('/api/kitchen');view.innerHTML=`<div class="row between"><h2>Comandas de cocina</h2><button class="secondary" onclick="renderKitchen()">Actualizar</button></div><div class="grid">${d.items.map(i=>`<div class="box"><b>Mesa ${i.table_id}</b><h3>${i.qty} × ${i.product_name}</h3><p>${i.notes||'Sin observaciones'}</p><div class="small">${i.created_at}</div><button onclick="itemReady(${i.id})">Marcar listo</button></div>`).join('')||'<p class="muted">No hay comandas pendientes.</p>'}</div>`}
async function itemReady(id){await api('/api/kitchen/ready',{method:'POST',body:JSON.stringify({item_id:id})});renderKitchen()}
async function renderProducts(){let d=await api('/api/products');view.innerHTML=`<h2>Administrar menú</h2><div class="box"><div class="row"><div style="flex:2"><label>Producto</label><input id="pname"></div><div style="flex:1"><label>Categoría</label><input id="pcat" placeholder="Bebidas"></div><div style="flex:1"><label>Precio ($)</label><input id="pprice" type="number" min="0"></div></div><button onclick="saveProduct()">Agregar producto</button></div><div class="box" style="margin-top:14px">${d.products.map(p=>`<div class="item"><div><b>${p.name}</b><div class="muted">${p.category}</div></div><div class="row"><b>${money(p.price)}</b><button class="secondary" onclick="editPrice(${p.id},${p.price})">Precio</button><button class="danger" onclick="disableProduct(${p.id})">Quitar</button></div></div>`).join('')}</div>`}
async function saveProduct(){await api('/api/products',{method:'POST',body:JSON.stringify({name:pname.value,category:pcat.value||'General',price:Number(pprice.value)})});renderProducts()}
async function editPrice(id,old){let v=prompt('Nuevo precio',old);if(v===null)return;await api('/api/products/'+id,{method:'PATCH',body:JSON.stringify({price:Number(v)})});renderProducts()}
async function disableProduct(id){if(confirm('¿Quitar del menú?')){await api('/api/products/'+id,{method:'DELETE'});renderProducts()}}
async function renderSales(){let d=await api('/api/sales');view.innerHTML=`<h2>Ventas de hoy</h2><div class="box"><div class="total">${money(d.total)}</div><p>${d.count} cuentas cerradas</p></div><div class="box" style="margin-top:12px">${d.sales.map(s=>`<div class="item"><span>Mesa ${s.table_id} · ${s.payment_method} · ${s.closed_at}</span><b>${money(s.total)}</b></div>`).join('')||'<p class="muted">Sin ventas registradas hoy.</p>'}</div>`}
async function boot(){try{me=await api('/api/me');start()}catch(e){showLogin()}}
if('serviceWorker' in navigator){window.addEventListener('load',()=>navigator.serviceWorker.register('/sw.js').catch(()=>{}));}\nboot();setInterval(()=>{if(me&&activeTab==='Cocina')renderKitchen()},12000);
</script></body></html>'''


@app.get("/manifest.json")
def manifest():
    return jsonify({
        "name": "Sommelier POS",
        "short_name": "Sommelier",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#101010",
        "theme_color": "#101010",
        "description": "Sistema de pedidos y caja de Restaurante Sommelier",
        "icons": []
    })

@app.get("/sw.js")
def service_worker():
    from flask import Response
    return Response(
        "self.addEventListener('install',e=>self.skipWaiting());"
        "self.addEventListener('activate',e=>self.clients.claim());",
        mimetype="application/javascript",
        headers={"Cache-Control": "no-cache"}
    )

@app.route("/")
def home(): return render_template_string(PAGE)
@app.post("/api/login")
def login():
    d=request.get_json() or {}; u=USERS.get(d.get("username"))
    if not u or not secrets.compare_digest(str(d.get("pin","")),str(u["pin"])): return jsonify(error="Usuario o PIN incorrecto."),401
    session.clear(); session.update(user=d["username"],role=u["role"],name=u["name"])
    return jsonify(role=u["role"],name=u["name"])
@app.post("/api/logout")
def logout(): session.clear(); return jsonify(ok=True)
@app.get("/api/me")
def me():
    if not session.get("user"): return jsonify(error="No login"),401
    return jsonify(role=session["role"],name=session["name"])
@app.get("/api/data")
@required()
def data():
    c=db(); p=[dict(x) for x in c.execute("SELECT * FROM products WHERE active=1 ORDER BY category,name")]
    t=[dict(x) for x in c.execute("SELECT t.id,t.label,o.id order_id,COALESCE(o.total,0) total FROM tables_rest t LEFT JOIN orders o ON o.table_id=t.id AND o.status='open' ORDER BY t.id")]
    c.close(); return jsonify(products=p,tables=t)
@app.get("/api/table/<int:tid>")
@required("admin","waiter","cashier")
def table(tid):
    c=db(); t=c.execute("SELECT * FROM tables_rest WHERE id=?",(tid,)).fetchone()
    if not t: c.close(); return jsonify(error="Mesa inexistente"),404
    o=c.execute("SELECT * FROM orders WHERE table_id=? AND status='open'",(tid,)).fetchone()
    if not o and session["role"] in ("admin","waiter"):
        cur=c.execute("INSERT INTO orders(table_id,waiter,created_at) VALUES(?,?,?)",(tid,session["name"],datetime.now().strftime("%d/%m %H:%M")))
        c.commit(); o=c.execute("SELECT * FROM orders WHERE id=?",(cur.lastrowid,)).fetchone()
    items=[dict(x) for x in c.execute("SELECT * FROM order_items WHERE order_id=?",(o["id"],))] if o else []
    c.close(); return jsonify(table=dict(t),order=dict(o) if o else None,items=items)
@app.post("/api/order/add")
@required("admin","waiter")
def add():
    d=request.get_json() or {}; c=db(); o=c.execute("SELECT * FROM orders WHERE table_id=? AND status='open'",(d.get("table_id"),)).fetchone()
    if not o:
        cur=c.execute("INSERT INTO orders(table_id,waiter,created_at) VALUES(?,?,?)",(d["table_id"],session["name"],datetime.now().strftime("%d/%m %H:%M"))); oid=cur.lastrowid
    else: oid=o["id"]
    p=c.execute("SELECT * FROM products WHERE id=? AND active=1",(d.get("product_id"),)).fetchone()
    if not p: c.close(); return jsonify(error="Producto no disponible"),400
    c.execute("INSERT INTO order_items(order_id,product_id,product_name,qty,unit_price,notes,status,created_at) VALUES(?,?,?,?,?,?,?,?)",(oid,p["id"],p["name"],1,p["price"],d.get("notes",""),"pending",datetime.now().strftime("%H:%M")))
    total=c.execute("SELECT COALESCE(SUM(qty*unit_price),0) FROM order_items WHERE order_id=?",(oid,)).fetchone()[0]
    c.execute("UPDATE orders SET total=? WHERE id=?",(total,oid)); c.commit()
    t=c.execute("SELECT * FROM tables_rest WHERE id=?",(d["table_id"],)).fetchone(); items=[dict(x) for x in c.execute("SELECT * FROM order_items WHERE order_id=?",(oid,))]; o=c.execute("SELECT * FROM orders WHERE id=?",(oid,)).fetchone()
    c.close(); return jsonify(table=dict(t),order=dict(o),items=items)
@app.post("/api/order/send")
@required("admin","waiter")
def send():
    d=request.get_json() or {}; c=db()
    c.execute("UPDATE order_items SET status='en cocina' WHERE order_id=(SELECT id FROM orders WHERE table_id=? AND status='open') AND status='pending'",(d.get("table_id"),)); c.commit(); c.close(); return jsonify(ok=True)
@app.get("/api/cash")
@required("admin","cashier")
def cash():
    c=db(); r=[dict(x) for x in c.execute("SELECT * FROM orders WHERE status='open' ORDER BY table_id")]; c.close(); return jsonify(orders=r)
@app.get("/api/order/<int:oid>")
@required("admin","cashier")
def order(oid):
    c=db(); o=c.execute("SELECT * FROM orders WHERE id=? AND status='open'",(oid,)).fetchone()
    if not o: c.close(); return jsonify(error="Pedido no encontrado"),404
    t=c.execute("SELECT * FROM tables_rest WHERE id=?",(o["table_id"],)).fetchone(); i=[dict(x) for x in c.execute("SELECT * FROM order_items WHERE order_id=?",(oid,))]; c.close()
    return jsonify(order=dict(o),table=dict(t),items=i)
@app.post("/api/pay")
@required("admin","cashier")
def pay():
    d=request.get_json() or {}; c=db(); o=c.execute("SELECT * FROM orders WHERE id=? AND status='open'",(d.get("order_id"),)).fetchone()
    if not o: c.close(); return jsonify(error="La cuenta ya fue cerrada o no existe."),400
    c.execute("UPDATE orders SET status='closed',closed_at=?,payment_method=? WHERE id=?",(datetime.now().strftime("%d/%m/%Y %H:%M"),d.get("payment_method","Efectivo"),o["id"])); c.commit(); c.close(); return jsonify(ok=True)
@app.get("/api/kitchen")
@required("admin","kitchen")
def kitchen():
    c=db(); r=[dict(x) for x in c.execute("SELECT i.*,o.table_id FROM order_items i JOIN orders o ON i.order_id=o.id WHERE o.status='open' AND i.status='en cocina' ORDER BY i.id")]; c.close(); return jsonify(items=r)
@app.post("/api/kitchen/ready")
@required("admin","kitchen")
def ready():
    d=request.get_json() or {}; c=db(); c.execute("UPDATE order_items SET status='listo' WHERE id=?",(d.get("item_id"),)); c.commit(); c.close(); return jsonify(ok=True)
@app.get("/api/products")
@required("admin")
def product_list():
    c=db(); p=[dict(x) for x in c.execute("SELECT * FROM products WHERE active=1 ORDER BY category,name")]; c.close(); return jsonify(products=p)
@app.post("/api/products")
@required("admin")
def product_add():
    d=request.get_json() or {}
    try: price=float(d.get("price",-1))
    except: price=-1
    if not d.get("name") or price<0:return jsonify(error="Completá nombre y precio válido."),400
    c=db(); c.execute("INSERT INTO products(name,category,price) VALUES(?,?,?)",(d["name"],d.get("category","General"),price)); c.commit(); c.close(); return jsonify(ok=True)
@app.patch("/api/products/<int:pid>")
@required("admin")
def product_edit(pid):
    d=request.get_json() or {}
    try: price=float(d.get("price",-1))
    except: price=-1
    if price<0:return jsonify(error="Precio inválido"),400
    c=db(); c.execute("UPDATE products SET price=? WHERE id=?",(price,pid)); c.commit(); c.close(); return jsonify(ok=True)
@app.delete("/api/products/<int:pid>")
@required("admin")
def product_delete(pid):
    c=db(); c.execute("UPDATE products SET active=0 WHERE id=?",(pid,)); c.commit(); c.close(); return jsonify(ok=True)
@app.get("/api/sales")
@required("admin","cashier")
def sales():
    today=datetime.now().strftime("%d/%m/%Y"); c=db(); r=[dict(x) for x in c.execute("SELECT * FROM orders WHERE status='closed' AND closed_at LIKE ? ORDER BY id DESC",(today+"%",))]; c.close()
    return jsonify(total=sum(x["total"] for x in r),count=len(r),sales=r)
if __name__=="__main__":
    init_db(); print("Sommelier POS: http://127.0.0.1:5000"); app.run(host="0.0.0.0",port=5000,debug=False)
