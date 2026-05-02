"""Web UI with dashboard editor, tuning, and live data."""
import json
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

from dash_config import load_config, save_config, AVAILABLE_CHANNELS
from tuning import TUNING_PARAMS


class WebUI:
    def __init__(self, dashboard, reader, logger=None, tuner=None, host="0.0.0.0", port=8080):
        self.dashboard = dashboard
        self.reader = reader
        self.logger = logger
        self.tuner = tuner
        self.host = host
        self.port = port
        handler = _make_handler(dashboard, reader, logger, tuner)
        self._server = HTTPServer((host, port), handler)

    def start(self):
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        print(f"WebUI running at http://0.0.0.0:{self.port}")

    def stop(self):
        if self._server:
            self._server.shutdown()


def _make_handler(dashboard, reader, logger, tuner):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            pass

        def do_GET(self):
            routes = {
                "/": self._page_main,
                "/editor": self._page_editor,
                "/tuning": self._page_tuning,
                "/api/data": self._api_data,
                "/api/status": self._api_status,
                "/api/next-page": lambda: (dashboard.next_page(), self._json({"page": dashboard.current_page})),
                "/api/prev-page": lambda: (setattr(dashboard, "current_page", (dashboard.current_page - 1) % len(dashboard.pages)), self._json({"page": dashboard.current_page})),
                "/api/logs": self._api_logs,
                "/api/config": lambda: self._json(load_config()),
                "/api/channels": lambda: self._json(AVAILABLE_CHANNELS),
                "/api/tuning/params": self._api_tuning_params,
            }
            if self.path in routes:
                routes[self.path]()
            elif self.path.startswith("/api/logs/"):
                self._api_log_file(self.path.split("/api/logs/")[1])
            elif self.path.startswith("/api/tuning/read/"):
                self._api_tuning_read(self.path.split("/api/tuning/read/")[1])
            else:
                self.send_error(404)

        def do_POST(self):
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length) if length else b""

            if self.path == "/api/config":
                try:
                    config = json.loads(body)
                    save_config(config)
                    self._json({"ok": True, "msg": "Saved. Restart dashboard to apply."})
                except Exception as e:
                    self._json({"ok": False, "msg": str(e)})

            elif self.path == "/api/tuning/write":
                try:
                    data = json.loads(body)
                    if tuner:
                        ok, msg = tuner.write_param(data["id"], data["value"])
                        self._json({"ok": ok, "msg": msg})
                    else:
                        self._json({"ok": False, "msg": "No ECU connected"})
                except Exception as e:
                    self._json({"ok": False, "msg": str(e)})

            elif self.path == "/api/tuning/burn":
                if tuner:
                    tuner.burn_to_flash()
                    self._json({"ok": True, "msg": "Burned to flash"})
                else:
                    self._json({"ok": False, "msg": "No ECU connected"})
            else:
                self.send_error(404)

        def _json(self, data):
            body = json.dumps(data).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)

        def _html(self, content):
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(content.encode())

        def _api_data(self):
            self._json(reader.get_data())

        def _api_status(self):
            self._json({
                "connected": getattr(reader, "connected", False),
                "connection_type": getattr(reader, "connection_type", None),
                "page": dashboard.current_page,
                "page_name": dashboard.pages[dashboard.current_page].name,
                "total_pages": len(dashboard.pages),
                "logging": logger.current_file if logger else None,
            })

        def _api_logs(self):
            self._json({"logs": logger.list_logs() if logger else []})

        def _api_log_file(self, filename):
            if not logger or ".." in filename:
                self.send_error(404)
                return
            filepath = os.path.join(logger.log_dir, filename)
            if not os.path.exists(filepath):
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/csv")
            self.send_header("Content-Disposition", f"attachment; filename={filename}")
            self.end_headers()
            with open(filepath, "rb") as f:
                self.wfile.write(f.read())

        def _api_tuning_params(self):
            if tuner:
                self._json(tuner.get_all_params())
            else:
                self._json(TUNING_PARAMS)

        def _api_tuning_read(self, param_id):
            if tuner:
                val = tuner.read_param(param_id)
                self._json({"id": param_id, "value": val})
            else:
                self._json({"id": param_id, "value": None, "error": "No ECU"})

        def _page_main(self):
            self._html(HTML_MAIN)

        def _page_editor(self):
            self._html(HTML_EDITOR)

        def _page_tuning(self):
            self._html(HTML_TUNING)

    return Handler


