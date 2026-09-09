import React, { useState } from 'react';
import { Network, MapPin, Search, Maximize, AlertCircle, RefreshCcw } from 'lucide-react';
import api from '../services/api';

export default function SatelliteLocationAnalysis() {
    const [latitude, setLatitude] = useState(28.0);
    const [longitude, setLongitude] = useState(86.9);
    const [radius, setRadius] = useState(10);
    const [beforeDate, setBeforeDate] = useState('2026-07-01');
    const [afterDate, setAfterDate] = useState('2026-08-30');
    const [query, setQuery] = useState('Check for flood-related changes.');

    const [stepContext, setStepContext] = useState('');
    const [loadingStage, setLoadingStage] = useState(0);
    const [error, setError] = useState(null);
    const [result, setResult] = useState(null);

    const handleAnalyze = async () => {
        setError(null);
        setLoadingStage(1);
        setStepContext('SATELLITE DATA ACQUISITION');
        setResult(null);

        let t1, t2, t3, t4;

        try {
            const formData = {
                latitude, longitude, radius_km: radius,
                before_date: beforeDate, after_date: afterDate, query
            };

            // Simulating API visual stages while waiting for the monolithic pipeline
            t1 = setTimeout(() => { setLoadingStage(2); setStepContext('METADATA VALIDATION'); }, 1000);
            t2 = setTimeout(() => { setLoadingStage(3); setStepContext('BEFORE & AFTER IMAGE PROCESSING\n(SAR Radiometric Calibration)'); }, 2500);
            t3 = setTimeout(() => { setLoadingStage(4); setStepContext('IMAGE ALIGNMENT\n(Spatial Grid Overlay)'); }, 4000);
            t4 = setTimeout(() => { setLoadingStage(5); setStepContext('READY FOR DISASTER ANALYSIS\n(Calculating Risk Scores)'); }, 5500);

            const response = await api.post('/api/satellite/analyze/location', formData);
            setResult(response.data);

        } catch (err) {
            console.error(err);
            setError(err.response?.data?.detail || "An error occurred connecting to Copernicus Sentinel Hub.");
        } finally {
            clearTimeout(t1);
            clearTimeout(t2);
            clearTimeout(t3);
            clearTimeout(t4);
            setLoadingStage(0);
        }
    };

    return (
        <div className="max-w-7xl mx-auto space-y-8 pb-12 animate-in fade-in zoom-in-95 duration-700">
            <div className="mb-8 flex flex-col items-start gap-4 border-b border-ocean-600/20 pb-6 relative">
                <div className="absolute top-0 right-0 p-3 bg-ocean-900/40 rounded-xl border border-ocean-600/30 font-bold text-ocean-400 text-sm tracking-uppercase flex items-center">
                    <Network className="w-5 h-5 mr-3" />
                    SAR / RADAR DATA
                </div>
                <h1 className="text-3xl font-bold text-white mb-2 flex items-center">
                    <MapPin className="mr-3 text-ocean-500" />
                    Satellite Location Analysis
                </h1>
                <p className="text-ocean-200">Automatically retrieve live Sentinel-1 GRD imagery for a geographic bounding box.</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">

                {/* Inputs Setup (Left sidebar 4 cols) */}
                <div className="col-span-1 lg:col-span-4 space-y-6">
                    <div className="bg-ocean-900/40 backdrop-blur-md border border-ocean-800 p-6 rounded-2xl">
                        <div className="space-y-4">
                            <div>
                                <label className="block text-xs uppercase tracking-widest text-ocean-400 font-bold mb-2">Latitude</label>
                                <input type="number" step="0.0001" className="w-full bg-ocean-950/80 border border-ocean-700 rounded-lg p-2.5 text-ocean-100 placeholder-ocean-600" value={latitude} onChange={(e) => setLatitude(parseFloat(e.target.value))} />
                            </div>
                            <div>
                                <label className="block text-xs uppercase tracking-widest text-ocean-400 font-bold mb-2">Longitude</label>
                                <input type="number" step="0.0001" className="w-full bg-ocean-950/80 border border-ocean-700 rounded-lg p-2.5 text-ocean-100 placeholder-ocean-600" value={longitude} onChange={(e) => setLongitude(parseFloat(e.target.value))} />
                            </div>
                            <div>
                                <label className="block text-xs uppercase tracking-widest text-ocean-400 font-bold mb-2">Radius (km)</label>
                                <input type="number" className="w-full bg-ocean-950/80 border border-ocean-700 rounded-lg p-2.5 text-ocean-100 placeholder-ocean-600" value={radius} onChange={(e) => setRadius(parseFloat(e.target.value))} />
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-xs uppercase tracking-widest text-ocean-400 font-bold mb-2">Before Date</label>
                                    <input type="date" className="w-full bg-ocean-950/80 border border-ocean-700 rounded-lg p-2.5 text-ocean-100 text-xs" value={beforeDate} onChange={(e) => setBeforeDate(e.target.value)} />
                                </div>
                                <div>
                                    <label className="block text-xs uppercase tracking-widest text-ocean-400 font-bold mb-2">After Date</label>
                                    <input type="date" className="w-full bg-ocean-950/80 border border-ocean-700 rounded-lg p-2.5 text-ocean-100 text-xs" value={afterDate} onChange={(e) => setAfterDate(e.target.value)} />
                                </div>
                            </div>
                            <div>
                                <label className="block text-xs uppercase tracking-widest text-ocean-400 font-bold mb-2">Intelligence Target</label>
                                <input type="text" className="w-full bg-ocean-950/80 border border-ocean-700 rounded-lg p-2.5 text-ocean-100" value={query} onChange={(e) => setQuery(e.target.value)} />
                            </div>

                            <button
                                onClick={handleAnalyze}
                                disabled={loadingStage > 0}
                                className="w-full mt-4 bg-ocean-600 hover:bg-ocean-500 text-white font-bold py-4 rounded-xl flex items-center justify-center transition-all disabled:opacity-50 uppercase tracking-widest text-sm shadow-lg shadow-ocean-500/20 hover:-translate-y-1"
                            >
                                {loadingStage > 0 ? 'Executing Pipeline...' : (
                                    <>🚀 ANALYZE LOCATION</>
                                )}
                            </button>

                            {error && (
                                <div className="mt-4 p-4 bg-red-500/10 border border-red-500/30 rounded-lg flex items-start text-red-400 text-xs">
                                    <AlertCircle className="w-4 h-4 mr-2 shrink-0" />
                                    <span>{error}</span>
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Right Col 8: Results display */}
                <div className="col-span-1 lg:col-span-8 flex flex-col h-full">
                    {loadingStage > 0 && (
                        <div className="flex-1 min-h-[400px] flex flex-col items-center justify-center bg-ocean-900/20 border border-ocean-800 rounded-2xl p-8">
                            <RefreshCcw className="w-16 h-16 text-ocean-500 animate-spin mb-8" />
                            <div className="w-full max-w-md bg-ocean-950 rounded-full h-2.5 mb-4 border border-ocean-800">
                                <div className="bg-ocean-500 h-2.5 rounded-full transition-all duration-500" style={{ width: `${(loadingStage / 5) * 100}%` }}></div>
                            </div>
                            <div className="text-sm font-bold text-center text-ocean-400 tracking-widest whitespace-pre-wrap">{stepContext}</div>
                        </div>
                    )}

                    {loadingStage === 0 && result && (
                        <div className="bg-ocean-900/40 backdrop-blur-md border border-ocean-800 p-8 rounded-2xl animate-in fade-in slide-in-from-right-8 duration-500 h-full">
                            <div className="flex items-center justify-between border-b border-ocean-700/50 pb-6 mb-8">
                                <div>
                                    <div className="text-xs text-ocean-500 uppercase tracking-widest font-bold mb-1">Disaster Brain Assessment (SAR Target)</div>
                                    <div className="text-2xl font-bold text-white">Latest Available Satellite Acquisition</div>
                                </div>
                                <div className="p-3 bg-ocean-950 rounded-xl border border-ocean-700 flex flex-col items-end">
                                    <div className="text-[10px] text-ocean-500 font-bold tracking-widest uppercase">Target Bounding Box</div>
                                    <div className="font-mono text-xs text-ocean-200 mt-1">
                                        [{result.aoi.bbox.join(", ")}]
                                    </div>
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-6 mb-8">
                                <div className="bg-ocean-950/60 p-5 rounded-xl border border-ocean-800 relative overflow-hidden">
                                    <div className="text-[10px] font-bold text-ocean-500 uppercase tracking-widest mb-3 flex items-center">
                                        <Search className="w-3 h-3 mr-2" /> Before Acquisition (Baseline)
                                    </div>
                                    <div className="text-sm text-ocean-200 font-mono break-all break-words pr-8">{result.before_acquisition.product_id}</div>
                                    <div className="text-xs text-ocean-400 mt-2">{result.before_acquisition.satellite} | {result.before_acquisition.polarization} | {result.before_acquisition.orbit_direction} Orbit</div>
                                </div>
                                <div className="bg-ocean-950/60 p-5 rounded-xl border border-ocean-800 relative overflow-hidden">
                                    <div className="text-[10px] font-bold text-ocean-500 uppercase tracking-widest mb-3 flex items-center">
                                        <Maximize className="w-3 h-3 mr-2" /> Target Acquisition (Current)
                                    </div>
                                    <div className="text-sm text-ocean-200 font-mono break-all break-words pr-8">{result.after_acquisition.product_id}</div>
                                    <div className="text-xs text-ocean-400 mt-2">{result.after_acquisition.satellite} | {result.after_acquisition.polarization} | {result.after_acquisition.orbit_direction} Orbit</div>
                                </div>
                            </div>

                            <div className="bg-ocean-950/60 p-5 rounded-xl border border-ocean-800 mb-8 flex flex-col gap-3">
                                <div className="text-[10px] font-bold text-ocean-500 uppercase tracking-widest">Processing Intelligence</div>
                                <div className="grid grid-cols-2 gap-4 text-xs font-mono text-ocean-200">
                                    <div className="col-span-2 text-ocean-300 font-sans border-b border-ocean-800 pb-2 italic">{result.processing_summary?.status}</div>
                                    <div><span className="text-ocean-400">Status:</span> {result.status}</div>
                                    <div><span className="text-ocean-400">Data Source:</span> {result.data_source}</div>
                                    <div><span className="text-ocean-400">Mode:</span> {result.monitoring_mode}</div>
                                    <div><span className="text-ocean-400">Compatibility Score:</span> {result.compatibility?.score}/100</div>
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-6">
                                <div>
                                    <h3 className="font-bold text-ocean-400 uppercase tracking-widest mb-3">Overall Risk Score</h3>
                                    <div className="text-2xl text-ocean-500/50 font-black tracking-widest">{result.risk_assessment.risk_level.replace(/_/g, ' ')}</div>
                                </div>
                                <div className="space-y-2">
                                    <h3 className="font-bold text-ocean-400 uppercase tracking-widest mb-2">System Status</h3>
                                    {result.limitations.map((lim, i) => (
                                        <div key={i} className="text-xs text-ocean-200 border-l-2 border-ocean-500/50 pl-2">{lim}</div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    )}

                    {loadingStage === 0 && !result && (
                        <div className="flex-1 min-h-[500px] w-full rounded-2xl overflow-hidden relative border border-ocean-800 shadow-[0_0_30px_rgba(0,0,0,0.5)]">
                            <iframe
                                title="Satellite Map of India"
                                width="100%"
                                height="100%"
                                style={{ border: 0, minHeight: '500px', filter: 'contrast(1.1) saturate(1.2)' }}
                                src="https://maps.google.com/maps?q=india&t=k&z=5&ie=UTF8&iwloc=&output=embed"
                                allowFullScreen
                            ></iframe>
                            <div className="absolute top-4 left-4 bg-ocean-950/80 backdrop-blur-md px-4 py-2 rounded-xl border border-ocean-800 flex items-center shadow-lg pointer-events-none">
                                <MapPin className="w-5 h-5 mr-3 text-ocean-500" />
                                <span className="text-xs font-bold text-ocean-100 uppercase tracking-widest">Interactive Satellite View — India</span>
                            </div>
                            <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 bg-ocean-900/90 backdrop-blur-md px-4 py-2 rounded-full border border-ocean-700 flex items-center shadow-lg pointer-events-none">
                                <Maximize className="w-4 h-4 mr-2 text-ocean-400" />
                                <span className="text-[10px] font-bold text-ocean-200 uppercase tracking-widest">Click & Drag to Pan • Scroll to Zoom</span>
                            </div>
                        </div>
                    )}

                </div>
            </div>
        </div>
    );
}
