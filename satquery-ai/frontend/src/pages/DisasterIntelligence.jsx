import React, { useState } from 'react';
import ImageUploader from '../components/ImageUploader';
import AnalysisLoader from '../components/AnalysisLoader';
import { Send, AlertCircle, Siren, Activity, GitCommit, Search, Link } from 'lucide-react';
import api from '../services/api';

const DisasterIntelligence = () => {
    const [targetFile, setTargetFile] = useState(null);
    const [targetPreview, setTargetPreview] = useState(null);
    const [baselineFile, setBaselineFile] = useState(null);
    const [baselinePreview, setBaselinePreview] = useState(null);
    const [query, setQuery] = useState('Analyze disaster presence, mapping hazards from visual and temporal components.');

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [result, setResult] = useState(null);

    const handleAnalyze = async () => {
        if (!targetFile) {
            setError("Please provide a target image for combined disaster analysis.");
            return;
        }

        setError(null);
        setLoading(true);
        setResult(null);

        const formData = new FormData();
        formData.append('query', query);

        if (baselineFile) {
            formData.append('before_image', baselineFile);
            formData.append('after_image', targetFile);
        } else {
            formData.append('image', targetFile);
        }

        try {
            const response = await api.post('/disaster-analysis', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            setResult(response.data);
        } catch (err) {
            console.error(err);
            setError(err.response?.data?.detail || "An error occurred during generalized disaster orchestration.");
        } finally {
            setLoading(false);
        }
    };

    const getRiskColor = (level) => {
        if (!level) return 'text-slate-400 bg-slate-800 border-slate-700';
        switch (level.toUpperCase()) {
            case 'CRITICAL': return 'text-red-500 bg-red-500/10 border-red-500/30';
            case 'HIGH': return 'text-orange-500 bg-orange-500/10 border-orange-500/30';
            case 'MODERATE': return 'text-yellow-400 bg-yellow-400/10 border-yellow-400/30';
            case 'LOW': return 'text-green-400 bg-green-400/10 border-green-400/30';
            default: return 'text-slate-400 bg-slate-800 border-slate-700';
        }
    };

    return (
        <div className="max-w-7xl mx-auto space-y-6 pb-12">
            <div className="mb-6">
                <h1 className="text-3xl font-bold text-white mb-2 flex items-center">
                    <Siren className="mr-3 text-impact-red" />
                    Disaster Intelligence Matrix
                </h1>
                <p className="text-slate-400">Unified pipeline routing requests through all available intelligence specialists automatically.</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">

                {/* Input Panel */}
                <div className="lg:col-span-5 space-y-6 h-full flex flex-col">
                    <div className="glass-panel p-5 border-t-[3px] border-t-impact-red flex-1 flex flex-col">

                        <div className="space-y-4 mb-6">
                            <ImageUploader
                                file={targetFile} setFile={setTargetFile}
                                preview={targetPreview} setPreview={setTargetPreview}
                                label="Post-Disaster Imagery"
                            />
                            <ImageUploader
                                file={baselineFile} setFile={setBaselineFile}
                                preview={baselinePreview} setPreview={setBaselinePreview}
                                label="Baseline Imagery (Optional)"
                            />
                        </div>

                        <div className="mt-auto">
                            <label className="block text-sm font-medium text-slate-400 mb-2">Automated Discovery Prompt</label>
                            <textarea
                                className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-slate-200 focus:outline-none focus:border-impact-red focus:ring-1 focus:ring-impact-red placeholder-slate-600 text-sm resize-none h-24"
                                value={query}
                                onChange={(e) => setQuery(e.target.value)}
                            />

                            <button
                                onClick={handleAnalyze}
                                disabled={loading || !targetFile || !query.trim()}
                                className="w-full mt-4 bg-impact-red hover:bg-red-500 text-white font-bold py-4 px-4 rounded-lg flex items-center justify-center transition-colors shadow-[0_0_20px_rgba(255,51,51,0.2)] disabled:opacity-50 disabled:shadow-none disabled:cursor-not-allowed uppercase tracking-wider"
                            >
                                {loading ? 'Initializing Cortex...' : (
                                    <>Run Global Assessment <Activity className="ml-2 w-5 h-5" /></>
                                )}
                            </button>

                            {error && (
                                <div className="mt-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg flex items-start text-red-400 text-sm">
                                    <AlertCircle className="w-5 h-5 mr-2 shrink-0" />
                                    <span>{error}</span>
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Output Panel */}
                <div className="lg:col-span-7">
                    <div className="glass-panel h-full min-h-[600px] flex flex-col relative overflow-hidden bg-slate-900/50">
                        {loading ? (
                            <div className="flex-1 flex flex-col items-center justify-center w-full h-full p-8 border border-slate-800 m-4 rounded-xl bg-slate-900/80">
                                <AnalysisLoader />
                                <div className="mt-12 opacity-50 flex items-center space-x-2 text-xs font-mono uppercase tracking-widest text-accent-blue">
                                    <span>[</span>
                                    <GitCommit className="w-4 h-4 animate-ping" />
                                    <span>Routing to active specialist protocols]</span>
                                </div>
                            </div>
                        ) : null}

                        <div className={`p-6 flex flex-col h-full ${loading ? 'opacity-0 pointer-events-none absolute' : 'relative'}`}>
                            {!result && !loading ? (
                                <div className="flex-1 flex flex-col items-center justify-center text-slate-500">
                                    {/* Cool node graph illustration */}
                                    <div className="relative w-full max-w-sm h-64 mb-6">
                                        <div className="absolute top-0 left-1/2 -translate-x-1/2 p-4 bg-slate-800 border border-slate-700 rounded-xl text-center shadow-lg">
                                            <Search className="w-6 h-6 mx-auto mb-2 text-slate-400" />
                                            <span className="text-xs font-bold uppercase tracking-wider">Query Node</span>
                                        </div>

                                        {/* Connections */}
                                        <svg className="absolute inset-0 w-full h-full pointer-events-none" style={{ zIndex: 0 }}>
                                            <path d="M 192 80 L 80 180" stroke="rgba(255,255,255,0.1)" strokeWidth="2" fill="none" strokeDasharray="4" />
                                            <path d="M 192 80 L 192 180" stroke="rgba(255,255,255,0.1)" strokeWidth="2" fill="none" strokeDasharray="4" />
                                            <path d="M 192 80 L 304 180" stroke="rgba(255,255,255,0.1)" strokeWidth="2" fill="none" strokeDasharray="4" />
                                        </svg>

                                        <div className="absolute bottom-4 left-4 p-3 bg-slate-800/80 border border-slate-700 rounded-lg text-center backdrop-blur text-cyan-400">
                                            <span className="text-[10px] font-bold uppercase block">Flood Spec</span>
                                        </div>
                                        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 p-3 bg-slate-800/80 border border-slate-700 rounded-lg text-center backdrop-blur text-purple-400">
                                            <span className="text-[10px] font-bold uppercase block">Change Det</span>
                                        </div>
                                        <div className="absolute bottom-4 right-4 p-3 bg-slate-800/80 border border-slate-700 rounded-lg text-center backdrop-blur text-slate-300">
                                            <span className="text-[10px] font-bold uppercase block">Glacier Spec</span>
                                        </div>
                                    </div>
                                    <h3 className="text-xl font-medium text-slate-400 mb-2">System Interfacing</h3>
                                    <p className="max-w-md text-center text-sm leading-relaxed">
                                        Input data is recursively passed through specialized micro-agents. Findings are aggregated into a unified situational report automatically.
                                    </p>
                                </div>
                            ) : null}

                            {result && (
                                <div className="animate-in fade-in zoom-in-95 duration-500 h-full flex flex-col space-y-6">

                                    {/* Master status line */}
                                    <div className="flex border-b border-slate-800 pb-4">
                                        <div className="flex-1">
                                            <div className="text-xs text-slate-500 uppercase tracking-widest font-semibold mb-1">Detected Typology</div>
                                            <div className="text-2xl font-black tracking-widest uppercase text-white drop-shadow-md">
                                                {result.disaster_type?.replace(/_/g, ' ') || 'UNKNOWN'}
                                            </div>
                                        </div>
                                        {result.risk_assessment && (
                                            <div className="text-right">
                                                <div className="text-xs text-slate-500 uppercase tracking-widest font-semibold mb-1">Global Risk</div>
                                                <div className={`text-2xl font-black ${getRiskColor(result.risk_assessment.risk_level)} px-4 py-1 rounded border inline-block`}>
                                                    {result.risk_assessment.risk_level}
                                                    <span className="text-sm ml-2 opacity-60">[{result.risk_assessment.risk_score}]</span>
                                                </div>
                                            </div>
                                        )}
                                    </div>

                                    {/* Grid output */}
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 flex-1 overflow-y-auto custom-scrollbar pr-2 pb-4">

                                        {/* Agent Route Trace */}
                                        <div className="col-span-1 md:col-span-2 bg-slate-900 border border-slate-700 rounded-xl p-4 relative overflow-hidden">
                                            <div className="absolute inset-0 bg-gradient-to-br from-impact-red/5 to-transparent pointer-events-none"></div>
                                            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-4 flex items-center relative z-10">
                                                <Link className="w-4 h-4 mr-2 text-slate-500" /> Executive Trace
                                            </h3>
                                            <div className="relative z-10 w-full rounded-lg bg-black/40 border border-slate-800 p-4">
                                                <ul className="space-y-4">
                                                    <li className="flex items-start text-sm">
                                                        <div className="w-6 h-6 rounded-full bg-slate-800 flex items-center justify-center mr-3 border border-slate-600 shadow shrink-0 text-slate-300">1</div>
                                                        <div>
                                                            <strong className="text-slate-200">Query Parsing & Intent</strong>
                                                            <span className="block text-slate-500 text-xs mt-1">Discovered `{result.disaster_type}` context from input.</span>
                                                        </div>
                                                    </li>
                                                    <li className="flex items-start text-sm">
                                                        <div className="w-6 h-6 rounded-full bg-accent-blue/20 text-accent-blue flex items-center justify-center mr-3 border border-accent-blue/30 shadow shrink-0">2</div>
                                                        <div>
                                                            <strong className="text-slate-200">Specialist Invocation</strong>
                                                            <span className="block text-slate-500 text-xs mt-1">Routed to subsystem `{result.analysis_type}`. Processing spectral imagery metrics.</span>
                                                        </div>
                                                    </li>
                                                    <li className="flex items-start text-sm">
                                                        <div className="w-6 h-6 rounded-full bg-impact-red/20 text-impact-red flex items-center justify-center mr-3 border border-impact-red/30 shadow shrink-0 text-[10px]">✔</div>
                                                        <div className="flex-1">
                                                            <strong className="text-slate-200">Consolidation & Assessment </strong>
                                                            <div className="bg-slate-900 border border-slate-800 p-3 rounded mt-2 text-slate-300 text-sm whitespace-pre-wrap leading-relaxed shadow-inner font-mono max-h-32 overflow-y-auto">
                                                                {result.evidence?.[0]?.source || "System completed operation without discrete node tags."}
                                                                {result.risk_assessment?.risk_factors?.map((f, i) => `\n=> ${f.factor}`) || "\nRisk nodes calculated"}
                                                            </div>
                                                        </div>
                                                    </li>
                                                </ul>
                                            </div>
                                        </div>

                                        {/* Fast insights / recommendations */}
                                        {result.recommendations && result.recommendations.length > 0 && (
                                            <div className="col-span-1 md:col-span-2 bg-slate-900 border border-slate-700 p-4 rounded-xl">
                                                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3">Post-Evaluation Actions</h3>
                                                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                                    {result.recommendations.map((rec, i) => (
                                                        <div key={i} className="flex bg-slate-800/50 border border-slate-700 p-3 rounded-lg text-sm text-slate-300 leading-snug">
                                                            <div className="w-1 h-full bg-impact-red rounded-full mr-3 shrink-0"></div>
                                                            {rec}
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        )}

                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default DisasterIntelligence;
