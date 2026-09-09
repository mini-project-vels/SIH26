import React, { useState } from 'react';
import ImageUploader from '../components/ImageUploader';
import AnalysisLoader from '../components/AnalysisLoader';
import { Send, AlertCircle, CheckCircle2, Satellite } from 'lucide-react';
import api from '../services/api';

const SatelliteAnalysis = () => {
    const [file, setFile] = useState(null);
    const [preview, setPreview] = useState(null);
    const [query, setQuery] = useState('');

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [result, setResult] = useState(null);

    const handleAnalyze = async () => {
        if (!file || !query.trim()) {
            setError("Please provide both an image and a query.");
            return;
        }

        setError(null);
        setLoading(true);
        setResult(null);

        const formData = new FormData();
        formData.append('image', file);
        formData.append('query', query);

        try {
            const response = await api.post('/analyze-image', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            setResult(response.data);
        } catch (err) {
            console.error(err);
            setError(err.response?.data?.detail || "An error occurred during analysis.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="max-w-6xl mx-auto space-y-6">
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-white mb-2">Satellite Analysis</h1>
                <p className="text-slate-400">Ask any natural-language question about the uploaded satellite image using advanced Vision-Language Models.</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Left Col: Upload */}
                <div className="lg:col-span-1 space-y-6">
                    <div className="glass-panel p-5">
                        <ImageUploader
                            file={file} setFile={setFile}
                            preview={preview} setPreview={setPreview}
                            label="Target Satellite Image"
                        />
                    </div>

                    <div className="glass-panel p-5">
                        <label className="block text-sm font-medium text-slate-400 mb-2">Natural Language Query</label>
                        <textarea
                            className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-slate-200 focus:outline-none focus:border-accent-blue focus:ring-1 focus:ring-accent-blue resize-none placeholder-slate-600"
                            rows={4}
                            placeholder="e.g. What can you see in this satellite image? Identify major landmarks."
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                        />

                        <button
                            onClick={handleAnalyze}
                            disabled={loading || !file || !query.trim()}
                            className="w-full mt-4 bg-accent-blue hover:brightness-110 text-white font-semibold py-3 px-4 rounded-lg flex items-center justify-center transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-[0_0_15px_rgba(239,108,0,0.15)]"
                        >
                            {loading ? 'Processing...' : (
                                <>Analyze Image <Send className="ml-2 w-4 h-4" /></>
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

                {/* Right Col: Results */}
                <div className="lg:col-span-2">
                    <div className="glass-panel h-full min-h-[500px] p-6 lg:p-8 flex flex-col">
                        <h2 className="text-xl font-semibold text-slate-200 mb-4 border-b border-slate-800 pb-4">Analysis Results</h2>

                        {loading ? (
                            <div className="flex-1 flex items-center justify-center">
                                <AnalysisLoader />
                            </div>
                        ) : result ? (
                            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
                                <div className="flex items-center justify-between p-4 bg-slate-800/50 rounded-lg border border-slate-700">
                                    <div className="flex items-center space-x-3">
                                        {result.status === "ERROR" ? (
                                            <AlertCircle className="w-6 h-6 text-red-500" />
                                        ) : (
                                            <CheckCircle2 className="w-6 h-6 text-impact-green" />
                                        )}
                                        <div>
                                            <div className="text-sm text-slate-400 uppercase tracking-wide font-semibold">Status</div>
                                            <div className={`font-medium ${result.status === "ERROR" ? "text-red-400" : "text-white"}`}>{result.status}</div>
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <div className="text-sm text-slate-400 uppercase tracking-wide font-semibold">Model</div>
                                        <div className="font-medium text-white">{result.model?.model_name || 'Vision Model'}</div>
                                    </div>
                                </div>

                                <div>
                                    <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">AI Analysis</h3>
                                    <div className={`bg-slate-900 border ${result.status === "ERROR" ? "border-red-500/30" : "border-slate-700"} p-5 rounded-lg text-slate-200 leading-relaxed whitespace-pre-wrap shadow-inner relative`}>
                                        {result.status === "ERROR"
                                            ? result.message
                                            : (result.result?.answer || "No response provided by the model.")}
                                        <div className={`absolute top-0 right-0 w-16 h-16 bg-gradient-to-bl ${result.status === "ERROR" ? "from-red-500/10" : "from-accent-blue/10"} to-transparent pointer-events-none rounded-tr-lg`}></div>
                                    </div>
                                </div>

                                {result.limitations && result.limitations.length > 0 && (
                                    <div className="mt-8">
                                        <h3 className="text-xs font-semibold text-slate-500 uppercase mb-2">Limitations</h3>
                                        <ul className="list-disc list-inside text-xs text-slate-500 space-y-1">
                                            {result.limitations.map((lim, i) => (
                                                <li key={i}>{lim}</li>
                                            ))}
                                        </ul>
                                    </div>
                                )}
                            </div>
                        ) : (
                            <div className="flex-1 flex flex-col items-center justify-center text-slate-500">
                                <Satellite className="w-16 h-16 mb-4 opacity-50" />
                                <p>Upload an image and submit a query to view results.</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default SatelliteAnalysis;
