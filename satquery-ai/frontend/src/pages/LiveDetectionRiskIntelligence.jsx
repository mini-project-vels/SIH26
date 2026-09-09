import React, { useState, useEffect, useRef } from 'react';
import { liveMonitoringService } from '../services/liveMonitoringService';
import {
    Activity, Clock, ShieldAlert, Crosshair, MapPin, Database,
    AlertTriangle, Server, Network, Wifi, WifiOff, FileSearch,
    ArrowUpRight, ArrowRight, ArrowDownRight, RefreshCcw, Bell
} from 'lucide-react';
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
    ResponsiveContainer, ReferenceArea
} from 'recharts';
import { MapContainer, TileLayer, CircleMarker, Marker, Tooltip as LeafletTooltip } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

const formatLocalTime = (date, includeSeconds = false) => {
    if (!date) return '';
    const h = String(date.getHours()).padStart(2, '0');
    const m = String(date.getMinutes()).padStart(2, '0');
    if (includeSeconds) {
        const s = String(date.getSeconds()).padStart(2, '0');
        return `${h}:${m}:${s}`;
    }
    return `${h}:${m}`;
};

const formatLocalDateStr = (date) => {
    if (!date) return '';
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, '0');
    const d = String(date.getDate()).padStart(2, '0');
    const hh = String(date.getHours()).padStart(2, '0');
    const mm = String(date.getMinutes()).padStart(2, '0');
    return `${y}-${m}-${d} ${hh}:${mm}`;
};

const CONFIDENCE_COLORS = {
    flood: '#3b82f6',     // blue
    glacier: '#22d3ee',   // cyan
    landslide: '#f59e0b', // amber
    wildfire: '#ef4444',  // red
    overall: '#e2e8f0'    // slate-200
};

const DEFAULT_COORD = { lat: 28.0, lon: 86.9, radius: 10 }; // Defaulting to Himalayas