CSS = """
* { margin:0; padding:0; box-sizing:border-box; }
body { background:#0a0a0e; color:#28ff14; font-family:-apple-system,monospace; padding:12px; font-size:13px; }
h1 { font-size:16px; margin-bottom:8px; }
h2 { font-size:14px; margin:12px 0 6px; color:#28ff14; }
a { color:#28ff14; }
.nav { display:flex; gap:8px; margin-bottom:12px; }
.nav a { padding:8px 14px; border:1px solid #1a1a24; border-radius:4px; text-decoration:none; font-size:12px; }
.nav a.active, .nav a:active { background:#28ff14; color:#000; }
.status { padding:6px 10px; border-radius:4px; margin-bottom:10px; font-size:12px; }
.connected { background:#0a1a0a; border:1px solid #28ff14; }
.disconnected { background:#1a0a0a; border:1px solid #f00; color:#f00; }
.grid { display:grid; grid-template-columns:1fr 1fr; gap:6px; margin-bottom:10px; }
.gauge { background:#12121a; border:1px solid #1a1a24; border-radius:4px; padding:8px; }
.gauge .label { font-size:10px; color:#666; }
.gauge .value { font-size:20px; font-weight:bold; margin:2px 0; }
.gauge .unit { font-size:9px; color:#444; }
.warn { color:#ff0; }
.crit { color:#f00; }
.buttons { display:flex; gap:6px; margin-bottom:10px; }
button, .btn { padding:10px; font-size:13px; font-weight:bold; border:1px solid #28ff14;
  background:#0a1a0a; color:#28ff14; border-radius:4px; cursor:pointer; text-align:center; }
button:active, .btn:active { background:#28ff14; color:#000; }
.btn-danger { border-color:#f00; color:#f00; }
.btn-danger:active { background:#f00; color:#000; }
input, select { background:#12121a; color:#28ff14; border:1px solid #1a1a24; padding:6px; border-radius:4px; font-size:12px; width:100%; }
.form-row { display:flex; gap:6px; align-items:center; margin-bottom:6px; }
.form-row label { min-width:80px; font-size:11px; color:#666; }
.form-row input, .form-row select { flex:1; }
.card { background:#12121a; border:1px solid #1a1a24; border-radius:6px; padding:10px; margin-bottom:8px; }
.card h3 { font-size:12px; color:#28ff14; margin-bottom:6px; }
.desc { font-size:10px; color:#555; margin-bottom:4px; }
.msg { padding:6px; border-radius:4px; margin:6px 0; font-size:11px; }
.msg-ok { background:#0a1a0a; border:1px solid #28ff14; }
.msg-err { background:#1a0a0a; border:1px solid #f00; color:#f00; }
"""

HTML_MAIN = f"""<!DOCTYPE html><html><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>OpenDash</title><style>{CSS}</style></head><body>
<h1>OpenDash</h1>
<div class="nav"><a href="/" class="active">Live</a><a href="/editor">Editor</a><a href="/tuning">Tuning</a></div>
<div id="status" class="status disconnected">Connecting...</div>
<div class="buttons">
  <button onclick="api('prev-page')" style="flex:1">&#9664; Prev</button>
  <button onclick="api('next-page')" style="flex:1">Next &#9654;</button>
</div>
<div class="grid" id="gauges"></div>
<script>
const gauges=[
  {{key:'rpm',label:'RPM',unit:'',warnHigh:6000}},
  {{key:'boost',label:'Boost',unit:'kPa',warnHigh:150}},
  {{key:'afr',label:'AFR',unit:'',warnLow:13,warnHigh:16,fmt:1}},
  {{key:'clt',label:'Coolant',unit:'°C',warnHigh:93}},
  {{key:'oilpressure',label:'Oil P',unit:'psi',warnLow:25}},
  {{key:'batteryv',label:'Battery',unit:'V',warnLow:12,fmt:1}},
  {{key:'tps',label:'TPS',unit:'%'}},
  {{key:'map',label:'MAP',unit:'kPa'}},
  {{key:'advance',label:'ADV',unit:'°'}},
  {{key:'iat',label:'IAT',unit:'°C',warnHigh:50}},
  {{key:'pw1',label:'PW',unit:'ms',fmt:1}},
  {{key:'ve',label:'VE',unit:'%'}},
];
const el=id=>document.getElementById(id);
function init(){{let h='';gauges.forEach(g=>{{h+=`<div class="gauge" id="g-${{g.key}}"><div class="label">${{g.label}}</div><div class="value">--</div><div class="unit">${{g.unit}}</div></div>`;}}); el('gauges').innerHTML=h;}}
function update(data){{gauges.forEach(g=>{{const v=data[g.key];if(v===undefined)return;const d=el('g-'+g.key);if(!d)return;const val=d.querySelector('.value');val.textContent=g.fmt?v.toFixed(g.fmt):Math.round(v);val.className='value';if(g.warnHigh&&v>=g.warnHigh)val.classList.add('crit');else if(g.warnLow&&v<=g.warnLow)val.classList.add('crit');}});}}
function api(ep){{fetch('/api/'+ep).then(r=>r.json());}}
function poll(){{
  fetch('/api/data').then(r=>r.json()).then(update).catch(()=>{{}});
  fetch('/api/status').then(r=>r.json()).then(st=>{{const s=el('status');if(st.connected){{s.textContent='Connected via '+(st.connection_type||'').toUpperCase()+' | Page '+(st.page+1)+'/'+st.total_pages;s.className='status connected';}}else{{s.textContent='Searching for ECU...';s.className='status disconnected';}}}}).catch(()=>{{}});
}}
init();setInterval(poll,500);poll();
</script></body></html>"""

