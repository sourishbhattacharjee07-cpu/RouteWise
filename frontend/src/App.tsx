import { useEffect, useMemo, useState } from 'react';
import { ArrowRight, Clock3, Wallet, Footprints, RefreshCw, Route as RouteIcon, TrainFront, Bus, Footprints as WalkIcon, AlertTriangle, CheckCircle2, MapPin, Zap } from 'lucide-react';

const API = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
type Stop = {id:string; name:string; lat:number; lon:number};
type Leg = {edge_id:string; from_name:string; to_name:string; mode:string; depart_time:string; arrival_time:string; minutes:number; fare:number; walking_m:number; wait_minutes:number};
type Route = {id:string; rank:number; arrival_time:string; duration_minutes:number; fare:number; walking_m:number; transfers:number; stops:string[]; legs:Leg[]; explanation:string; recommendation:string};
type Disruption = {edge_id:string; kind:string; delay_minutes?:number; label:string};
const money = (n:number) => `₹${Math.round(n)}`;
const duration = (n:number) => `${Math.floor(n/60)}h ${n%60}m`;
function ModeIcon({mode}:{mode:string}) { if(mode==='Metro') return <TrainFront size={16}/>; if(mode==='Bus') return <Bus size={16}/>; return <WalkIcon size={16}/>; }

