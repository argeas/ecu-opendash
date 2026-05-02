"""Lightweight web config panel for OpenDash. Access from phone at http://opendash.local:8080"""
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler


class WebUI:
    def __init__(self, dashboard, reader, logger=None, host="0.0.0.0", port=8080):
        self.dashboard = dashboard
        self.reader = reader
        self.logger = logger
        self.host = host
        self.port = port
        self._server = None
        self._thread = None

        handler = _make_handler(dashboard, reader, logger)
        self._server = HTTPServer((host, port), handler)

    def start(self):
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        print(f"WebUI running at http://0.0.0.0:{self.port}")

    def stop(self):
        if self._server:
            self._server.shutdown()


def _make_handler(dashboard, reader, logger):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            pass

        def do_GET(self):
            if self.path == "/":
                self._serve_html()
            elif self.path == "/api/data":
                self._serve_data()
            elif self.path == "/api/status":
                self._serve_status()
            elif self.path == "/api/next-page":
                dashboard.next_page()
                self._json_response({"page": dashboard.current_page})
            elif self.path == "/api/prev-page":
                dashboard.current_page = (dashboard.current_page - 1) % len(dashboard.pages)
                self._json_response({"page": dashboard.current_page})
            elif self.path == "/api/logs":
                self._serve_logs()
            elif self.path.startswith("/api/logs/"):
                self._serve_log_file(self.path.split("/api/logs/")[1])
            else:
                self.send_error(404)

        def _json_response(self, data):
            body = json.dumps(data).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)

        def _serve_data(self):
            self._json_response(reader.get_data())

        def _serve_status(self):
            self._json_response({
                "connected": getattr(reader, "connected", False),
                "connection_type": getattr(reader, "connection_type", None),
                "page": dashboard.current_page,
                "page_name": dashboard.pages[dashboard.current_page].name,
                "total_pages": len(dashboard.pages),
                "logging": logger.current_file if logger else None,
            })

        def _serve_logs(self):
            if logger:
                self._json_response({"logs": logger.list_logs()})
            else:
                self._json_response({"logs": []})

        def _serve_log_file(self, filename):
            import os
            if not logger:
                self.send_error(404)
                return
            filepath = os.path.join(logger.log_dir, filename)
            if not os.path.exists(filepath) or ".." in filename:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/csv")
            self.send_header("Content-Disposition", f"attachment; filename={filename}")
            self.end_headers()
            with open(filepath, "rb") as f:
                self.wfile.write(f.read())

        def _serve_html(self):
            html = """<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>OpenDash</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { background: #0a0a0e; color: #28ff14; font-family: -apple-system, monospace; padding: 16px; }
h1 { font-size: 18px; margin-bottom: 12px; }
.status { padding: 8px 12px; border-radius: 6px; margin-bottom: 16px; font-size: 13px; }
.connected { background: #0a1a0a; border: 1px solid #28ff14; }
.disconnected { background: #1a0a0a; border: 1px solid #ff0000; color: #ff0000; }
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 16px; }
.gauge { background: #12121a; border: 1px solid #1a1a24; border-radius: 6px; padding: 10px; }
.gauge .label { font-size: 10px; color: #666; text-transform: uppercase; }
.gauge .value { font-size: 22px; font-weight: bold; margin: 2px 0; }
.gauge .unit { font-size: 10px; color: #444; }
.warn { color: #ffff00; }
.crit { color: #ff0000; }
.buttons { display: flex; gap: 8px; margin-bottom: 16px; }
button { flex: 1; padding: 14px; font-size: 15px; font-weight: bold; border: 1px solid #28ff14;
  background: #0a1a0a; color: #28ff14; border-radius: 6px; cursor: pointer; }
button:active { background: #28ff14; color: #000; }
.section { font-size: 12px; color: #444; margin: 12px 0 6px; text-transform: uppercase; }
</style>
</head><body>
<h1>OpenDash</h1>
<div id="status" class="status disconnected">Connecting...</div>
<div class="buttons">
  <button onclick="api('prev-page')">&#9664; Prev</button>
  <button onclick="api('next-page')">Next &#9654;</button>
</div>
<div class="section">Live Data</div>
<div class="grid" id="gauges"></div>
<script>
const gauges = [
  {key:'rpm', label:'RPM', unit:'', max:8000, warnHigh:6000},
  {key:'boost', label:'Boost', unit:'kPa', max:200, warnHigh:150},
  {key:'afr', label:'AFR', unit:'', warnLow:13, warnHigh:16, fmt:1},
  {key:'clt', label:'Coolant', unit:'°C', warnHigh:93, critHigh:104},
  {key:'oilpressure', label:'Oil P', unit:'psi', warnLow:25},
  {key:'batteryv', label:'Battery', unit:'V', warnLow:12, fmt:1},
  {key:'tps', label:'TPS', unit:'%'},
  {key:'map', label:'MAP', unit:'kPa'},
  {key:'advance', label:'Advance', unit:'°'},
  {key:'iat', label:'IAT', unit:'°C', warnHigh:50},
  {key:'pw1', label:'PW', unit:'ms', fmt:1},
  {key:'ve', label:'VE', unit:'%'},
];
const el = id => document.getElementById(id);
function init() {
  let h = '';
  gauges.forEach(g => {
    h += `<div class="gauge" id="g-${g.key}"><div class="label">${g.label}</div><div class="value">--</div><div class="unit">${g.unit}</div></div>`;
  });
  el('gauges').innerHTML = h;
}
function update(data) {
  gauges.forEach(g => {
    const v = data[g.key];
    if (v === undefined) return;
    const d = el('g-'+g.key);
    if (!d) return;
    const val = d.querySelector('.value');
    val.textContent = g.fmt ? v.toFixed(g.fmt) : Math.round(v);
    val.className = 'value';
    if (g.critHigh && v >= g.critHigh) val.classList.add('crit');
    else if (g.warnHigh && v >= g.warnHigh) val.classList.add('warn');
    else if (g.warnLow && v <= g.warnLow) val.classList.add('crit');
  });
}
function api(endpoint) {
  fetch('/api/'+endpoint).then(r=>r.json()).then(d=>{
    if(d.page !== undefined) el('status').textContent = 'Page '+(d.page+1);
  });
}
function poll() {
  fetch('/api/data').then(r=>r.json()).then(data=>{
    update(data);
  }).catch(()=>{});
  fetch('/api/status').then(r=>r.json()).then(st=>{
    const s = el('status');
    if(st.connected) {
      const t = st.connection_type ? st.connection_type.toUpperCase() : '';
      s.textContent='Connected via '+t+' | Page '+(st.page+1)+'/'+st.total_pages;
      s.className='status connected';
    } else {
      s.textContent='Searching for ECU...';
      s.className='status disconnected';
    }
  }).catch(()=>{
    el('status').textContent='Dashboard offline';
    el('status').className='status disconnected';
  });
}
init();
setInterval(poll, 500);
poll();
</script>
</body></html>"""
            body = html.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(body)

    return Handler
