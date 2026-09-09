import React, { useState } from 'react';
import ImageUploader from '../components/ImageUploader';
import AnalysisLoader from '../components/AnalysisLoader';
import { Send, AlertCircle, Waves, MapPin, Building, AlertTriangle } from 'lucide-react';
import api, { getImageUrl } from '../services/api';

const FloodIntelligence = () => {
    const [targetFile, setTargetFile] = useState(null);
    const [targetPreview, setTargetPreview] = useState(null);
    const [baselineFile, setBaselineFile] = useState(null);
    const [baselinePreview, setBaselinePreview] = useState(null);
    const [query, setQuery] = useState('Compare these satellite images and detect flood-related changes and potentially affected areas.');

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [result, setResult] = useState(null);
    const [showOriginal, setShowOriginal] = useState(false);

    const handleAnalyze = async () => {
        if (!targetFile) {
            setError("Please provide at least a Target Image.");
            return;
        }

        setError(null);
        setLoading(true);
        setResult(null);
        setShowOriginal(false);

        const formData = new FormData();
        formData.append('query', query);
        // the backend uses 'image' or 'after_image' based on the signature
        // Since disaster_analysis accepts: query, image, before_image, after_image
        // For single image, send it as `image`.
        // For comparison, send before_image and after_image.

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
            setError(err.response?.data?.detail || "An error occurred during flood risk analysis.");
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

    const getAnnotatedUrl = () => {
        if (!result?.annotated_image?.generated) return null;
        return getImageUrl(result.annotated_image.path_or_url || result.annotated_image.url);
    };

    return (
        <div className="max-w-7xl mx-auto space-y-6 pb-10">
            <div className="mb-6 flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2 flex items-center">
                        <Waves className="mr-3 text-cyan-400" />
                        Flood Intelligence
                    </h1>
                    <p className="text-slate-400">Identify flooded areas, water expansion parameters, and compute risk levels.</p>
                </div>
            </div>

            <div className="grid grid-cols-1 xl:grid-cols-12 gap-8">
                <div className="xl:col-span-4 space-y-6">
                    <div className="glass-panel p-5 border-t-[3px] border-t-cyan-500">
                        <ImageUploader
                            file={targetFile} setFile={setTargetFile}
                            preview={targetPreview} setPreview={setTargetPreview}
                            label="Target Image (Recent/Post-Flood)"
                        />
                    </div>

                    <div className="glass-panel p-5">
                        <ImageUploader
                            file={baselineFile} setFile={setBaselineFile}
                            preview={baselinePreview} setPreview={setBaselinePreview}
                            label="Baseline Image (Optional Before)"
                        />
                    </div>

                    <div className="glass-panel p-5">
                        <label className="block text-sm font-medium text-slate-400 mb-2">Analysis Query</label>
                        <textarea
                            className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-slate-200 focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 placeholder-slate-600 text-sm resize-none h-24"
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                        />

                        <button
                            onClick={handleAnalyze}
                            disabled={loading || !targetFile || !query.trim()}
                            className="w-full mt-4 bg-cyan-500 hover:bg-cyan-400 text-navy-dark font-bold py-3 px-4 rounded-lg flex items-center justify-center transition-colors shadow-[0_0_20px_rgba(34,211,238,0.2)] disabled:opacity-50 disabled:shadow-none disabled:cursor-not-allowed uppercase tracking-wider text-sm"
                        >
                            {loading ? 'Processing...' : (
                                <>Analyze Flood Risk <Send className="ml-2 w-4 h-4" /></>
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

                <div className="xl:col-span-8">
                    <div className="glass-panel h-full min-h-[700px] flex flex-col relative overflow-hidden">
                        {loading ? (
                            <div className="flex-1 flex items-center justify-center bg-slate-900/50 object-cover backdrop-blur-sm z-10 w-full h-full absolute inset-0">
                                <AnalysisLoader />
                            </div>
                        ) : null}

                        <div className={`p-6 flex flex-col h-full ${loading ? 'opacity-30 blur-sm pointer-events-none' : ''}`}>
                            {!result && !loading ? (
                                <div className="flex-1 flex flex-col items-center justify-center text-slate-500">
                                    <Waves className="w-20 h-20 mb-6 opacity-30" />
                                    <h3 className="text-xl font-medium text-slate-400 mb-2">Awaiting Intelligence Target</h3>
                                    <p className="max-w-md text-center text-sm leading-relaxed">
                                        Upload a post-disaster satellite image (and an optional baseline) to calculate flood segmentation metrics, infrastructure peril, and global risk score.
                                    </p>
                                </div>
                            ) : null}

                            {result && (
                                <div className="animate-in fade-in slide-in-from-bottom-8 duration-700 h-full flex flex-col space-y-6">
                                    {/* Top Header */}
                                    <div className="flex flex-col md:flex-row justify-between shrink-0 gap-4">
                                        <div>
                                            <h2 className="text-xl font-bold tracking-wide uppercase text-slate-200">Disaster Intelligence Report</h2>
                                            <p className="text-xs text-slate-500 tracking-wider">REQ: {result.request_id || "UNKNOWN"}</p>
                                        </div>

                                        <div className={`flex items-center px-6 py-2 rounded-xl text-lg font-bold uppercase tracking-widest border ${getRiskColor(result.risk_assessment?.risk_level)} shadow-lg`}>
                                            <AlertTriangle className="w-5 h-5 mr-3 shrink-0" />
                                            {result.risk_assessment?.risk_level || 'UNKNOWN'} RISK
                                            <span className="ml-4 text-xs font-semibold opacity-70">SCORE: {result.risk_assessment?.risk_score || 0}</span>
                                        </div>
                                    </div>

                                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 flex-1">
                                        {/* Visualizer output block */}
                                        <div className="bg-black/40 border border-slate-800 rounded-xl relative flex flex-col min-h-[300px]">
                                            <div className="absolute top-3 right-3 z-20 flex bg-slate-900/80 backdrop-blur-md rounded-lg p-1 border border-slate-700/50">
                                                <button onClick={() => setShowOriginal(false)} className={`px-3 py-1 text-xs font-medium rounded transition-colors ${!showOriginal ? 'bg-cyan-500/20 text-cyan-400' : 'text-slate-400'}`}>Analysis</button>
                                                <button onClick={() => setShowOriginal(true)} className={`px-3 py-1 text-xs font-medium rounded transition-colors ${showOriginal ? 'bg-slate-700/80 text-white' : 'text-slate-400'}`}>Original</button>
                                            </div>

                                            <div className="flex-1 rounded-xl overflow-hidden flex items-center justify-center p-2">
                                                {getAnnotatedUrl() ? (
                                                    <img
                                                        src={showOriginal ? targetPreview : getAnnotatedUrl()}
                                                        className="max-h-[350px] object-contain rounded transition-opacity duration-500"
                                                        alt="Annotated mask result"
                                                    />
                                                ) : (
                                                    <div className="text-slate-500 text-sm flex flex-col items-center">
                                                        <Target className="w-8 h-8 mb-2 opacity-50" />
                                                        No analysis overlays generated
                                                    </div>
                                                )}
                                            </div>
                                        </div>

                                        {/* Insights Block */}
                                        <div className="flex flex-col space-y-4 max-h-[400px] overflow-y-auto custom-scrollbar pr-2">
                                            {/* Hydro metrics */}
                                            {result.water_analysis && (
                                                <div className="bg-slate-900/80 border border-cyan-900/30 p-4 rounded-xl">
                                                    <h3 className="text-xs uppercase tracking-widest text-cyan-500 font-bold mb-3 flex items-center">
                                                        <Waves className="w-4 h-4 mr-2" /> Hydro Analysis
                                                    </h3>
                                                    <div className="grid grid-cols-2 gap-3 text-sm">
                                                        <div className="bg-slate-800/50 p-2 rounded">
                                                            <div className="text-slate-500 text-xs mb-1">Water Detected</div>
                                                            <div className="text-slate-200 font-medium">{result.water_analysis.water_detected ? 'Yes' : 'No'}</div>
                                                        </div>
                                                        <div className="bg-slate-800/50 p-2 rounded">
                                                            <div className="text-slate-500 text-xs mb-1">Expansion Detected</div>
                                                            <div className="text-slate-200 font-medium">{result.water_analysis.water_expansion_detected ? 'Yes' : 'No'}</div>
                                                        </div>
                                                        <div className="bg-slate-800/50 p-2 rounded col-span-2 flex justify-between">
                                                            <span className="text-slate-500 text-xs">Estimated Expansion %</span>
                                                            <span className="text-cyan-400 font-semibold">{(result.water_analysis.estimated_expansion_percentage || 0).toFixed(1)}%</span>
                                                        </div>
                                                    </div>
                                                </div>
                                            )}

                                            {/* Building Detections */}
                                            {result.potentially_affected_buildings_detail && result.potentially_affected_buildings_detail.length > 0 && (
                                                <div className="bg-slate-900/80 border border-orange-900/30 p-4 rounded-xl">
                                                    <h3 className="text-xs uppercase tracking-widest text-orange-400 font-bold mb-3 flex items-center">
                                                        <Building className="w-4 h-4 mr-2" /> Infrastructure Impact
                                                    </h3>
                                                    <div className="space-y-2">
                                                        {result.potentially_affected_buildings_detail.slice(0, 3).map((b, i) => (
                                                            <div key={i} className="flex justify-between items-center text-xs p-2 bg-slate-800/50 border border-slate-700/50 rounded">
                                                                <span className="text-slate-300 font-medium">{b.description || `Building ${b.id}`}</span>
                                                                <span className="text-orange-400 bg-orange-400/10 px-2 py-0.5 rounded">{b.status || 'At Risk'}</span>
                                                            </div>
                                                        ))}
                                                        {result.potentially_affected_buildings_detail.length > 3 && (
                                                            <div className="text-center text-xs text-slate-500 bg-slate-800/30 p-1 rounded">
                                                                + {result.potentially_affected_buildings_detail.length - 3} more structures flagged
                                                            </div>
                                                        )}
                                                    </div>
                                                </div>
                                            )}

                                            {/* Risk Factors */}
                                            {result.risk_assessment?.risk_factors && result.risk_assessment.risk_factors.length > 0 && (
                                                <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-xl">
                                                    <h3 className="text-xs uppercase tracking-widest text-slate-400 font-bold mb-3">Critical Risk Factors</h3>
                                                    <ul className="space-y-2">
                                                        {result.risk_assessment.risk_factors.map((factor, i) => (
                                                            <li key={i} className="text-sm text-slate-300 leading-snug flex items-start">
                                                                <span className="text-orange-500 mr-2 rounded-full mt-1.5 w-1 h-1 bg-orange-500 shrink-0"></span>
                                                                <span>{factor.factor} <span className="opacity-50 ml-1 text-xs">(+{factor.contribution} pts)</span></span>
                                                            </li>
                                                        ))}
                                                    </ul>
                                                </div>
                                            )}
                                        </div>
                                    </div>

                                    {/* Recommendations Bottom Panes */}
                                    {result.recommendations && result.recommendations.length > 0 && (
                                        <div className="bg-gradient-to-r from-slate-900 to-slate-800 border-l-[4px] border-l-blue-500 p-5 rounded-r-xl shrink-0">
                                            <h3 className="text-xs uppercase tracking-widest text-blue-400 font-bold mb-3">Strategic Recommendations</h3>
                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                                {result.recommendations.map((rec, idx) => (
                                                    <div key={idx} className="flex items-start bg-black/20 p-3 rounded-lg border border-slate-700/50">
                                                        <div className="w-5 h-5 rounded-full bg-blue-500/20 text-blue-400 flex items-center justify-center text-xs font-bold shrink-0 mr-3 mt-0.5">{idx + 1}</div>
                                                        <p className="text-sm text-slate-300">{rec}</p>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default FloodIntelligence;