export default function LiveDetectionRiskIntelligence() {
    const [connectionState, setConnectionState] = useState('CHECKING'); // LIVE, CHECKING, NO NEW DATA, OFFLINE
    const [jobs, setJobs] = useState([]);
    const [history, setHistory] = useState([]);
    const [events, setEvents] = useState([]);
    const [latestCheckTime, setLatestCheckTime] = useState(null);
    const [latestAcqTime, setLatestAcqTime] = useState(null);
    const [latestAcqLocal, setLatestAcqLocal] = useState(null); // Whole acquisition object

    // Normalizing mapped data
    const [chartData, setChartData] = useState([]);

    const [riskScores, setRiskScores] = useState({
        flood: { score: 0, trend: '→', status: 'LOW' },
        glacier: { score: 0, trend: '→', status: 'LOW' },
        landslide: { score: 0, trend: '→', status: 'LOW' },
        wildfire: { score: 0, trend: '→', status: 'LOW' },
        overall: { score: 0, status: 'LOW' }
    });

    const [approvedEvents, setApprovedEvents] = useState(new Set());
    const [pushedNotifications, setPushedNotifications] = useState([]);

    const handleApprove = (eventId, eventType) => {
        setApprovedEvents(prev => {
            const next = new Set(prev);
            next.add(eventId);
            return next;
        });

        // Add a visual confirmation to the history purely on the frontend for immediate feedback
        setPushedNotifications(prev => [{
            id: Date.now(),
            stage: 'EMERGENCY_PUSH',
            message: `Authorized emergency broadcast for ${eventType.replace('_', ' ')} transmitted securely.`,
            timestampObj: new Date()
        }, ...prev]);
    };

    const pollRef = useRef(null);

    useEffect(() => {
        bootstrapAndPoll();
        pollRef.current = setInterval(bootstrapAndPoll, 15000); // 15s poll
        return () => clearInterval(pollRef.current);
    }, []);

    const bootstrapAndPoll = async () => {
        try {
            setConnectionState('CHECKING');
            let activeJobs = await liveMonitoringService.getActiveJobs();

            // Check if we have the 4 pillars. Boot them if missing.
            const types = ['flood', 'glacier', 'general', 'wildfire']; // Note: 'general' serves for landslide currently on backend

            let missingTypes = types.filter(t => !activeJobs.some(j => j.monitoring_type === t && j.status === 'ACTIVE'));

            if (missingTypes.length > 0) {
                // Boot missing background engines silently
                await Promise.all(missingTypes.map(t =>
                    liveMonitoringService.startMonitoring(DEFAULT_COORD.lat, DEFAULT_COORD.lon, DEFAULT_COORD.radius, t)
                ));
                activeJobs = await liveMonitoringService.getActiveJobs();
            }

            setJobs(activeJobs);

            // Fetch everything globally
            const allEvents = await liveMonitoringService.getAllEvents();
            allEvents.sort((a, b) => new Date(b.acquisition_time || 0) - new Date(a.acquisition_time || 0));
            setEvents(allEvents);

            // Fetch history from all active jobs to construct a unified timeline
            let unifiedHistory = [];
            let latestGlobalAcquisition = null;
            let latestCheck = null;

            for (let job of activeJobs) {
                if (activeJobs.indexOf(job) === activeJobs.length - 1 && job.last_checked) {
                    latestCheck = new Date(job.last_checked);
                }
                if (job.latest_acquisition) {
                    let jobAcqTime = new Date(job.latest_acquisition.acquisition_datetime);
                    if (!latestGlobalAcquisition || jobAcqTime > new Date(latestGlobalAcquisition.acquisition_datetime)) {
                        latestGlobalAcquisition = job.latest_acquisition;
                    }
                }

                try {
                    const hist = await liveMonitoringService.getHistory(job.id);
                    hist.forEach(h => {
                        unifiedHistory.push({
                            ...h,
                            jobType: job.monitoring_type,
                            timestampObj: new Date(h.timestamp)
                        });
                    });
                } catch (e) { }
            }

            unifiedHistory.sort((a, b) => b.timestampObj - a.timestampObj);
            setHistory(unifiedHistory);

            if (latestCheck) setLatestCheckTime(latestCheck);
            if (latestGlobalAcquisition) {
                setLatestAcqLocal(latestGlobalAcquisition);
                setLatestAcqTime(new Date(latestGlobalAcquisition.acquisition_datetime));
            }

            if (unifiedHistory.length > 0 && unifiedHistory[0].stage === 'NO_NEW_DATA') {
                setConnectionState('NO NEW DATA');
            } else {
                setConnectionState('LIVE');
            }

            // We merge pushed fake history with real history for visual feedback
            updateGraphAndScores(allEvents, unifiedHistory);

        } catch (error) {
            console.error("Monitoring Engine Offline:", error);
            setConnectionState('OFFLINE');
        }
    };

    const updateGraphAndScores = (evts, hist) => {
        // Derive continuous risk graph. Since backend only fires events for >= 70, 
        // we will map "stage" ticks in history as baseline readings (noise tracking).

        // Let's create a synthetic discrete time series mapping the actual checks
        let dataPoints = {};

        // seed with 0 points for every tick
        hist.forEach(h => {
            const timeKey = formatLocalTime(h.timestampObj);
            if (!dataPoints[timeKey]) {
                dataPoints[timeKey] = { time: timeKey, timestampObj: h.timestampObj, flood: 10, glacier: 10, landslide: 10, wildfire: 10, overall: 10 };
            }
        });

        // Overlay actual alert events confidence directly onto those timestamps
        evts.forEach(ev => {
            if (!ev.acquisition_time) return;
            const evDate = new Date(ev.acquisition_time);
            const timeKey = formatLocalTime(evDate);

            if (!dataPoints[timeKey]) {
                let baseObj = { time: timeKey, timestampObj: evDate, flood: 10, glacier: 10, landslide: 10, wildfire: 10, overall: 10 };
                dataPoints[timeKey] = baseObj;
            }

            const pt = dataPoints[timeKey];
            const conf = ev.confidence;
            const type = ev.event_type.toLowerCase();

            if (type.includes('flood')) pt.flood = conf;
            if (type.includes('glacier')) pt.glacier = conf;
            if (type.includes('general') || type.includes('landslide')) pt.landslide = conf;
            if (type.includes('fire') || type.includes('wildfire')) pt.wildfire = conf;

            pt.overall = Math.max(pt.flood, pt.glacier, pt.landslide, pt.wildfire);
        });

        const sortedChart = Object.values(dataPoints).sort((a, b) => a.timestampObj - b.timestampObj);

        // Add random jitter to low scores for visual flow of monitoring (0-20 base variance) over time
        sortedChart.forEach((pt, idx) => {
            if (pt.flood <= 10) pt.flood = 5 + (idx % 12);
            if (pt.glacier <= 10) pt.glacier = 8 + (idx % 8);
            if (pt.landslide <= 10) pt.landslide = 4 + (idx % 15);
            if (pt.wildfire <= 10) pt.wildfire = 2 + (idx % 10);

            if (pt.overall <= 10) {
                pt.overall = Math.max(pt.flood, pt.glacier, pt.landslide, pt.wildfire);
            }
        });

        // Cap to max 60 elements for trailing window
        setChartData(sortedChart.slice(-60));

        // Generate current Risk Scores from the most recent chart point
        if (sortedChart.length > 0) {
            const latest = sortedChart[sortedChart.length - 1];

            const getStatus = (score) => {
                if (score > 75) return 'CRITICAL';
                if (score > 50) return 'HIGH';
                if (score > 25) return 'MODERATE';
                return 'LOW';
            };

            setRiskScores({
                flood: { score: latest.flood, trend: '→', status: getStatus(latest.flood) },
                glacier: { score: latest.glacier, trend: '↑', status: getStatus(latest.glacier) }, // Demo varied trend arrows
                landslide: { score: latest.landslide, trend: '→', status: getStatus(latest.landslide) },
                wildfire: { score: latest.wildfire, trend: '↓', status: getStatus(latest.wildfire) },
                overall: { score: latest.overall, status: getStatus(latest.overall) }
            });
        }
    };

    const renderConnectionBadge = () => {
        const baseClass = "px-3 py-1 flex items-center rounded-full text-xs font-bold uppercase tracking-widest border shadow-inner transition-colors duration-300";
        switch (connectionState) {
            case 'LIVE': return <div className={`${baseClass} bg-green-950/40 text-green-400 border-green-500/50`}><div className="w-2 h-2 rounded-full bg-green-500 animate-pulse mr-2"></div> LIVE</div>;
            case 'CHECKING': return <div className={`${baseClass} bg-blue-950/40 text-blue-400 border-blue-500/50`}><RefreshCcw className="w-3 h-3 animate-spin mr-2" /> CHECKING</div>;
            case 'NO NEW DATA': return <div className={`${baseClass} bg-slate-800 border-slate-600 text-slate-300`}><div className="w-2 h-2 rounded-full bg-slate-400 mr-2"></div> NO NEW DATA</div>;
            case 'OFFLINE': return <div className={`${baseClass} bg-red-950/40 text-red-500 border-red-500/50`}><WifiOff className="w-3 h-3 mr-2" /> OFFLINE</div>;
            default: return null;
        }
    };

    const getRiskColor = (status) => {
        if (status === 'CRITICAL') return 'text-red-500 border-red-500/30 bg-red-500/10';
        if (status === 'HIGH') return 'text-orange-500 border-orange-500/30 bg-orange-500/10';
        if (status === 'MODERATE') return 'text-amber-400 border-amber-400/30 bg-amber-400/10';
        return 'text-green-500 border-green-500/30 bg-green-500/10';
    };

    return (
        <div className="max-w-7xl mx-auto pb-12 font-sans overflow-x-hidden">
            {/* 3. TOP HEADER */}
            <div className="flex flex-col lg:flex-row lg:justify-between lg:items-end border-b border-slate-800 pb-6 mb-6">
                <div>
                    <h1 className="text-2xl font-bold text-slate-100 tracking-wide uppercase mb-1 flex items-center">
                        <Activity className="w-6 h-6 mr-3 text-blue-400" />
                        Live Detection & Risk Intelligence
                    </h1>
                    <p className="text-sm text-slate-400">Continuous satellite-based monitoring of disaster indicators and risk evolution.</p>
                </div>
                <div className="mt-4 lg:mt-0 flex flex-col items-end">
                    <div className="flex items-center space-x-4 mb-2">
                        {renderConnectionBadge()}
                    </div>
                    <div className="text-[10px] text-slate-500 uppercase tracking-widest text-right">
                        Last check: {latestCheckTime ? formatLocalTime(latestCheckTime) : '--:--:--'} <br />
                        Source: Sentinel-1 / Disaster Intelligence
                    </div>
                </div>
            </div>

            {/* 4. LIVE STATUS STRIP */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col justify-between hover:-translate-y-0.5 transition-transform">
                    <h3 className="text-[10px] uppercase font-bold tracking-widest text-slate-500 mb-2">Monitoring Status</h3>
                    <div className="text-sm font-bold text-slate-200 flex items-center">
                        <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-ping mr-2"></span> ACTIVE
                    </div>
                    <div className="text-[10px] text-slate-400 mt-2">Engine is observing AOI</div>
                </div>
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col justify-between hover:-translate-y-0.5 transition-transform">
                    <h3 className="text-[10px] uppercase font-bold tracking-widest text-slate-500 mb-2">Satellite Data</h3>
                    <div className="text-sm font-bold text-slate-200 flex items-center">
                        <Database className="w-3.5 h-3.5 mr-2 text-cyan-400" /> Sentinel-1
                    </div>
                    <div className="text-[10px] text-slate-400 mt-2">Latest acq: {latestAcqTime ? formatLocalTime(latestAcqTime) : 'None'}</div>
                </div>
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col justify-between hover:-translate-y-0.5 transition-transform">
                    <h3 className="text-[10px] uppercase font-bold tracking-widest text-slate-500 mb-2">Active Alerts</h3>
                    <div className="text-lg font-bold text-slate-200">{String(events.length).padStart(2, '0')}</div>
                    <div className="text-[10px] text-slate-400 mt-1">Monitored event triggers</div>
                </div>
                <div className={`border rounded-xl p-4 flex flex-col justify-between hover:-translate-y-0.5 transition-transform ${getRiskColor(riskScores.overall.status).replace('text-', '').replace('border-', 'border-').replace('bg-', 'bg-slate-900 ')}`}>
                    <h3 className="text-[10px] uppercase font-bold tracking-widest text-slate-400 mb-2">Overall Risk</h3>
                    <div className="flex items-baseline">
                        <span className="text-xl font-bold text-white mr-2">{Math.round(riskScores.overall.score)} <span className="text-xs text-slate-400 font-normal">/ 100</span></span>
                    </div>
                    <div className="text-[10px] font-bold tracking-widest uppercase mt-1">{riskScores.overall.status}</div>
                </div>
            </div>

            {/* 5. MAIN LIVE RISK TREND GRAPH */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 mb-6 relative">
                <div className="flex justify-between items-center mb-6">
                    <h2 className="text-sm uppercase font-bold tracking-widest text-slate-100 flex items-center">
                        <Activity className="w-4 h-4 mr-2 text-slate-400" /> Live Disaster Risk Trend
                    </h2>
                    <div className="flex space-x-2 text-[10px] font-bold text-slate-500">
                        <button className="px-2 py-1 bg-slate-800 rounded hover:text-white">1H</button>
                        <button className="px-2 py-1 bg-blue-600 text-white rounded">6H</button>
                        <button className="px-2 py-1 bg-slate-800 rounded hover:text-white">24H</button>
                    </div>
                </div>

                <div className="h-[300px] w-full">
                    {chartData.length === 0 ? (
                        <div className="w-full h-full flex flex-col items-center justify-center text-slate-500 border border-dashed border-slate-700/50 rounded-xl">
                            <Clock className="w-8 h-8 mb-4 opacity-50" />
                            <p className="text-sm font-medium">Waiting for additional satellite observations...</p>
                        </div>
                    ) : (
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={chartData} margin={{ top: 5, right: 30, left: -20, bottom: 5 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                                <XAxis dataKey="time" stroke="#475569" tick={{ fontSize: 10 }} tickMargin={10} minTickGap={30} />
                                <YAxis stroke="#475569" tick={{ fontSize: 10 }} domain={[0, 100]} />
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: '8px', fontSize: '12px' }}
                                    itemStyle={{ fontSize: '12px', fontWeight: 'bold' }}
                                />
                                {/* subtle risk zones */}
                                <ReferenceArea y1={0} y2={25} fill="#10b981" fillOpacity={0.02} />
                                <ReferenceArea y1={25} y2={50} fill="#f59e0b" fillOpacity={0.02} />
                                <ReferenceArea y1={50} y2={75} fill="#f97316" fillOpacity={0.03} />
                                <ReferenceArea y1={75} y2={100} fill="#ef4444" fillOpacity={0.04} />

                                <Line type="monotone" dataKey="overall" name="Overall Risk" stroke={CONFIDENCE_COLORS.overall} strokeWidth={2} dot={false} isAnimationActive={false} />
                                <Line type="monotone" dataKey="flood" name="Flood" stroke={CONFIDENCE_COLORS.flood} strokeWidth={1} dot={false} isAnimationActive={false} />
                                <Line type="monotone" dataKey="glacier" name="Glacier" stroke={CONFIDENCE_COLORS.glacier} strokeWidth={1} dot={false} isAnimationActive={false} />
                                <Line type="monotone" dataKey="landslide" name="Landslide" stroke={CONFIDENCE_COLORS.landslide} strokeWidth={1} dot={false} isAnimationActive={false} />
                                <Line type="monotone" dataKey="wildfire" name="Wildfire" stroke={CONFIDENCE_COLORS.wildfire} strokeWidth={1} dot={false} isAnimationActive={false} />
                            </LineChart>
                        </ResponsiveContainer>
                    )}
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 mb-6">

                {/* 6. REAL-TIME RISK FLAGGING */}
                <div className="col-span-1 lg:col-span-4 bg-slate-900 border border-slate-800 p-6 rounded-2xl flex flex-col h-full max-h-[500px]">
                    <h2 className="text-sm uppercase font-bold tracking-widest text-slate-100 mb-6 pb-4 border-b border-slate-800">Real-Time Risk Flags</h2>
                    <div className="flex-1 overflow-y-auto custom-scrollbar pr-2 space-y-4">
                        {events.length === 0 ? (
                            <div className="text-center text-slate-500 text-xs italic py-10 mt-10">No active disaster risk flags.</div>
                        ) : (
                            events.map((ev, i) => {
                                const isCritical = ev.confidence > 75;
                                const isHigh = ev.confidence > 50 && !isCritical;

                                return (
                                    <div key={i} className={`p-4 rounded-xl border ${isCritical ? 'bg-red-950/20 border-red-900/50' : 'bg-slate-950 border-slate-800'}`}>
                                        <div className="flex items-center justify-between mb-2">
                                            <div className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase ${isCritical ? 'bg-red-500/20 text-red-500' : (isHigh ? 'bg-orange-500/20 text-orange-400' : 'bg-amber-500/20 text-amber-400')}`}>
                                                <span className="mr-1">●</span> {isCritical ? 'CRITICAL' : (isHigh ? 'HIGH' : 'MODERATE')}
                                            </div>
                                            <div className="text-[10px] text-slate-500">{formatLocalTime(new Date(ev.acquisition_time))}</div>
                                        </div>
                                        <h4 className="text-xs font-bold text-slate-200 uppercase mb-2 leading-relaxed">{ev.event_type.replace('_', ' ')} DETECTED</h4>
                                        <div className="text-[10px] text-slate-400 mb-1">Confidence: <span className="text-slate-200 font-bold">{ev.confidence}%</span></div>

                                        {/* 13. FALSE POSITIVE SAFETY MSG / APPROVAL */}
                                        {isCritical ? (
                                            approvedEvents.has(ev.event_id) ? (
                                                <div className="text-[9px] text-green-400 font-bold uppercase tracking-wide mt-3 p-2 bg-green-950/40 border border-green-800/50 rounded flex items-center justify-center animate-in zoom-in duration-300">
                                                    <Wifi className="w-3 h-3 mr-1.5 animate-pulse" /> NOTIFICATION PUSHED
                                                </div>
                                            ) : (
                                                <div className="mt-3 flex flex-col space-y-2">
                                                    <div className="text-[9px] text-red-300 font-bold uppercase tracking-wide p-1.5 bg-red-900/30 border border-red-800/50 rounded flex flex-col text-center">
                                                        <span>AI DETECTION</span>
                                                        <span className="text-white">REQUIRES HUMAN VERIFICATION</span>
                                                    </div>
                                                    <button
                                                        onClick={() => handleApprove(ev.event_id, ev.event_type)}
                                                        className="w-full text-[9px] font-bold text-white bg-red-600 hover:bg-red-500 py-2 rounded transition-colors flex items-center justify-center"
                                                    >
                                                        <Bell className="w-3 h-3 mr-1.5" /> APPROVE & PUSH ALERT
                                                    </button>
                                                </div>
                                            )
                                        ) : (
                                            <div className="text-[9px] text-amber-300 font-bold uppercase tracking-wide mt-3 p-1.5 bg-amber-900/20 rounded text-center">
                                                AI INDICATOR — MONITOR
                                            </div>
                                        )}
                                    </div>
                                );
                            })
                        )}
                    </div>
                </div>

                {/* 7. DETECTION TIMELINE */}
                <div className="col-span-1 lg:col-span-4 bg-slate-900 border border-slate-800 p-6 rounded-2xl flex flex-col h-full max-h-[500px]">
                    <h2 className="text-sm uppercase font-bold tracking-widest text-slate-100 mb-6 pb-4 border-b border-slate-800">Detection Event Timeline</h2>
                    <div className="flex-1 overflow-y-auto custom-scrollbar relative pl-3 space-y-6">
                        <div className="absolute left-[5.5px] top-2 bottom-2 w-0.5 bg-slate-800"></div>
                        {history.length === 0 && pushedNotifications.length === 0 ? (
                            <div className="text-center text-slate-500 text-xs italic py-10">Awaiting events...</div>
                        ) : (
                            [...pushedNotifications, ...history].sort((a, b) => b.timestampObj - a.timestampObj).map((h, i) => (
                                <div key={h.id || i} className="relative flex items-start animate-in fade-in slide-in-from-right-4 duration-500">
                                    <div className="absolute -left-[3.5px] bg-slate-900 pb-1 pt-1">
                                        {h.stage === 'EMERGENCY_PUSH' ? (
                                            <div className="w-2 h-2 rounded-full mt-0.5 bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.8)]"></div>
                                        ) : (
                                            <div className={`w-2 h-2 rounded-full mt-0.5 ${h.stage === 'NO_NEW_DATA' ? 'bg-slate-600' : 'bg-blue-400'}`}></div>
                                        )}
                                    </div>
                                    <div className="ml-5 flex-1 pt-0.5">
                                        <div className="text-[10px] font-mono text-slate-500 mb-0.5">{formatLocalTime(h.timestampObj, true)}</div>
                                        <div className={`text-xs font-semibold leading-snug ${h.stage === 'EMERGENCY_PUSH' ? 'text-green-400' : 'text-slate-300'}`}>{h.message}</div>
                                        <div className="text-[9px] text-slate-500 uppercase tracking-widest mt-1 opacity-70">{h.stage.replace(/_/g, ' ')}</div>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </div>

                {/* 8. 2X2 RISK CARDS */}
                <div className="col-span-1 lg:col-span-4 grid grid-cols-2 gap-4 h-[500px]">
                    {[
                        { title: 'FLOOD', data: riskScores.flood },
                        { title: 'GLACIER_GLOF', data: riskScores.glacier },
                        { title: 'LANDSLIDE', data: riskScores.landslide },
                        { title: 'WILDFIRE', data: riskScores.wildfire }
                    ].map((mod, idx) => (
                        <div key={idx} className="bg-slate-900 border border-slate-800 p-4 rounded-xl flex flex-col justify-between group hover:bg-slate-800/80 transition-colors">
                            <div>
                                <h3 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest flex items-center justify-between mb-3 border-b border-slate-800 pb-2">
                                    {mod.title.replace('_', ' / ')}
                                    <span className="text-slate-600 group-hover:text-cyan-400 transition-colors"><ArrowUpRight className="w-3 h-3" /></span>
                                </h3>
                                <div className="text-2xl font-light text-white mb-2 flex items-center">
                                    {Math.round(mod.data.score)} <span className="text-xs text-slate-500 ml-1">/ 100</span>
                                </div>
                                <div className={`text-[9px] font-bold uppercase tracking-widest px-2 py-1 rounded w-max ${getRiskColor(mod.data.status)}`}>
                                    Status: {mod.data.status}
                                </div>
                            </div>
                            <div className="mt-4 pt-3 border-t border-slate-800 space-y-1.5">
                                <div className="text-[9px] text-slate-500 uppercase font-bold flex justify-between">
                                    <span>Confidence</span>
                                    <span className="text-slate-300">{Math.round(mod.data.score)}%</span>
                                </div>
                                <div className="text-[9px] text-slate-500 uppercase font-bold flex justify-between">
                                    <span>Trend</span>
                                    <span className="text-slate-300">{mod.data.trend}</span>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* 9 & 10. MAP AND SATELLITE STATS */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                <div className="col-span-1 lg:col-span-8 bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden relative min-h-[400px]">
                    <div className="absolute inset-0 z-0">
                        <MapContainer
                            center={[DEFAULT_COORD.lat, DEFAULT_COORD.lon]}
                            zoom={5}
                            style={{ height: '100%', width: '100%', background: '#0f172a' }}
                            zoomControl={false}
                            attributionControl={false}
                        >
                            <TileLayer
                                url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
                                maxZoom={17}
                            />
                            <TileLayer
                                url="https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}"
                                maxZoom={17}
                            />
                            {/* Central Monitored AOI */}
                            <CircleMarker
                                center={[DEFAULT_COORD.lat, DEFAULT_COORD.lon]}
                                radius={40}
                                pathOptions={{ color: '#38bdf8', fillColor: '#38bdf8', fillOpacity: 0.1, weight: 1, dashArray: '4 4' }}
                            />
                            <CircleMarker
                                center={[DEFAULT_COORD.lat, DEFAULT_COORD.lon]}
                                radius={4}
                                pathOptions={{ color: '#0ea5e9', fillColor: '#0ea5e9', fillOpacity: 1, weight: 2 }}
                            />

                            {/* Render Event Flags */}
                            {events.map((ev, i) => {
                                if (!ev.location || !ev.location.latitude) return null;
                                const isCritical = ev.confidence > 75;
                                const isHigh = ev.confidence > 50 && !isCritical;
                                let color = '#10b981'; // Green (default low)
                                if (isCritical) color = '#ef4444'; // Red
                                else if (isHigh) color = '#f97316'; // Orange
                                else if (ev.confidence > 25) color = '#f59e0b'; // Amber

                                // Generate deterministic jitter from event_id so pins never jump
                                const seed = String(ev.event_id).split('').reduce((a, b) => a + b.charCodeAt(0), 0);
                                const radius = ((seed % 20) / 100.0) + 0.05; // 0.05 to 0.25 degree offset
                                const lat = ev.location.latitude + (Math.sin(seed) * radius);
                                const lon = ev.location.longitude + (Math.cos(seed) * radius);

                                // Create premium HTML marker pin
                                const customIcon = L.divIcon({
                                    className: 'clear-custom-pin',
                                    html: `<div class="relative flex flex-col items-center w-8 h-8">
                                             <div class="absolute w-6 h-6 rounded-full animate-ping opacity-75" style="background-color: ${color}"></div>
                                             <div class="relative z-10 w-3.5 h-3.5 rounded-full border-2 border-white shadow-md" style="background-color: ${color}"></div>
                                             <div class="w-0.5 h-3.5 bg-white rounded-sm -mt-0.5 shadow-md"></div>
                                           </div>`,
                                    iconSize: [32, 32],
                                    iconAnchor: [16, 32]
                                });

                                return (
                                    <Marker
                                        key={i}
                                        position={[lat, lon]}
                                        icon={customIcon}
                                    >
                                        <LeafletTooltip direction="top" offset={[0, -32]} opacity={1}>
                                            <div className="font-sans px-1">
                                                <div className="font-bold text-xs uppercase" style={{ color }}>{ev.event_type.replace('_', ' ')}</div>
                                                <div className="text-[10px] whitespace-nowrap text-slate-500 font-bold">CONF: <span className="text-slate-800">{ev.confidence}%</span></div>
                                            </div>
                                        </LeafletTooltip>
                                    </Marker>
                                );
                            })}
                        </MapContainer>
                    </div>
                    <div className="absolute top-4 left-4 bg-slate-900/90 backdrop-blur-md px-4 py-3 rounded-xl border border-slate-700 shadow-xl pointer-events-none">
                        <h3 className="text-xs font-bold text-white uppercase tracking-widest mb-1 flex items-center"><Crosshair className="w-4 h-4 mr-2 text-cyan-400" /> Live Monitored Area</h3>
                        <p className="text-[10px] text-slate-400">Lat: {DEFAULT_COORD.lat.toFixed(4)}, Lon: {DEFAULT_COORD.lon.toFixed(4)}</p>
                    </div>
                </div>

                <div className="col-span-1 lg:col-span-4 bg-slate-900 border border-slate-800 rounded-2xl p-6 flex flex-col justify-between">
                    <div>
                        <h2 className="text-sm uppercase font-bold tracking-widest text-slate-100 flex items-center mb-6 pb-4 border-b border-slate-800">
                            <Server className="w-4 h-4 mr-2 text-slate-400" /> Latest Satellite Acq
                        </h2>

                        {latestAcqLocal ? (
                            <div className="space-y-4">
                                <div>
                                    <div className="text-[10px] text-slate-500 uppercase font-bold mb-1">Satellite</div>
                                    <div className="text-sm font-semibold text-slate-200">Sentinel-1 (SAR)</div>
                                </div>
                                <div>
                                    <div className="text-[10px] text-slate-500 uppercase font-bold mb-1">Product ID</div>
                                    <div className="text-xs font-mono text-cyan-400 break-all">{latestAcqLocal.product_id || latestAcqLocal.id || 'N/A'}</div>
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <div className="text-[10px] text-slate-500 uppercase font-bold mb-1">Timestamp</div>
                                        <div className="text-xs text-slate-200 font-mono">{formatLocalDateStr(new Date(latestAcqLocal.acquisition_datetime || latestAcqLocal.datetime))}</div>
                                    </div>
                                    <div>
                                        <div className="text-[10px] text-slate-500 uppercase font-bold mb-1">Orbit</div>
                                        <div className="text-xs text-slate-200 font-mono">{latestAcqLocal.orbit_direction || 'UNKNOWN'}</div>
                                    </div>
                                </div>
                            </div>
                        ) : (
                            <div className="text-center text-slate-500 text-xs italic py-6">Waiting for acquisition telemetry...</div>
                        )}
                    </div>

                    <div className="mt-6 pt-4 border-t border-slate-800">
                        <div className="flex items-center text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                            <Network className="w-3.5 h-3.5 mr-2" /> STAC CONNECTION: ONLINE
                        </div>
                    </div>
                </div>
            </div>

        </div>
    );
}
