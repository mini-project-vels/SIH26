import React, { useState } from 'react';
import ImageUploader from '../components/ImageUploader';
import AnalysisLoader from '../components/AnalysisLoader';
import { Send, AlertCircle, MapPin, Target } from 'lucide-react';
import api, { getImageUrl } from '../services/api';

const VisualGrounding = () => {
    const [file, setFile] = useState(null);
    const [preview, setPreview] = useState(null);
    const [query, setQuery] = useState('');

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [result, setResult] = useState(null);
    const [showOriginal, setShowOriginal] = useState(false);

    const handleAnalyze = async () => {
        if (!file || !query.trim()) {
            setError("Please provide an image and specify what to locate.");
            return;
        }

        setError(null);
        setLoading(true);
        setResult(null);
        setShowOriginal(false);

        const formData = new FormData();
        formData.append('image', file);
        formData.append('query', query);

        try {
            const response = await api.post('/locate-object', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            setResult(response.data);
        } catch (err) {
            console.error(err);
            setError(err.response?.data?.detail || "An error occurred during grounding analysis.");
        } finally {
            setLoading(false);
        }
    };

    const getAnnotatedUrl = () => {
        if (!result?.annotated_image?.generated) return null;
        return getImageUrl(result.annotated_image.path_or_url || result.annotated_image.url);
    };

    return (
        <div className="max-w-6xl mx-auto space-y-6">
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-white mb-2">Visual Grounding</h1>
                <p className="text-slate-400">Identify, highlight, and segment geographical features from a target query.</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <div className="lg:col-span-1 space-y-6">
                    <div className="glass-panel p-5">
                        <ImageUploader
                            file={file} setFile={setFile}
                            preview={preview} setPreview={setPreview}
                            label="Target Satellite Image"
                        />
                    </div>

                    <div className="glass-panel p-5">
                        <label className="block text-sm font-medium text-slate-400 mb-2">Target Query</label>
                        <input
                            type="text"
                            className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-slate-200 focus:outline-none focus:border-green-400 focus:ring-1 focus:ring-green-400 placeholder-slate-600 mb-2"
                            placeholder="e.g. Highlight all roads and buildings"
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                        />
                        <div className="flex flex-wrap gap-2 mb-4">
                            {['Water bodies', 'Buildings', 'Forests', 'Roads'].map(q => (
                                <button
                                    key={q}
                                    onClick={() => setQuery(`Where are the ${q.toLowerCase()}?`)}
                                    className="text-xs bg-slate-800 text-slate-400 px-2 py-1 rounded hover:bg-slate-700 hover:text-slate-200"
                                >
                                    {q}
                                </button>
                            ))}
                        </div>

                        <button
                            onClick={handleAnalyze}
                            disabled={loading || !file || !query.trim()}
                            className="w-full bg-green-500 hover:bg-green-400 text-navy-dark font-semibold py-3 px-4 rounded-lg flex items-center justify-center transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {loading ? 'Processing...' : (
                                <>Locate Features <Target className="ml-2 w-4 h-4" /></>
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

                <div className="lg:col-span-2">
                    <div className="glass-panel h-full min-h-[600px] flex flex-col relative overflow-hidden">
                        {loading ? (
                            <div className="flex-1 flex items-center justify-center">
                                <AnalysisLoader />
                            </div>
                        ) : result ? (
                            <div className="flex flex-col h-full animate-in fade-in duration-500">
                                <div className="p-4 border-b border-slate-800 flex justify-between items-center bg-slate-900/50">
                                    <div>
                                        <h2 className="text-lg font-semibold text-slate-200">Grounding Results</h2>
                                        <p className="text-sm text-slate-400">Target: <span className="text-green-400 font-medium">{result.target}</span></p>
                                    </div>
                                    {getAnnotatedUrl() && (
                                        <div className="flex bg-slate-800 rounded-lg p-1 border border-slate-700">
                                            <button
                                                onClick={() => setShowOriginal(false)}
                                                className={`px-3 py-1 text-sm rounded-md transition-colors ${!showOriginal ? 'bg-slate-700 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'}`}
                                            >
                                                Analysis
                                            </button>
                                            <button
                                                onClick={() => setShowOriginal(true)}
                                                className={`px-3 py-1 text-sm rounded-md transition-colors ${showOriginal ? 'bg-slate-700 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'}`}
                                            >
                                                Original
                                            </button>
                                        </div>
                                    )}
                                </div>

                                <div className="flex-1 flex flex-col relative bg-[#040810] p-4">
                                    <div className="flex-1 mb-4 flex items-center justify-center relative min-h-[300px] border border-slate-800 rounded-xl overflow-hidden bg-black/20">
                                        {getAnnotatedUrl() ? (
                                            <img
                                                src={showOriginal ? preview : getAnnotatedUrl()}
                                                alt="Grounding result"
                                                className="max-w-full max-h-[450px] object-contain transition-opacity duration-300"
                                            />
                                        ) : (
                                            <div className="text-red-400 p-4 bg-red-400/10 rounded-lg border border-red-400/20 text-sm">
                                                No visual mask generated. Ensure the objects exist in the image.
                                            </div>
                                        )}
                                    </div>

                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        <div className="bg-slate-900 border border-slate-700 p-4 rounded-xl">
                                            <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-2">Findings</h3>
                                            <p className="text-slate-200 text-sm leading-relaxed">{result.text_answer}</p>
                                        </div>
                                        <div className="bg-slate-900 border border-slate-700 p-4 rounded-xl overflow-y-auto max-h-40 custom-scrollbar">
                                            <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3 flex items-center justify-between">
                                                <span>Detections</span>
                                                <span className="bg-green-500/20 text-green-400 px-2 py-0.5 rounded-full text-xs font-bold border border-green-500/30">
                                                    {result.detections?.length || 0} found
                                                </span>
                                            </h3>
                                            {result.detections && result.detections.length > 0 ? (
                                                <div className="space-y-2">
                                                    {result.detections.map(det => (
                                                        <div key={det.id} className="flex justify-between items-center text-sm p-2 bg-slate-800/50 rounded border border-slate-700/50">
                                                            <span className="text-slate-200 font-medium capitalize">{det.label}</span>
                                                            <span className="text-slate-400 text-xs">{det.location}</span>
                                                        </div>
                                                    ))}
                                                </div>
                                            ) : (
                                                <p className="text-slate-500 text-sm">No specific regions identified.</p>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ) : (
                            <div className="flex-1 min-h-[500px] w-full rounded-xl overflow-hidden relative border border-slate-800 shadow-xl">
                                <iframe
                                    title="Interactive Satellite Map"
                                    width="100%"
                                    height="100%"
                                    style={{ border: 0, minHeight: '600px', filter: 'contrast(1.1) saturate(1.2)' }}
                                    src="https://maps.google.com/maps?q=india&t=k&z=5&ie=UTF8&iwloc=&output=embed"
                                    allowFullScreen
                                ></iframe>
                                <div className="absolute top-4 left-4 bg-slate-900/80 backdrop-blur-md px-4 py-2 rounded-xl border border-slate-700 flex items-center shadow-lg pointer-events-none">
                                    <MapPin className="w-5 h-5 mr-3 text-slate-300" />
                                    <span className="text-xs font-bold text-white uppercase tracking-widest">Global Targeting Interface</span>
                                </div>
                                <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 bg-slate-900/90 backdrop-blur-md px-4 py-2 rounded-full border border-slate-700 flex items-center shadow-lg pointer-events-none">
                                    <span className="text-[10px] font-bold text-slate-300 uppercase tracking-widest">Interact to locate zones before uploading target imagery</span>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default VisualGrounding;