HTML_EDITOR = f"""<!DOCTYPE html><html><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>OpenDash Editor</title><style>{CSS}</style></head><body>
<h1>Dashboard Editor</h1>
<div class="nav"><a href="/">Live</a><a href="/editor" class="active">Editor</a><a href="/tuning">Tuning</a></div>
<div id="msg"></div>
<div id="pages"></div>
<div class="buttons" style="margin-top:10px">
  <button onclick="addPage()" style="flex:1">+ Add Page</button>
  <button onclick="saveConfig()" style="flex:1;background:#0a1a0a;border-color:#28ff14">Save</button>
</div>
<script>
let config={{}};
let channels=[];
async function init(){{
  config=await(await fetch('/api/config')).json();
  channels=await(await fetch('/api/channels')).json();
  render();
}}
function render(){{
  let h='';
  config.pages.forEach((p,pi)=>{{
    h+=`<div class="card"><h3>Page ${{pi+1}}: ${{p.name}} <button onclick="removePage(${{pi}})" class="btn-danger" style="float:right;padding:2px 8px;font-size:10px">Delete</button></h3>`;
    h+=`<div class="form-row"><label>Name</label><input value="${{p.name}}" onchange="config.pages[${{pi}}].name=this.value"></div>`;
    h+=`<div class="form-row"><label>RPM Bar</label><select onchange="config.pages[${{pi}}].rpm_bar=this.value==='true'"><option value="true" ${{p.rpm_bar?'selected':''}}>Yes</option><option value="false" ${{!p.rpm_bar?'selected':''}}>No</option></select></div>`;
    h+=`<div class="form-row"><label>Gear</label><select onchange="config.pages[${{pi}}].gear=this.value==='true'"><option value="true" ${{p.gear?'selected':''}}>Yes</option><option value="false" ${{!p.gear?'selected':''}}>No</option></select></div>`;
    h+=`<h3 style="margin-top:8px">Gauges</h3>`;
    (p.gauges||[]).forEach((g,gi)=>{{
      h+=`<div class="card" style="margin-left:8px">`;
      h+=`<div class="form-row"><label>Channel</label><select onchange="config.pages[${{pi}}].gauges[${{gi}}].key=this.value">${{channels.map(c=>`<option value="${{c.key}}" ${{c.key===g.key?'selected':''}}>${{c.label}}</option>`).join('')}}</select><button onclick="removeGauge(${{pi}},${{gi}})" class="btn-danger" style="padding:2px 8px;font-size:10px">X</button></div>`;
      h+=`<div class="form-row"><label>Label</label><input value="${{g.label||''}}" onchange="config.pages[${{pi}}].gauges[${{gi}}].label=this.value" style="width:60px"><label>Min</label><input type="number" value="${{g.min||0}}" onchange="config.pages[${{pi}}].gauges[${{gi}}].min=+this.value" style="width:50px"><label>Max</label><input type="number" value="${{g.max||100}}" onchange="config.pages[${{pi}}].gauges[${{gi}}].max=+this.value" style="width:50px"></div>`;
      h+=`<div class="form-row"><label>Warn Low</label><input type="number" value="${{g.warn_low||''}}" onchange="config.pages[${{pi}}].gauges[${{gi}}].warn_low=+this.value||undefined" style="width:50px"><label>Warn High</label><input type="number" value="${{g.warn_high||''}}" onchange="config.pages[${{pi}}].gauges[${{gi}}].warn_high=+this.value||undefined" style="width:50px"></div>`;
      h+=`</div>`;
    }});
    h+=`<button onclick="addGauge(${{pi}})" style="margin-top:4px;padding:4px 10px;font-size:11px">+ Add Gauge</button>`;
    h+=`</div>`;
  }});
  document.getElementById('pages').innerHTML=h;
}}
function addPage(){{config.pages.push({{name:'NEW',rpm_bar:false,gauges:[],gear:false,ve_gauge:false,bottom_bars:[]}});render();}}
function removePage(i){{if(config.pages.length>1){{config.pages.splice(i,1);render();}}}}
function addGauge(pi){{config.pages[pi].gauges.push({{key:'rpm',label:'RPM',unit:'rpm',min:0,max:8000}});render();}}
function removeGauge(pi,gi){{config.pages[pi].gauges.splice(gi,1);render();}}
async function saveConfig(){{
  const r=await fetch('/api/config',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(config)}});
  const d=await r.json();
  document.getElementById('msg').innerHTML=`<div class="msg ${{d.ok?'msg-ok':'msg-err'}}">${{d.msg}}</div>`;
  setTimeout(()=>document.getElementById('msg').innerHTML='',3000);
}}
init();
</script></body></html>"""

