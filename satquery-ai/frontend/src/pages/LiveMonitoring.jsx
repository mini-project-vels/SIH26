import React, { useState, useEffect } from 'react';
import { Activity, Clock, ShieldAlert, Crosshair, MapPin, Database, Target, AlertTriangle, RefreshCcw } from 'lucide-react';
import api from '../services/api';

export default function LiveMonitoring() {
    const [latitude, setLatitude] = useState(28.0);
    const [longitude, setLongitude] = useState(86.9);
    const [radius, setRadius] = useState(10);
    const [type, setType] = useState('flood');
    const [jobId, setJobId] = useState(null);
    const [jobData, setJobData] = useState(null);
    const [history, setHistory] = useState([]);
    const [events, setEvents] = useState([]);
    const [stacDiag, setStacDiag] = useState(null);
    const [diagLoading, setDiagLoading] = useState(false);

    const checkStacConnection = async () => {
        setDiagLoading(true);
        try {
            const res = await api.get(`/api/monitoring/debug?latitude=${latitude}&longitude=${longitude}&radius_km=${radius}`);
            setStacDiag(res.data);
        } catch (e) {
            console.error(e);
        }
        setDiagLoading(false);
    };

    const handleStart = async () => {
        try {
            const res = await api.post('/api/monitoring/start', {
                latitude, longitude, radius_km: radius, monitoring_type: type, frequency: 'daily'
            });
            setJobId(res.data.monitoring_id);
            fetchStatus(res.data.monitoring_id);
        } catch (e) {
            console.error(e);
        }
    };

    const handleTriggerCheck = async () => {
        if (!jobId) return;
        try {
            await api.post(`/api/monitoring/${jobId}/check`);
            fetchStatus(jobId);
        } catch (e) {
            console.error(e);
        }
    };

    const fetchStatus = async (id) => {
        try {
            const [statusRes, histRes, eventsRes] = await Promise.all([
                api.get(`/api/monitoring/status/${id}`),
                api.get(`/api/monitoring/history/${id}`),
                api.get(`/api/monitoring/events`)
            ]);
            setJobData(statusRes.data);
            setHistory(histRes.data.history.reverse());
            setEvents(eventsRes.data);
        } catch (e) {
            console.error(e);
        }
    };

    useEffect(() => {
        let interval;
        if (jobId) {
            interval = setInterval(() => {
                fetchStatus(jobId);
            }, 5000);
        }
        return () => clearInterval(interval);
    }, [jobId]);

    const renderEventIcon = (stage) => {
        if (stage.includes('NO_NEW_DATA') || stage.includes('NO_SIGNIFICANT_CHANGE')) return <div className="w-2 h-2 rounded-full bg-slate-500 mt-1.5" />;
        if (stage.includes('NEW_') || stage.includes('PROCESSING')) return <div className="w-2 h-2 rounded-full bg-ocean-500 mt-1.5" />;
        if (stage.includes('ANALYSIS')) return <div className="w-2 h-2 rounded-full bg-emerald-500 mt-1.5" />;
        if (stage.includes('POTENTIAL') || stage.includes('RISK')) return <AlertTriangle className="w-3 h-3 text-red-500 mt-1" />;
        return <div className="w-2 h-2 rounded-full bg-white mt-1.5" />;
    };

    const formatDate = (ds) => {
        if (!ds) return 'N/A';
        const d = new Date(ds);
        return d.toLocaleDateString() + ' ' + d.toLocaleTimeString();
    };

    return (
        <div className="max-w-7xl mx-auto space-y-8 pb-12 animate-in fade-in zoom-in-95 duration-700 font-sans">
            <div className="mb-8 flex justify-between items-end border-b border-ocean-600/20 pb-6 relative">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2 flex items-center">
                        <Activity className="mr-3 text-emerald-400" />
                        Live Monitoring
                    </h1>
                    <p className="text-ocean-200">Near-real-time monitoring based on the latest available Sentinel-1 satellite acquisition.</p>
                </div>
                {jobId && (
                    <button onClick={handleTriggerCheck} className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs uppercase tracking-widest rounded-lg flex items-center">
                        <RefreshCcw className="w-4 h-4 mr-2" /> Trigger Satellite Check
                    </button>
                )}
            </div>

            {!jobId ? (
                <div className="bg-slate-900 border border-slate-800 p-8 rounded-2xl max-w-2xl mx-auto">
                    <h2 className="text-xl font-bold text-white mb-6 border-b border-slate-800 pb-4">Configure Target Monitored Area (AOI)</h2>
                    <div className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-xs uppercase tracking-widest text-slate-400 font-bold mb-2">Latitude</label>
                                <input type="number" step="0.0001" className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-slate-100 placeholder-slate-600" value={latitude} onChange={(e) => setLatitude(parseFloat(e.target.value))} />
                            </div>
                            <div>
                                <label className="block text-xs uppercase tracking-widest text-slate-400 font-bold mb-2">Longitude</label>
                                <input type="number" step="0.0001" className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-slate-100 placeholder-slate-600" value={longitude} onChange={(e) => setLongitude(parseFloat(e.target.value))} />
                            </div>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-xs uppercase tracking-widest text-slate-400 font-bold mb-2">Radius (km)</label>
                                <input type="number" className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-slate-100" value={radius} onChange={(e) => setRadius(parseFloat(e.target.value))} />
                            </div>
                            <div>
                                <label className="block text-xs uppercase tracking-widest text-slate-400 font-bold mb-2">Target Type</label>
                                <select className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-slate-100" value={type} onChange={(e) => setType(e.target.value)}>
                                    <option value="flood">Flood Risk Monitoring</option>
                                    <option value="glacier">Glacier / GLOF Risk Monitoring</option>
                                    <option value="general">General Surface Change Detection</option>
                                </select>
                            </div>
                        </div>
                        <div className="grid grid-cols-2 gap-4 mt-6">
                            <button onClick={checkStacConnection} className="w-full bg-slate-800 hover:bg-slate-700 text-white block py-4 text-sm font-bold uppercase tracking-widest rounded-xl transition-all flex items-center justify-center">
                                {diagLoading ? 'Testing...' : 'Test STAC Connection'}
                            </button>
                            <button onClick={handleStart} className="w-full bg-emerald-600 hover:bg-emerald-500 text-white block py-4 text-sm font-bold uppercase tracking-widest rounded-xl transition-all">
                                Initiate Tracking
                            </button>
                        </div>

                        {stacDiag && (
                            <div className="mt-4 p-5 bg-slate-950 border border-slate-800 rounded-xl space-y-3">
                                <h3 className="text-xs uppercase font-bold text-ocean-400 tracking-widest border-b border-slate-800 pb-2 mb-2">Diagnostic Protocol</h3>
                                <div className="text-xs font-mono text-slate-300">STAC CONNECTION: <span className={stacDiag.error ? "text-red-400" : "text-emerald-400 font-bold"}>{stacDiag.error ? "FAILED" : "SUCCESS (HTTP " + stacDiag.http_status + ")"}</span></div>
                                <div className="text-xs font-mono text-slate-300">Collections found: {stacDiag.available_collections?.length || 0}</div>
                                <div className="text-xs font-mono text-slate-300">Sentinel-1 collection: <span className={(stacDiag.available_collections || []).some(x => x.includes('sentinel-1-grd')) ? "text-emerald-400" : "text-amber-400"}>{(stacDiag.available_collections || []).some(x => x.includes('sentinel-1-grd')) ? 'AVAILABLE' : 'NOT AVAILABLE'}</span></div>

                                {stacDiag.items_found === 0 ? (
                                    <div className="mt-4 p-3 border border-red-900/50 bg-red-950/20 text-red-200 text-xs italic rounded">
                                        No Sentinel-1 acquisition found matching the current AOI and filters. <br />
                                        AOI: [{stacDiag.bbox.join(', ')}]
                                    </div>
                                ) : (
                                    <div className="mt-4 space-y-2 p-3 bg-emerald-950/20 border border-emerald-900/50 rounded-lg">
                                        <div className="text-[10px] font-bold text-emerald-500 uppercase tracking-widest mb-1">REAL SATELLITE ACQUISITION FOUND</div>
                                        <div className="text-xs font-mono text-emerald-100">Platform: Sentinel-1</div>
                                        <div className="text-xs font-mono text-emerald-100">Product ID: {stacDiag.latest_item?.id}</div>
                                        <div className="text-xs font-mono text-emerald-100">Acquisition Time: {stacDiag.latest_item?.datetime}</div>
                                        <div className="text-xs font-mono text-emerald-100">Orbit Direction: {stacDiag.latest_item?.orbit_direction}</div>
                                        <div className="text-xs font-mono text-emerald-100">Source: {stacDiag.stac_endpoint}</div>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                </div>
            ) : (
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">

                    {/* Status Dash */}
                    <div className="col-span-1 lg:col-span-4 space-y-4">
                        <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl">
                            <div className="flex items-center justify-between mb-4">
                                <div className="text-xs uppercase tracking-widest font-bold text-slate-400">Monitoring Status</div>
                                <div className="px-2.5 py-1 bg-emerald-950 border border-emerald-500/50 text-emerald-400 text-[10px] font-bold rounded flex items-center uppercase"><div className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-ping mr-2"></div> ACTIVE</div>
                            </div>

                            <div className="space-y-4">
                                <div>
                                    <div className="text-[10px] uppercase font-bold text-slate-500 mb-1">Data Mode</div>
                                    <div className="text-sm font-medium text-white flex items-center"><Database className="w-3.5 h-3.5 mr-2 text-ocean-400" /> Latest Available Sentinel-1 Acquisition</div>
                                </div>
                                <div>
                                    <div className="text-[10px] uppercase font-bold text-slate-500 mb-1">Monitored Area (AOI)</div>
                                    <div className="text-sm font-medium text-white flex items-center"><MapPin className="w-3.5 h-3.5 mr-2 text-ocean-400" /> {jobData?.latitude}, {jobData?.longitude}</div>
                                </div>
                                <div className="grid grid-cols-2 gap-4 border-t border-slate-800 pt-4 mt-4">
                                    <div>
                                        <div className="text-[10px] uppercase font-bold text-slate-500 mb-1">Last Satellite Check</div>
                                        <div className="text-xs font-mono text-slate-300">{formatDate(jobData?.last_checked)}</div>
                                    </div>
                                    <div>
                                        <div className="text-[10px] uppercase font-bold text-slate-500 mb-1">Latest Acquisition (Actual)</div>
                                        <div className="text-xs font-mono text-slate-300">{jobData?.latest_acquisition ? formatDate(jobData.latest_acquisition.acquisition_datetime) : 'N/A'}</div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {events.length > 0 && (
                            <div className="bg-red-950/20 border border-red-900/50 p-6 rounded-2xl">
                                <h3 className="text-xs font-bold text-red-500 uppercase tracking-widest mb-4 flex items-center"><ShieldAlert className="w-4 h-4 mr-2" /> Threat Events Detected</h3>
                                <div className="space-y-3">
                                    {events.map((ev, i) => (
                                        <div key={i} className="bg-slate-950 p-3 rounded-lg border border-red-900/30">
                                            <div className="flex justify-between items-center mb-2">
                                                <span className="text-[10px] font-bold text-red-400 bg-red-950 px-2 py-0.5 rounded">{ev.status}</span>
                                                <span className="text-[10px] font-mono text-slate-500">{formatDate(ev.acquisition_time)}</span>
                                            </div>
                                            <p className="text-xs text-slate-300 leading-relaxed mb-2">{ev.message}</p>
                                            <div className="text-[10px] text-slate-500 uppercase tracking-widest">Confidence: <span className="text-white font-bold">{ev.confidence}%</span> | Sentinel-1</div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Timeline */}
                    <div className="col-span-1 lg:col-span-8">
                        <div className="bg-slate-900 border border-slate-800 p-8 rounded-2xl h-full">
                            <h3 className="text-sm font-bold text-white uppercase tracking-widest mb-6 flex items-center border-b border-slate-800 pb-4">
                                <Clock className="w-5 h-5 mr-3 text-ocean-400" /> Event Timeline
                            </h3>

                            <div className="relative pl-4 space-y-6">
                                <div className="absolute left-[7px] top-2 bottom-2 w-0.5 bg-slate-800"></div>
                                {history.length === 0 && <div className="text-xs text-slate-500 italic ml-4">Awaiting first scheduled tick...</div>}

                                {history.map((hist, i) => (
                                    <div key={i} className="relative flex items-start">
                                        <div className="absolute -left-[4.5px] bg-slate-900 pb-2">
                                            {renderEventIcon(hist.stage)}
                                        </div>
                                        <div className="ml-6 flex-1 bg-slate-950 rounded-lg p-3 border border-slate-800/50">
                                            <div className="flex justify-between">
                                                <p className="text-xs font-bold text-slate-300">
                                                    {hist.stage.includes('POTENTIAL') ? (
                                                        <span className="text-red-400">⚠ {hist.message}</span>
                                                    ) : (
                                                        <span>{hist.message}</span>
                                                    )}
                                                </p>
                                                <span className="text-[10px] font-mono text-slate-500 ml-4 shrink-0">{formatDate(hist.timestamp)}</span>
                                            </div>
                                            <div className="text-[10px] font-bold tracking-widest text-slate-600 mt-2 uppercase">{hist.stage.replace(/_/g, ' ')}</div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>

                </div>
            )}
        </div>
    );
}

// Needed to implement `RefreshCcw` import fix in imports since React lucide requires correct case.
// Just ensuring `RefreshCcw` is valid.