export default function App() {
  const [stops,setStops] = useState<Stop[]>([]);
  const [origin,setOrigin] = useState('central');
  const [destination,setDestination] = useState('techpark');
  const [departure,setDeparture] = useState('09:00');
  const [deadline,setDeadline] = useState('11:00');
  const [budget,setBudget] = useState(100);
  const [walking,setWalking] = useState(1500);
  const [preference,setPreference] = useState('balanced');
  const [disruptions,setDisruptions] = useState<Disruption[]>([]);
  const [routes,setRoutes] = useState<Route[]>([]);
  const [message,setMessage] = useState('');
  const [loading,setLoading] = useState(false);
  const [error,setError] = useState('');
  const [selected,setSelected] = useState(0);

  useEffect(() => { fetch(`${API}/api/stops`).then(r=>r.json()).then(d=>setStops(d.stops)).catch(()=>setError('Cannot connect to backend. Start the FastAPI server on port 8000.')); }, []);
  const stopName = (id:string) => stops.find(s=>s.id===id)?.name || id;
  const payload = useMemo(()=>({origin,destination,departure_time:departure,arrival_deadline:deadline||null,budget,max_walking_m:walking,preference,disruptions}),[origin,destination,departure,deadline,budget,walking,preference,disruptions]);

  async function plan() {
    setLoading(true); setError('');
    try {
      const response = await fetch(`${API}/api/plan`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
      if(!response.ok) throw new Error(`API returned ${response.status}`);
      const data = await response.json();
      setRoutes(data.routes || []); setMessage(data.message || ''); setSelected(0);
    } catch(e) { setError('Could not reach RouteWise API. Ensure the backend is running at '+API+'.'); }
    finally { setLoading(false); }
  }
  function simulate() {
    const next:Disruption = {edge_id:'e7',kind:'cancel',label:'University → Tech Park bus cancelled (simulated)'};
    setDisruptions(old => old.some(d=>d.edge_id===next.edge_id) ? old : [...old,next]);
    setMessage('Simulated disruption added. Click “Find routes” to recalculate.');
  }
  function clearDisruptions() { setDisruptions([]); setMessage('Disruptions cleared. Find routes again to restore normal service.'); }
  useEffect(()=>{ if(stops.length) plan(); /* initial demo results */ },[stops.length]); // eslint-disable-line react-hooks/exhaustive-deps
  const active = routes[selected];

  return <div className="app-shell">
    <header className="topbar"><a className="brand" href="#"><span className="brand-mark"><RouteIcon size={22}/></span><span>RouteWise<small>JOURNEY RECOVERY</small></span></a><span className="demo-pill"><span/> SIMULATED DATA</span></header>
    <main className="layout">
      <section className="intro"><div className="eyebrow"><Zap size={14}/> DISRUPTION-AWARE TRAVEL</div><h1>Your journey,<br/><em>back on track.</em></h1><p>When plans change, find a smarter way forward. Compare alternative routes by time, fare and walking distance.</p><div className="trust-note"><AlertTriangle size={15}/> Student prototype using fictional transport data — not live service information.</div></section>
      <section className="planner panel">
        <div className="section-heading"><div><span className="step">01</span><h2>Plan your journey</h2></div><span className="muted">Set your limits</span></div>
        <div className="form-grid">
          <label>FROM <span className="select-wrap"><MapPin size={16}/><select value={origin} onChange={e=>setOrigin(e.target.value)}>{stops.map(s=><option key={s.id} value={s.id}>{s.name}</option>)}</select></span></label>
          <label>TO <span className="select-wrap"><MapPin size={16}/><select value={destination} onChange={e=>setDestination(e.target.value)}>{stops.map(s=><option key={s.id} value={s.id}>{s.name}</option>)}</select></span></label>
          <label>DEPARTURE <input type="time" value={departure} onChange={e=>setDeparture(e.target.value)}/></label>
          <label>ARRIVE BY <input type="time" value={deadline} onChange={e=>setDeadline(e.target.value)}/></label>
          <label><span className="label-icon"><Wallet size={15}/> MAX BUDGET</span><div className="range-row"><input type="range" min="10" max="200" step="5" value={budget} onChange={e=>setBudget(Number(e.target.value))}/><strong>{money(budget)}</strong></div></label>
          <label><span className="label-icon"><Footprints size={15}/> WALKING LIMIT</span><div className="range-row"><input type="range" min="0" max="5000" step="250" value={walking} onChange={e=>setWalking(Number(e.target.value))}/><strong>{walking} m</strong></div></label>
        </div>
        <div className="preference"><span>OPTIMISE FOR</span>{[['balanced','Balanced'],['fastest','Fastest'],['cheapest','Cheapest']].map(([v,t])=><button key={v} className={preference===v?'choice active':'choice'} onClick={()=>setPreference(v)}>{t}</button>)}</div>
        <div className="actions"><button className="primary" onClick={plan} disabled={loading}>{loading?'Finding routes…':'Find routes'} <ArrowRight size={17}/></button><button className="secondary" onClick={simulate}><AlertTriangle size={16}/> Simulate disruption</button>{disruptions.length>0&&<button className="text-btn" onClick={clearDisruptions}>Reset</button>}</div>
        {disruptions.length>0&&<div className="disruption-banner"><AlertTriangle size={16}/><span><b>Disruption active:</b> {disruptions.map(d=>d.label).join(', ')}</span></div>}
        {error&&<div className="error">{error}</div>}
      </section>
      <section className="results">
        <div className="section-heading results-heading"><div><span className="step">02</span><h2>Route options</h2></div><span className="muted">{routes.length} option{routes.length===1?'':'s'} found</span></div>
        {message&&<div className="message">{message}</div>}
        {routes.length===0&&!loading?<div className="empty panel"><RouteIcon size={30}/><h3>No feasible route found</h3><p>Try increasing your budget or walking limit, or move your arrival deadline later.</p></div>:<div className="route-layout">
          <div className="route-list">{routes.map((r,i)=><button className={`route-card ${selected===i?'selected':''}`} key={r.id} onClick={()=>setSelected(i)}>
            <div className="route-card-top"><span className={i===0?'recommend':'rank'}>{i===0?'BEST MATCH':`OPTION 0${i+1}`}</span><span className="route-fare">{money(r.fare)}</span></div>
            <div className="route-times"><strong>{r.legs[0]?.depart_time||departure}</strong><span className="time-line"/><strong>{r.arrival_time}</strong></div>
            <div className="route-meta"><span><Clock3 size={14}/>{duration(r.duration_minutes)}</span><span><RefreshCw size={14}/>{r.transfers} changes</span><span><Footprints size={14}/>{r.walking_m} m</span></div>
            <div className="route-stops">{r.stops.join('  →  ')}</div>
          </button>)}</div>
          {active&&<div className="detail panel"><div className="detail-head"><div><span className="eyebrow">YOUR ROUTE</span><h3>{stopName(origin)} <ArrowRight size={17}/> {stopName(destination)}</h3></div><CheckCircle2 size={23}/></div><p className="explanation">{active.explanation}</p><div className="timeline">{active.legs.map((leg,i)=><div className="leg" key={`${leg.edge_id}-${i}`}><div className="timeline-icon"><ModeIcon mode={leg.mode}/></div><div className="leg-content"><div className="leg-top"><b>{leg.mode}</b><span>{leg.minutes} min</span></div><strong>{leg.from_name} <ArrowRight size={13}/> {leg.to_name}</strong><small>{leg.depart_time} – {leg.arrival_time}{leg.wait_minutes>0?` · ${leg.wait_minutes} min wait`:''}</small></div><span className="leg-fare">{money(leg.fare)}</span></div>)}</div><div className="detail-footer"><span>Total estimated fare</span><b>{money(active.fare)}</b></div></div>}
        </div>}
      </section>
      <footer><span>ROUTEWISE · STUDENT PROJECT PROTOTYPE</span><span>Simulated timetable • No live transit feed connected</span></footer>
    </main>
  </div>;
}