HTML_TUNING = f"""<!DOCTYPE html><html><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>OpenDash Tuning</title><style>{CSS}
.param-val {{ font-size:18px; font-weight:bold; margin:4px 0; }}
.slider {{ -webkit-appearance:none; width:100%; height:6px; background:#1a1a24; border-radius:3px; outline:none; }}
.slider::-webkit-slider-thumb {{ -webkit-appearance:none; width:20px; height:20px; background:#28ff14; border-radius:50%; cursor:pointer; }}
</style></head><body>
<h1>ECU Tuning</h1>
<div class="nav"><a href="/">Live</a><a href="/editor">Editor</a><a href="/tuning" class="active">Tuning</a></div>
<div id="status" class="status disconnected">Checking ECU...</div>
<div class="msg msg-err" style="margin-bottom:8px">&#9888; Writing incorrect values can damage your engine. Use with caution.</div>
<div id="msg"></div>
<div id="params"></div>
<div class="buttons" style="margin-top:12px">
  <button onclick="burnFlash()" class="btn-danger" style="flex:1">Burn to Flash</button>
</div>
<script>
let params=[];
async function init(){{
  const st=await(await fetch('/api/status')).json();
  const s=document.getElementById('status');
  if(st.connected){{s.textContent='ECU Connected via '+(st.connection_type||'').toUpperCase();s.className='status connected';}}
  else{{s.textContent='No ECU connected — values cannot be read/written';s.className='status disconnected';}}
  params=await(await fetch('/api/tuning/params')).json();
  render();
}}
function render(){{
  let h='';
  params.forEach(p=>{{
    h+=`<div class="card">`;
    h+=`<h3>${{p.name}} <span style="color:#444;font-weight:normal">${{p.unit}}</span></h3>`;
    h+=`<div class="desc">${{p.description}}</div>`;
    h+=`<div class="param-val" id="val-${{p.id}}">${{p.value!==null&&p.value!==undefined?p.value:'--'}}</div>`;
    h+=`<input type="range" class="slider" min="${{p.min}}" max="${{p.max}}" step="${{p.step}}" value="${{p.value||p.min}}" id="sl-${{p.id}}" oninput="document.getElementById('val-${{p.id}}').textContent=this.value">`;
    h+=`<div class="form-row" style="margin-top:6px"><span style="font-size:10px;color:#444">${{p.min}}</span><span style="flex:1"></span><span style="font-size:10px;color:#444">${{p.max}}</span></div>`;
    h+=`<button onclick="writeParam('${{p.id}}')" style="margin-top:4px;padding:4px 10px;font-size:11px;width:100%">Write to ECU</button>`;
    h+=`</div>`;
  }});
  document.getElementById('params').innerHTML=h;
}}
async function writeParam(id){{
  const val=+document.getElementById('sl-'+id).value;
  if(!confirm('Write '+id+' = '+val+'?'))return;
  const r=await fetch('/api/tuning/write',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{id,value:val}})}});
  const d=await r.json();
  showMsg(d.msg,d.ok);
}}
async function burnFlash(){{
  if(!confirm('Burn all changes to ECU flash? This is permanent.'))return;
  const r=await fetch('/api/tuning/burn',{{method:'POST'}});
  const d=await r.json();
  showMsg(d.msg,d.ok);
}}
function showMsg(msg,ok){{
  document.getElementById('msg').innerHTML=`<div class="msg ${{ok?'msg-ok':'msg-err'}}">${{msg}}</div>`;
  setTimeout(()=>document.getElementById('msg').innerHTML='',3000);
}}
init();
</script></body></html>"""
