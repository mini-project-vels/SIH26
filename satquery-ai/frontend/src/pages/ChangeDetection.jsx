import React, { useState } from 'react';
import ImageUploader from '../components/ImageUploader';
import { Send, AlertCircle, RefreshCcw, ArrowRight, Layers, Target, Eye, Database } from 'lucide-react';
import api from '../services/api';

const ChangeDetection = () => {
    const [beforeFile, setBeforeFile] = useState(null);
    const [beforePreview, setBeforePreview] = useState(null);
    const [afterFile, setAfterFile] = useState(null);
    const [afterPreview, setAfterPreview] = useState(null);
    const [target, setTarget] = useState('general');

    const [loadingStage, setLoadingStage] = useState(0);
    const [stepContext, setStepContext] = useState('');
    const [error, setError] = useState(null);
    const [result, setResult] = useState(null);

    const [activeTab, setActiveTab] = useState('overlay'); // overlay, diff, original

    const handleAnalyze = async () => {
        if (!beforeFile || !afterFile) {
            setError("Please provide both before and after images.");
            return;
        }

        setError(null);
        setLoadingStage(1);
        setStepContext('IMAGE NORMALIZATION & ALIGNMENT');
        setResult(null);

        let t1, t2, t3;
        try {
            const formData = new FormData();
            formData.append('before_image', beforeFile);
            formData.append('after_image', afterFile);
            formData.append('analysis_target', target);

            t1 = setTimeout(() => { setLoadingStage(2); setStepContext('MULTI-METHOD CHANGE ANALYSIS\n(SSIM & Absolute Diff)'); }, 1000);
            t2 = setTimeout(() => { setLoadingStage(3); setStepContext('NOISE FILTERING & CONNECTED COMPONENTS\n(Removing speckle topology)'); }, 2500);
            t3 = setTimeout(() => { setLoadingStage(4); setStepContext('SIGNIFICANT CHANGE REGIONS\n(Extracting boundaries)'); }, 4000);

            const response = await api.post('/api/change-detection/analyze', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            setResult(response.data);
            setActiveTab('overlay');
        } catch (err) {
            console.error(err);
            setError(err.response?.data?.detail || "An error occurred during change detection analysis.");
        } finally {
            clearTimeout(t1); clearTimeout(t2); clearTimeout(t3);
            setLoadingStage(0);
        }
    };

    return (
        <div className="max-w-7xl mx-auto space-y-6 animate-in fade-in zoom-in-95 duration-500">
            <div className="mb-8 border-b border-ocean-800 pb-6">
                <h1 className="text-3xl font-bold text-white mb-2 flex items-center">
                    <Layers className="mr-3 text-ocean-500" /> Automated Change Detection Engine
                </h1>
                <p className="text-ocean-200">Automatically isolate geographical damage topologies using multi-method mathematical verification.</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                {/* Inputs Setup */}
                <div className="lg:col-span-4 space-y-6">
                    <div className="bg-ocean-950/60 p-5 rounded-2xl border border-ocean-800 backdrop-blur-md">
                        <ImageUploader
                            file={beforeFile} setFile={setBeforeFile}
                            preview={beforePreview} setPreview={setBeforePreview}
                            label="Before Spatial Image (Baseline)"
                        />
                    </div>
                    <div className="bg-ocean-950/60 p-5 rounded-2xl border border-ocean-800 backdrop-blur-md">
                        <ImageUploader
                            file={afterFile} setFile={setAfterFile}
                            preview={afterPreview} setPreview={setAfterPreview}
                            label="After Spatial Image (Target)"
                        />
                    </div>
                    <div className="bg-ocean-950/60 p-5 rounded-2xl border border-ocean-800 backdrop-blur-md shadow-xl">
                        <label className="block text-xs font-bold text-ocean-500 uppercase tracking-widest mb-3">Intelligence Target Routing</label>
                        <select
                            className="w-full bg-ocean-900 border border-ocean-700 rounded-lg p-3 text-ocean-100 mb-4 text-sm focus:outline-none focus:border-ocean-400"
                            value={target} onChange={(e) => setTarget(e.target.value)}
                        >
                            <option value="general">Global Detection</option>
                            <option value="flood">Flood Routing / Water Expand</option>
                            <option value="glacier">Glacier / Avalanche Routing</option>
                            <option value="landslide">Rockslide / Landmass Routing</option>
                        </select>

                        <button
                            onClick={handleAnalyze}
                            disabled={loadingStage > 0 || !beforeFile || !afterFile}
                            className="w-full bg-gradient-to-r from-ocean-600 to-ocean-500 hover:from-ocean-500 hover:to-ocean-400 text-white font-bold tracking-widest text-sm uppercase py-4 rounded-xl flex items-center justify-center transition-all disabled:opacity-50 shadow-lg shadow-ocean-500/20 hover:-translate-y-1"
                        >
                            {loadingStage > 0 ? (
                                <>Processing Data Pipeline ...</>
                            ) : (
                                <>🚀 Detect Core Changes</>
                            )}
                        </button>

                        {error && (
                            <div className="mt-4 p-4 bg-red-500/10 border border-red-500/30 rounded-lg flex items-start text-red-400 text-xs">
                                <AlertCircle className="w-5 h-5 mr-2 shrink-0" />
                                <span>{error}</span>
                            </div>
                        )}
                    </div>
                </div>

                {/* Processing Results Display */}
                <div className="lg:col-span-8 flex flex-col items-center">
                    {loadingStage > 0 && (
                        <div className="w-full min-h-[500px] flex flex-col items-center justify-center bg-ocean-950/40 border border-ocean-800 rounded-2xl p-8 backdrop-blur-md">
                            <Layers className={`w-16 h-16 text-ocean-500 mb-8 ${loadingStage === 2 ? 'animate-bounce' : 'animate-pulse'}`} />
                            <div className="w-full max-w-md bg-ocean-900 rounded-full h-3 mb-4 border border-ocean-800 overflow-hidden">
                                <div className="bg-ocean-400 h-full rounded-full transition-all duration-700 ease-in-out relative" style={{ width: `${(loadingStage / 4) * 100}%` }}>
                                    <div className="absolute top-0 right-0 bottom-0 left-0 bg-[linear-gradient(45deg,transparent_25%,rgba(255,255,255,0.2)_50%,transparent_75%,transparent_100%)] bg-[length:1rem_1rem] animate-[progress_1s_linear_infinite]"></div>
                                </div>
                            </div>
                            <div className="text-sm font-bold text-center text-ocean-300 tracking-widest whitespace-pre-wrap leading-relaxed">{stepContext}</div>
                        </div>
                    )}

                    {loadingStage === 0 && result && (
                        <div className="w-full bg-ocean-950/40 backdrop-blur-xl border border-ocean-800 p-6 rounded-2xl animate-in fade-in slide-in-from-bottom-4 duration-500">

                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                                <div className={`p-4 rounded-xl border ${result.change_detected ? 'bg-rose-950/50 border-rose-500/50' : 'bg-emerald-950/50 border-emerald-500/50'}`}>
                                    <p className="text-[10px] text-ocean-200 uppercase tracking-widest font-bold mb-1 opacity-70">Detection Status</p>
                                    <p className={`font-black text-sm uppercase tracking-wide ${result.change_detected ? 'text-rose-400' : 'text-emerald-400'}`}>
                                        {result.change_detected ? 'Change Detected' : 'No Major Change'}
                                    </p>
                                </div>
                                <div className="bg-ocean-900/60 p-4 rounded-xl border border-ocean-800 flex flex-col justify-center">
                                    <p className="text-[10px] text-ocean-200 uppercase tracking-widest font-bold mb-1 opacity-70">Impact Volume</p>
                                    <p className="text-white font-bold">{result.overall_change_percentage}% Spatial</p>
                                </div>
                                <div className="bg-ocean-900/60 p-4 rounded-xl border border-ocean-800 flex flex-col justify-center">
                                    <p className="text-[10px] text-ocean-200 uppercase tracking-widest font-bold mb-1 opacity-70">Significant Regions (CC)</p>
                                    <p className="text-white font-bold">{result.significant_regions.length} Nodes</p>
                                </div>
                                <div className="bg-ocean-900/60 p-4 rounded-xl border border-ocean-800 flex flex-col justify-center">
                                    <p className="text-[10px] text-ocean-200 uppercase tracking-widest font-bold mb-1 opacity-70">Change Intensity</p>
                                    <p className={`font-bold ${result.change_intensity === 'CRITICAL' ? 'text-red-500' : result.change_intensity === 'HIGH' ? 'text-orange-400' : 'text-emerald-400'}`}>{result.change_intensity}</p>
                                </div>
                            </div>

                            <div className="flex space-x-2 mb-4 bg-ocean-950 border border-ocean-800 rounded-lg p-1 w-fit">
                                <button onClick={() => setActiveTab('overlay')} className={`px-4 py-1.5 rounded-md text-xs font-bold uppercase tracking-wide transition-all ${activeTab === 'overlay' ? 'bg-ocean-600 text-white shadow-lg' : 'text-ocean-400 hover:text-white hover:bg-ocean-800'}`}>Final Overlay</button>
                                <button onClick={() => setActiveTab('diff')} className={`px-4 py-1.5 rounded-md text-xs font-bold uppercase tracking-wide transition-all ${activeTab === 'diff' ? 'bg-ocean-600 text-white shadow-lg' : 'text-ocean-400 hover:text-white hover:bg-ocean-800'}`}>Raw Difference Filter</button>
                                <button onClick={() => setActiveTab('original')} className={`px-4 py-1.5 rounded-md text-xs font-bold uppercase tracking-wide transition-all ${activeTab === 'original' ? 'bg-ocean-600 text-white shadow-lg' : 'text-ocean-400 hover:text-white hover:bg-ocean-800'}`}>Source Imagery</button>
                            </div>

                            <div className="bg-[#050811] rounded-xl overflow-hidden border border-ocean-900 min-h-[300px] mb-6 flex justify-center items-center relative object-contain">
                                {activeTab === 'overlay' && (
                                    <>
                                        <div className="absolute top-4 left-4 bg-black/60 backdrop-blur-sm border border-red-500/50 text-red-100 text-xs px-3 py-1.5 rounded-md z-10 flex items-center font-bold tracking-widest uppercase">
                                            <Target className="w-4 h-4 mr-2 text-rose-500" /> Analytical Target Impact Vectors
                                        </div>
                                        <img src={`http://localhost:8000/${result.visualizations.overlay}?req=x`} alt="Change Overlay" className="w-full h-[380px] object-contain" />
                                    </>
                                )}
                                {activeTab === 'diff' && (
                                    <>
                                        <div className="absolute top-4 left-4 bg-black/60 backdrop-blur-sm border border-ocean-500/50 text-ocean-100 text-xs px-3 py-1.5 rounded-md z-10 flex items-center font-bold tracking-widest uppercase">
                                            <Database className="w-4 h-4 mr-2" /> Unfiltered SSIM Map
                                        </div>
                                        <img src={`http://localhost:8000/${result.visualizations.difference_map}?req=x`} alt="Diff Map" className="w-full h-[380px] object-contain filter " />
                                    </>
                                )}
                                {activeTab === 'original' && (
                                    <div className="flex w-full h-[380px]">
                                        <div className="w-1/2 border-r border-ocean-800 relative">
                                            <span className="absolute bottom-4 left-4 bg-black/60 text-xs text-white px-2 py-1 rounded">Before</span>
                                            <img src={`http://localhost:8000/${result.visualizations.before}?req=x`} className="w-full h-full object-contain" />
                                        </div>
                                        <div className="w-1/2 relative">
                                            <span className="absolute bottom-4 left-4 bg-black/60 text-xs text-white px-2 py-1 rounded">After</span>
                                            <img src={`http://localhost:8000/${result.visualizations.after}?req=x`} className="w-full h-full object-contain" />
                                        </div>
                                    </div>
                                )}
                            </div>

                            <div className="bg-ocean-950/80 p-5 rounded-xl border border-ocean-800">
                                <h3 className="text-xs font-bold uppercase tracking-widest text-ocean-300 mb-3 border-b border-ocean-800/50 pb-2">Significant Region Analysis ({result.significant_regions.length})</h3>
                                <div className="space-y-2 max-h-40 overflow-y-auto custom-scrollbar">
                                    {result.significant_regions.length === 0 ? (
                                        <p className="text-xs text-ocean-500 italic">No significant regions crossed the mathematical threshold limits.</p>
                                    ) : (
                                        result.significant_regions.map((reg) => (
                                            <div key={reg.region_id} className="flex justify-between items-center text-xs bg-ocean-900/40 p-2.5 rounded border border-ocean-800/60">
                                                <span className="text-ocean-200">Region {reg.region_id} <span className="text-ocean-600 font-mono ml-2">[{reg.area_pixels} px²]</span></span>
                                                <div className="flex gap-4">
                                                    <span className="text-ocean-400">Confidence: {(reg.confidence * 100).toFixed(1)}%</span>
                                                    <span className="text-emerald-400">Yield: {reg.change_percentage}%</span>
                                                </div>
                                            </div>
                                        ))
                                    )}
                                </div>
                            </div>

                            <div className="mt-6 flex justify-end">
                                <button className="bg-ocean-900 border border-ocean-700 hover:bg-ocean-800 text-ocean-50 text-xs font-bold uppercase tracking-widest px-6 py-3 rounded-lg flex items-center transition-colors">
                                    Route Evidence to {target} Specialist <ArrowRight className="ml-2 w-4 h-4" />
                                </button>
                            </div>

                        </div>
                    )}

                    {loadingStage === 0 && !result && (
                        <div className="flex-1 min-h-[400px] flex flex-col items-center justify-center text-ocean-600 opacity-60">
                            <Layers className="w-20 h-20 mb-4 opacity-50" />
                            <p className="tracking-widest uppercase text-sm font-bold">Awaiting Execution Command</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default ChangeDetection;
