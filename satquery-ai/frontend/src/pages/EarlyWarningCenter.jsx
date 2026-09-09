import React, { useState } from 'react';
import ImageUploader from '../components/ImageUploader';
import AnalysisLoader from '../components/AnalysisLoader';
import { AlertTriangle, Activity, Map, ArrowRight, ShieldAlert, Navigation } from 'lucide-react';
import api from '../services/api';

export default function EarlyWarningCenter() {
    const [targetFile, setTargetFile] = useState(null);
    const [targetPreview, setTargetPreview] = useState(null);
    const [query, setQuery] = useState('Analyze disaster presence, detect infrastructure exposure and determine early warning levels.');

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [result, setResult] = useState(null);

    const handleAnalyze = async () => {
        if (!targetFile) {
            setError("Target image is required for impact extraction.");
            return;
        }

        setError(null);
        setLoading(true);
        setResult(null);

        const formData = new FormData();
        formData.append('query', query);
        formData.append('image', targetFile);
        // Added mocked lat/long optionally if they wanted it, we will keep it image relative.

        try {
            const response = await api.post('/analyze/early-warning', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            setResult(response.data);
        } catch (err) {
            console.error(err);
            setError(err.response?.data?.detail || "An error occurred.");
        } finally {
            setLoading(false);
        }
    };

    const getWarningColorBlock = (level) => {
        if (!level) return 'border-slate-800 bg-slate-900';
        switch (level.toUpperCase()) {
            case 'GREEN': return 'bg-green-500/10 border-green-500/50 text-green-400';
            case 'YELLOW': return 'bg-yellow-400/10 border-yellow-400/50 text-yellow-400';
            case 'ORANGE': return 'bg-orange-500/10 border-orange-500/50 text-orange-400';
            case 'RED': return 'bg-red-500/10 border-red-500/50 text-red-500 animate-pulse';
            default: return 'border-slate-800 bg-slate-900';
        }
    };

    return (
        <div className="max-w-7xl mx-auto space-y-8 pb-12">
            <div className="mb-6">
                <h1 className="text-3xl font-bold text-white mb-2 flex items-center">
                    <ShieldAlert className="mr-3 text-orange-500" />
                    Early Warning Intelligence Center
                </h1>
                <p className="text-slate-400">Decision Support System: Geospatial & Downstream Infrastructure Exposure Prediction.</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

                {/* Inputs Setup */}
                <div className="glass-panel p-5 border-t-[3px] border-t-orange-500 h-max">
                    <ImageUploader
                        file={targetFile} setFile={setTargetFile}
                        preview={targetPreview} setPreview={setTargetPreview}
                        label="SATELLITE INTEL"
                    />
                    <div className="mt-6">
                        <label className="block text-sm font-medium text-slate-400 mb-2">Threat Extraction Protocol</label>
                        <textarea
                            className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-slate-200 focus:outline-none focus:border-orange-500 text-sm h-28"
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                        />
                        <button
                            onClick={handleAnalyze}
                            disabled={loading || !targetFile}
                            className="w-full mt-4 bg-orange-600 hover:bg-orange-500 text-white font-bold py-4 rounded-lg flex items-center justify-center transition-all disabled:opacity-50 uppercase tracking-widest text-sm shadow-[0_0_15px_rgba(234,88,12,0.3)]"
                        >
                            {loading ? 'Compiling Warning...' : (
                                <>Generate Early Warning <Navigation className="ml-2 w-4 h-4 ml-3" /></>
                            )}
                        </button>
                    </div>
                </div>

                {/* Warning Display */}
                <div className="lg:col-span-2 flex flex-col h-full bg-slate-900 border border-slate-800 rounded-xl relative overflow-hidden">
                    {loading && (
                        <div className="absolute inset-0 z-50 bg-slate-900/90 flex flex-col items-center justify-center">
                            <AnalysisLoader />
                            <div className="mt-8 text-xs font-mono text-orange-500 tracking-widest animate-pulse">STRUCTURING GEOSPATIAL IMPACT...</div>
                        </div>
                    )}

                    {result ? (
                        <div className="p-8 flex flex-col h-full overflow-y-auto">

                            {/* Header Master Row */}
                            <div className="flex flex-wrap items-center justify-between mb-8 gap-4 border-b border-white/10 pb-6">
                                <div>
                                    <div className="text-xs font-mono text-slate-500 mb-1">WARNING LEVEL</div>
                                    <div className={`px-6 py-2 border-2 rounded-xl text-3xl font-black tracking-widest ${getWarningColorBlock(result.warning_level)}`}>
                                        {result.warning_level}
                                    </div>
                                </div>
                                <div className="text-right">
                                    <div className="text-xs font-mono text-slate-500 mb-1">RISK SCORE: {result.disaster_type}</div>
                                    <div className="text-4xl text-white font-medium">{result.risk_score} <span className="text-xl text-slate-500">/ 100</span></div>
                                </div>
                            </div>

                            <div className="text-white text-xl font-semibold mb-6 flex items-center border-l-4 border-orange-500 pl-4 py-1 bg-slate-800/40">
                                {result.headline}
                            </div>

                            {/* Triple Grid */}
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                                <div className="bg-black/30 border border-slate-800 p-5 rounded-xl">
                                    <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-4 flex"><Activity className="w-4 h-4 mr-2" /> Detected Indicators</h3>
                                    <ul className="space-y-3">
                                        {result.detected_indicators?.map((i, idx) => (
                                            <li key={idx} className="text-sm text-slate-300 flex items-start"><ArrowRight className="w-4 h-4 mr-2 text-slate-500 shrink-0" /> {i}</li>
                                        ))}
                                    </ul>
                                </div>

                                <div className="bg-black/30 border border-slate-800 p-5 rounded-xl">
                                    <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-4 flex"><Map className="w-4 h-4 mr-2" /> Potential Impact</h3>
                                    <div className="text-sm text-slate-300 space-y-4">
                                        <div><strong>Region Spread:</strong> {result.potential_impact?.affected_regions?.map(r => r).join(", ") || "Visual extraction only."}</div>
                                        <div><strong>Infrastructure Analysis:</strong> {result.potential_impact?.infrastructure_exposure?.join(", ") || "No direct infrastructure detected near hazard footprints."}</div>
                                        <div><strong>Downstream Terrain:</strong> {result.limitations?.[0] || (result.potential_impact?.downstream_analysis_available ? "Mapped" : "Constrained.")}</div>
                                    </div>
                                </div>
                            </div>

                            {/* Recommended Actions */}
                            <div className="bg-orange-500/5 border border-orange-500/20 p-6 rounded-xl mt-auto">
                                <h3 className="font-bold text-orange-400 uppercase tracking-widest mb-3 flex items-center"><AlertTriangle className="w-5 h-5 mr-3" /> Recommended Actions</h3>
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
                                    {result.recommended_actions?.map((r, i) => (
                                        <div key={i} className="bg-slate-900 border border-slate-800 p-3 rounded-lg text-sm text-slate-200">
                                            {r}
                                        </div>
                                    ))}
                                </div>
                            </div>

                        </div>
                    ) : (
                        <div className="flex flex-col items-center justify-center flex-1 text-slate-500 opacity-60">
                            <ShieldAlert className="w-24 h-24 mb-4 text-slate-700" />
                            <p>Execute Threat Extraction Protocol to Map Impact Zones</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}
