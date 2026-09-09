import React, { useState } from 'react';
import ImageUploader from '../components/ImageUploader';
import AnalysisLoader from '../components/AnalysisLoader';
import {
    Send, AlertCircle, Mountain, AlertTriangle, TrendingDown,
    BarChart2, Layers, Shield, MapPin, Activity, CheckCircle, XCircle
} from 'lucide-react';
import api, { getImageUrl } from '../services/api';

const LandslideIntelligence = () => {
    // --- Image state ---
    const [singleFile, setSingleFile] = useState(null);
    const [singlePreview, setSinglePreview] = useState(null);
    const [beforeFile, setBeforeFile] = useState(null);
    const [beforePreview, setBeforePreview] = useState(null);
    const [afterFile, setAfterFile] = useState(null);
    const [afterPreview, setAfterPreview] = useState(null);

    // --- Mode: 'single' | 'temporal' ---
    const [mode, setMode] = useState('single');

    const [query, setQuery] = useState('Detect landslide activity, terrain changes and landslide risk in this area.');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [result, setResult] = useState(null);
    const [showOriginal, setShowOriginal] = useState(false);

    // ─── Handlers ────────────────────────────────────────────────────────────

    const handleAnalyze = async () => {
        const hasSingle = singleFile !== null;
        const hasTemporal = beforeFile !== null && afterFile !== null;

        if (!hasSingle && !hasTemporal) {
            setError('Please upload at least one satellite image.');
            return;
        }
        if (mode === 'temporal' && (!beforeFile || !afterFile)) {
            setError('Temporal mode requires both a "Before" and an "After" image.');
            return;
        }

        setError(null);
        setLoading(true);
        setResult(null);
        setShowOriginal(false);

        const formData = new FormData();
        formData.append('query', query);

        if (mode === 'temporal') {
            formData.append('before_image', beforeFile);
            formData.append('after_image', afterFile);
        } else {
            formData.append('image', singleFile);
        }

        try {
            const res = await api.post('/api/disaster/landslide/analyze', formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
            });
            setResult(res.data);
        } catch (err) {
            console.error(err);
            setError(err.response?.data?.detail || 'An error occurred during landslide analysis.');
        } finally {
            setLoading(false);
        }
    };

    // ─── Helpers ─────────────────────────────────────────────────────────────

    const getRiskColor = (level) => {
        if (!level) return 'text-slate-400 bg-slate-800/50 border-slate-700';
        switch (level.toUpperCase()) {
            case 'CRITICAL': return 'text-red-400 bg-red-500/10 border-red-500/30';
            case 'HIGH': return 'text-orange-400 bg-orange-500/10 border-orange-500/30';
            case 'MODERATE': return 'text-yellow-400 bg-yellow-400/10 border-yellow-400/30';
            case 'LOW': return 'text-green-400 bg-green-400/10 border-green-400/30';
            default: return 'text-slate-400 bg-slate-800/50 border-slate-700';
        }
    };

    const getDetectionBadge = (status) => {
        switch ((status || '').toUpperCase()) {
            case 'DETECTED': return 'text-red-400 bg-red-500/10 border-red-500/30';
            case 'POSSIBLE': return 'text-orange-400 bg-orange-500/10 border-orange-500/30';
            case 'INCONCLUSIVE': return 'text-yellow-400 bg-yellow-400/10 border-yellow-400/30';
            case 'NOT_DETECTED': return 'text-green-400 bg-green-400/10 border-green-400/30';
            default: return 'text-slate-400 bg-slate-800 border-slate-700';
        }
    };

    const getAnnotatedUrl = () => {
        if (!result?.annotated_image?.generated) return null;
        return getImageUrl(result.annotated_image.path_or_url || result.annotated_image.url);
    };

    const currentPreview = mode === 'temporal' ? afterPreview : singlePreview;

    // ─── Render ───────────────────────────────────────────────────────────────

    return (
        <div className="max-w-7xl mx-auto space-y-6 pb-10">

            {/* ── Page header ─────────────────────────────────────────────── */}
            <div className="mb-4">
                <h1 className="text-3xl font-bold text-white mb-2 flex items-center">
                    <Mountain className="mr-3 text-orange-400" />
                    Landslide Risk Intelligence
                </h1>
                <p className="text-slate-400">
                    Satellite-based terrain disturbance detection, bare-soil analysis,
                    and multi-factor landslide risk scoring.
                </p>
            </div>

            <div className="grid grid-cols-1 xl:grid-cols-12 gap-8">

                {/* ── Left control panel ──────────────────────────────────── */}
                <div className="xl:col-span-4 space-y-5">

                    {/* Mode toggle */}
                    <div className="glass-panel p-4">
                        <label className="block text-xs font-bold uppercase tracking-widest text-slate-400 mb-3">
                            Analysis Mode
                        </label>
                        <div className="flex bg-slate-900 rounded-xl p-1 gap-1">
                            <button
                                onClick={() => setMode('single')}
                                className={`flex-1 py-2 rounded-lg text-sm font-semibold transition-all ${mode === 'single' ? 'bg-orange-500/20 text-orange-300 border border-orange-500/30' : 'text-slate-400 hover:text-slate-200'}`}
                            >
                                Single Image
                            </button>
                            <button
                                onClick={() => setMode('temporal')}
                                className={`flex-1 py-2 rounded-lg text-sm font-semibold transition-all ${mode === 'temporal' ? 'bg-orange-500/20 text-orange-300 border border-orange-500/30' : 'text-slate-400 hover:text-slate-200'}`}
                            >
                                Before / After
                            </button>
                        </div>
                    </div>

                    {/* Image upload(s) */}
                    {mode === 'single' ? (
                        <div className="glass-panel p-5 border-t-[3px] border-t-orange-500/60">
                            <ImageUploader
                                file={singleFile} setFile={setSingleFile}
                                preview={singlePreview} setPreview={setSinglePreview}
                                label="Satellite Image"
                            />
                        </div>
                    ) : (
                        <>
                            <div className="glass-panel p-5 border-t-[3px] border-t-slate-600">
                                <ImageUploader
                                    file={beforeFile} setFile={setBeforeFile}
                                    preview={beforePreview} setPreview={setBeforePreview}
                                    label="Before Image (Baseline)"
                                />
                            </div>
                            <div className="glass-panel p-5 border-t-[3px] border-t-orange-500/60">
                                <ImageUploader
                                    file={afterFile} setFile={setAfterFile}
                                    preview={afterPreview} setPreview={setAfterPreview}
                                    label="After Image (Recent)"
                                />
                            </div>
                        </>
                    )}

                    {/* Query & submit */}
                    <div className="glass-panel p-5">
                        <label className="block text-sm font-medium text-slate-400 mb-2">
                            Analysis Query
                        </label>
                        <textarea
                            className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-slate-200 focus:outline-none focus:border-orange-500/50 focus:ring-1 focus:ring-orange-500/30 placeholder-slate-600 text-sm resize-none h-24"
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                        />

                        <button
                            onClick={handleAnalyze}
                            disabled={loading || !query.trim()}
                            className="w-full mt-4 bg-gradient-to-r from-orange-600 to-red-600 hover:from-orange-500 hover:to-red-500 text-white font-bold py-3 px-4 rounded-lg flex items-center justify-center transition-all shadow-[0_0_20px_rgba(234,88,12,0.3)] disabled:opacity-40 disabled:shadow-none disabled:cursor-not-allowed uppercase tracking-wider text-sm"
                        >
                            {loading ? 'Analyzing…' : (
                                <><Mountain className="mr-2 w-4 h-4" /> Analyze Landslide Risk</>
                            )}
                        </button>

                        {error && (
                            <div className="mt-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg flex items-start text-red-400 text-sm">
                                <AlertCircle className="w-5 h-5 mr-2 shrink-0" />
                                <span>{error}</span>
                            </div>
                        )}
                    </div>

                    {/* Data transparency card */}
                    <div className="glass-panel p-4 border border-amber-800/30 bg-amber-900/10">
                        <div className="flex items-start gap-2">
                            <Shield className="w-4 h-4 text-amber-400 mt-0.5 shrink-0" />
                            <div>
                                <p className="text-xs font-bold text-amber-400 uppercase tracking-wide mb-1">
                                    Data Transparency
                                </p>
                                <p className="text-xs text-amber-200/70 leading-relaxed">
                                    Analysis uses spectral heuristics + AI visual reasoning.
                                    No dedicated landslide segmentation model is deployed.
                                    DEM/slope data unavailable. Ground verification always required.
                                </p>
                            </div>
                        </div>
                    </div>
                </div>

                {/* ── Right result panel ──────────────────────────────────── */}
                <div className="xl:col-span-8">
                    <div className="glass-panel min-h-[700px] flex flex-col relative overflow-hidden">

                        {loading && (
                            <div className="flex-1 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm z-10 absolute inset-0">
                                <AnalysisLoader />
                            </div>
                        )}

                        <div className={`p-6 flex flex-col h-full ${loading ? 'opacity-30 blur-sm pointer-events-none' : ''}`}>

                            {/* Placeholder */}
                            {!result && !loading && (
                                <div className="flex-1 flex flex-col items-center justify-center text-slate-500">
                                    <Mountain className="w-20 h-20 mb-6 opacity-20 text-orange-500" />
                                    <h3 className="text-xl font-medium text-slate-400 mb-2">
                                        Landslide Intelligence Awaiting
                                    </h3>
                                    <p className="max-w-md text-center text-sm leading-relaxed">
                                        Upload satellite imagery to detect terrain disturbances,
                                        bare-soil exposure, vegetation loss, and landslide risk indicators.
                                    </p>
                                </div>
                            )}

                            {result && (
                                <div className="animate-in fade-in slide-in-from-bottom-8 duration-700 space-y-6">

                                    {/* ── Status header ──────────────────────────────────── */}
                                    <div className="flex flex-col md:flex-row justify-between items-start gap-4">
                                        <div>
                                            <h2 className="text-xl font-bold tracking-wide uppercase text-slate-200">
                                                Landslide Risk Report
                                            </h2>
                                            <p className="text-xs text-slate-500 tracking-wider mt-0.5">
                                                REQ: {result.request_id || 'UNKNOWN'}
                                                {result.processing_time_seconds !== undefined && (
                                                    <span className="ml-3 opacity-60">
                                                        ⏱ {result.processing_time_seconds}s
                                                    </span>
                                                )}
                                            </p>
                                        </div>

                                        {/* Big risk badge */}
                                        <div className={`flex items-center px-5 py-2.5 rounded-xl text-base font-bold uppercase tracking-widest border ${getRiskColor(result.risk_assessment?.risk_level)} shadow-lg shrink-0`}>
                                            <AlertTriangle className="w-4 h-4 mr-2 shrink-0" />
                                            {result.risk_assessment?.risk_level || 'UNKNOWN'} RISK
                                            <span className="ml-3 text-xs font-semibold opacity-70">
                                                {result.risk_assessment?.risk_score ?? 0}/100
                                            </span>
                                        </div>
                                    </div>

                                    {/* ── Key metrics grid ──────────────────────────────── */}
                                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                                        {/* Detection Status */}
                                        <div className={`p-3 rounded-xl border ${getDetectionBadge(result.detection_status)} flex flex-col gap-1`}>
                                            <span className="text-xs opacity-60 uppercase tracking-wide">Status</span>
                                            <span className="font-bold text-sm">
                                                {(result.detection_status || 'UNKNOWN').replace(/_/g, ' ')}
                                            </span>
                                        </div>

                                        {/* Confidence */}
                                        <div className="p-3 rounded-xl border border-slate-700 bg-slate-900/60 flex flex-col gap-1">
                                            <span className="text-xs text-slate-500 uppercase tracking-wide">Confidence</span>
                                            <span className="font-bold text-slate-200 text-sm">
                                                {Math.round((result.risk_assessment?.confidence || 0) * 100)}%
                                            </span>
                                        </div>

                                        {/* Affected Area */}
                                        <div className="p-3 rounded-xl border border-slate-700 bg-slate-900/60 flex flex-col gap-1">
                                            <span className="text-xs text-slate-500 uppercase tracking-wide">Disturbed Area</span>
                                            <span className="font-bold text-orange-400 text-sm">
                                                {(result.landslide_assessment?.affected_area_percentage || 0).toFixed(1)}%
                                            </span>
                                        </div>

                                        {/* Change Detected */}
                                        <div className="p-3 rounded-xl border border-slate-700 bg-slate-900/60 flex flex-col gap-1">
                                            <span className="text-xs text-slate-500 uppercase tracking-wide">Change</span>
                                            <span className={`font-bold text-sm ${result.change_analysis?.change_detected ? 'text-orange-400' : 'text-green-400'}`}>
                                                {result.change_analysis?.change_detected ? 'DETECTED' : 'NONE'}
                                            </span>
                                        </div>
                                    </div>

                                    {/* ── Main 2-col layout ─────────────────────────────── */}
                                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">

                                        {/* Annotated image viewer */}
                                        <div className="bg-black/30 border border-slate-800 rounded-xl relative flex flex-col min-h-[280px]">
                                            {/* Toggle */}
                                            <div className="absolute top-3 right-3 z-20 flex bg-slate-900/80 backdrop-blur-md rounded-lg p-1 border border-slate-700/50">
                                                <button
                                                    onClick={() => setShowOriginal(false)}
                                                    className={`px-3 py-1 text-xs font-medium rounded transition-colors ${!showOriginal ? 'bg-orange-600/60 text-white' : 'text-slate-400'}`}
                                                >
                                                    Analysis
                                                </button>
                                                <button
                                                    onClick={() => setShowOriginal(true)}
                                                    className={`px-3 py-1 text-xs font-medium rounded transition-colors ${showOriginal ? 'bg-slate-700/80 text-white' : 'text-slate-400'}`}
                                                >
                                                    Original
                                                </button>
                                            </div>

                                            <div className="flex-1 rounded-xl overflow-hidden flex items-center justify-center p-3">
                                                {getAnnotatedUrl() || currentPreview ? (
                                                    <img
                                                        src={showOriginal ? currentPreview : (getAnnotatedUrl() || currentPreview)}
                                                        className="max-h-[300px] object-contain rounded transition-opacity duration-500"
                                                        alt="Landslide analysis"
                                                    />
                                                ) : (
                                                    <div className="text-slate-500 text-sm flex flex-col items-center">
                                                        <Mountain className="w-8 h-8 mb-2 opacity-30" />
                                                        No analysis overlay generated
                                                    </div>
                                                )}
                                            </div>

                                            {result.annotated_image?.generated && (
                                                <div className="absolute bottom-3 left-3 text-xs text-orange-400/70 bg-black/40 px-2 py-1 rounded">
                                                    🟠 Orange = candidate region
                                                </div>
                                            )}
                                        </div>

                                        {/* Landslide Details */}
                                        <div className="space-y-4 max-h-[380px] overflow-y-auto custom-scrollbar pr-1">

                                            {/* Detection breakdown */}
                                            <div className="bg-slate-900/70 border border-orange-900/30 p-4 rounded-xl">
                                                <h3 className="text-xs uppercase tracking-widest text-orange-400 font-bold mb-3 flex items-center">
                                                    <Activity className="w-3.5 h-3.5 mr-2" /> Landslide Assessment
                                                </h3>
                                                <div className="grid grid-cols-2 gap-2 text-sm">
                                                    <div className="bg-slate-800/50 p-2 rounded">
                                                        <div className="text-slate-500 text-xs mb-1">Bare Soil</div>
                                                        <div className="text-slate-200 font-medium">
                                                            {(result.landslide_assessment?.bare_soil_percentage || 0).toFixed(1)}%
                                                        </div>
                                                    </div>
                                                    <div className="bg-slate-800/50 p-2 rounded">
                                                        <div className="text-slate-500 text-xs mb-1">Vegetation</div>
                                                        <div className="text-green-400 font-medium">
                                                            {(result.landslide_assessment?.vegetation_percentage || 0).toFixed(1)}%
                                                        </div>
                                                    </div>
                                                    <div className="bg-slate-800/50 p-2 rounded col-span-2 flex justify-between">
                                                        <span className="text-slate-500 text-xs">Model Label</span>
                                                        <span className="text-orange-300 font-mono text-xs">
                                                            {result.landslide_assessment?.model_label || 'N/A'}
                                                        </span>
                                                    </div>
                                                    <div className="bg-slate-800/50 p-2 rounded col-span-2 flex justify-between">
                                                        <span className="text-slate-500 text-xs">Data Source</span>
                                                        <span className="text-slate-300 font-mono text-xs">
                                                            {result.landslide_assessment?.data_source || 'N/A'}
                                                        </span>
                                                    </div>
                                                </div>
                                            </div>

                                            {/* Change analysis */}
                                            {result.change_analysis && (
                                                <div className={`bg-slate-900/70 border ${result.change_analysis.change_detected ? 'border-orange-800/40' : 'border-slate-800'} p-4 rounded-xl`}>
                                                    <h3 className="text-xs uppercase tracking-widest text-amber-400 font-bold mb-3 flex items-center">
                                                        <TrendingDown className="w-3.5 h-3.5 mr-2" /> Change Analysis
                                                    </h3>
                                                    <div className="grid grid-cols-2 gap-2 text-sm">
                                                        <div className="bg-slate-800/50 p-2 rounded col-span-2 flex justify-between">
                                                            <span className="text-slate-500 text-xs">Change Type</span>
                                                            <span className={`font-medium text-xs ${result.change_analysis.change_detected ? 'text-orange-400' : 'text-slate-400'}`}>
                                                                {result.change_analysis.change_type?.replace(/_/g, ' ') || 'None Detected'}
                                                            </span>
                                                        </div>
                                                        {result.change_analysis.change_detected && (
                                                            <>
                                                                <div className="bg-slate-800/50 p-2 rounded flex justify-between">
                                                                    <span className="text-slate-500 text-xs">Surface Δ</span>
                                                                    <span className="text-orange-300 text-xs font-semibold">
                                                                        {(result.change_analysis.estimated_change_percentage || 0).toFixed(1)}%
                                                                    </span>
                                                                </div>
                                                                <div className="bg-slate-800/50 p-2 rounded flex justify-between">
                                                                    <span className="text-slate-500 text-xs">Veg. Loss</span>
                                                                    <span className="text-yellow-400 text-xs font-semibold">
                                                                        {(result.change_analysis.vegetation_loss_percentage || 0).toFixed(1)}%
                                                                    </span>
                                                                </div>
                                                            </>
                                                        )}
                                                    </div>
                                                </div>
                                            )}

                                            {/* AI Visual Assessment */}
                                            {result.ai_visual_assessment && (
                                                <div className="bg-slate-900/70 border border-indigo-900/30 p-4 rounded-xl">
                                                    <h3 className="text-xs uppercase tracking-widest text-indigo-400 font-bold mb-2 flex items-center">
                                                        <Layers className="w-3.5 h-3.5 mr-2" /> AI Visual Reasoning
                                                    </h3>
                                                    {result.ai_visual_assessment.available ? (
                                                        <>
                                                            <p className="text-xs text-slate-400 mb-2 italic">
                                                                Model: {result.ai_visual_assessment.model}
                                                            </p>
                                                            <p className="text-xs text-slate-300 leading-relaxed max-h-28 overflow-y-auto custom-scrollbar">
                                                                {result.ai_visual_assessment.reasoning}
                                                            </p>
                                                            <p className="text-[10px] text-indigo-400/60 mt-2">
                                                                {result.ai_visual_assessment.note}
                                                            </p>
                                                        </>
                                                    ) : (
                                                        <p className="text-xs text-slate-500 italic">
                                                            {result.ai_visual_assessment.note}
                                                        </p>
                                                    )}
                                                </div>
                                            )}
                                        </div>
                                    </div>

                                    {/* ── Risk Factors ──────────────────────────────────── */}
                                    {result.risk_assessment?.risk_factors?.length > 0 && (
                                        <div className="bg-slate-900/70 border border-slate-800 p-5 rounded-xl">
                                            <h3 className="text-xs uppercase tracking-widest text-slate-400 font-bold mb-3 flex items-center">
                                                <BarChart2 className="w-4 h-4 mr-2 text-orange-400" /> Risk Factors
                                            </h3>
                                            <div className="space-y-2">
                                                {result.risk_assessment.risk_factors.map((f, i) => (
                                                    <div key={i} className="flex items-start justify-between gap-4 bg-black/20 p-3 rounded-lg border border-slate-700/40">
                                                        <div className="flex-1">
                                                            <p className="text-sm text-slate-300">{f.factor}</p>
                                                            {f.source && (
                                                                <p className="text-[10px] text-slate-500 mt-0.5">
                                                                    Source: {f.source}
                                                                </p>
                                                            )}
                                                        </div>
                                                        <div className="text-right shrink-0">
                                                            <div className="text-orange-400 font-bold text-sm">+{f.contribution}</div>
                                                            {f.evidence_confidence != null && (
                                                                <div className="text-xs text-slate-500">
                                                                    conf: {(f.evidence_confidence * 100).toFixed(0)}%
                                                                </div>
                                                            )}
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {/* ── Infrastructure Impact ─────────────────────────── */}
                                    {result.potential_impact && (
                                        <div className="bg-slate-900/70 border border-slate-800 p-5 rounded-xl">
                                            <h3 className="text-xs uppercase tracking-widest text-slate-400 font-bold mb-3 flex items-center">
                                                <MapPin className="w-4 h-4 mr-2 text-orange-400" /> Potential Infrastructure Impact
                                            </h3>
                                            <div className="grid grid-cols-3 gap-3 text-sm mb-3">
                                                <div className="bg-slate-800/50 p-3 rounded text-center">
                                                    <div className="text-slate-500 text-xs mb-1">Buildings</div>
                                                    <div className="text-slate-200 font-bold text-lg">
                                                        {result.potential_impact.potentially_affected_buildings ?? '—'}
                                                    </div>
                                                </div>
                                                <div className="bg-slate-800/50 p-3 rounded text-center">
                                                    <div className="text-slate-500 text-xs mb-1">Roads</div>
                                                    <div className="text-slate-200 font-bold text-lg">
                                                        {result.potential_impact.potentially_affected_roads ?? '—'}
                                                    </div>
                                                </div>
                                                <div className="bg-slate-800/50 p-3 rounded text-center">
                                                    <div className="text-slate-500 text-xs mb-1">Analysis</div>
                                                    <div className="text-slate-300 text-xs font-medium">
                                                        {result.potential_impact.infrastructure_analysis}
                                                    </div>
                                                </div>
                                            </div>
                                            {result.potential_impact.note && (
                                                <p className="text-xs text-slate-500 italic">
                                                    {result.potential_impact.note}
                                                </p>
                                            )}
                                        </div>
                                    )}

                                    {/* ── Terrain + SAR evidence ────────────────────────── */}
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        <div className="bg-slate-900/60 border border-slate-800 p-4 rounded-xl">
                                            <h3 className="text-xs uppercase tracking-widest text-slate-500 font-bold mb-2">
                                                🏔️ Terrain / DEM Evidence
                                            </h3>
                                            <p className="text-xs text-slate-400">
                                                {result.terrain_evidence?.slope_analysis || 'Terrain elevation evidence unavailable.'}
                                            </p>
                                            <p className="text-[10px] text-slate-500 mt-1">
                                                {result.terrain_evidence?.note}
                                            </p>
                                        </div>
                                        <div className="bg-slate-900/60 border border-slate-800 p-4 rounded-xl">
                                            <h3 className="text-xs uppercase tracking-widest text-slate-500 font-bold mb-2">
                                                📡 Sentinel-1 / SAR Evidence
                                            </h3>
                                            <p className="text-xs text-slate-400">
                                                {result.sar_evidence?.note || 'SAR data unavailable.'}
                                            </p>
                                        </div>
                                    </div>

                                    {/* ── AI Disclaimer ─────────────────────────────────── */}
                                    {result.risk_assessment?.ai_disclaimer && (
                                        <div className="flex items-start gap-3 bg-red-900/10 border border-red-700/30 p-4 rounded-xl">
                                            <AlertTriangle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
                                            <p className="text-sm text-red-300">
                                                {result.risk_assessment.ai_disclaimer}
                                            </p>
                                        </div>
                                    )}

                                    {/* ── Recommendations ───────────────────────────────── */}
                                    {result.recommendations?.length > 0 && (
                                        <div className="bg-gradient-to-r from-slate-900 to-slate-800 border-l-[4px] border-l-orange-500 p-5 rounded-r-xl">
                                            <h3 className="text-xs uppercase tracking-widest text-orange-400 font-bold mb-3">
                                                Response Recommendations
                                            </h3>
                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                                                {result.recommendations.map((rec, idx) => (
                                                    <div key={idx} className="flex items-start bg-black/20 p-3 rounded-lg border border-slate-700/40">
                                                        <AlertCircle className="w-3.5 h-3.5 text-orange-400 mr-2 shrink-0 mt-0.5" />
                                                        <p className="text-sm text-slate-300">{rec}</p>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {/* ── Limitations ───────────────────────────────────── */}
                                    {result.limitations?.length > 0 && (
                                        <details className="group">
                                            <summary className="cursor-pointer text-xs text-slate-500 uppercase tracking-wide hover:text-slate-300 transition-colors select-none">
                                                ℹ️ Analysis Limitations & Disclosures ({result.limitations.length})
                                            </summary>
                                            <ul className="mt-2 space-y-1 pl-4">
                                                {result.limitations.map((lim, i) => (
                                                    <li key={i} className="text-xs text-slate-500 leading-relaxed flex items-start">
                                                        <span className="mr-2 text-slate-600">•</span>{lim}
                                                    </li>
                                                ))}
                                            </ul>
                                        </details>
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

export default LandslideIntelligence;
