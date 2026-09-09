import { useState, useRef } from 'react';
import axios from 'axios';
import {
    Flame, Upload, AlertTriangle, CheckCircle, XCircle, Clock,
    Activity, Eye, Thermometer, Wind, BarChart3, Info,
    ChevronDown, ChevronUp, FileImage, RefreshCw, Loader2,
    ShieldAlert, Shield, MapPin, Layers,
} from 'lucide-react';

const API_BASE = 'http://localhost:8000';

/** ─── Colour utilities ────────────────────────────────────────────────────── */
const levelColor = {
    LOW: { ring: '#22c55e', glow: 'rgba(34,197,94,0.25)', text: '#4ade80', badge: 'rgba(34,197,94,0.18)' },
    MODERATE: { ring: '#f59e0b', glow: 'rgba(245,158,11,0.25)', text: '#fbbf24', badge: 'rgba(245,158,11,0.18)' },
    HIGH: { ring: '#ef4444', glow: 'rgba(239,68,68,0.30)', text: '#f87171', badge: 'rgba(239,68,68,0.20)' },
    CRITICAL: { ring: '#dc2626', glow: 'rgba(220,38,38,0.40)', text: '#ff4444', badge: 'rgba(220,38,38,0.28)' },
};
const alertIcon = { INFO: Shield, WATCH: ShieldAlert, WARNING: AlertTriangle, CRITICAL: Flame };

function BoolBadge({ val, trueLabel = 'YES', falseLabel = 'NO', unknownLabel = 'UNKNOWN' }) {
    if (val === null || val === undefined)
        return <span style={{ color: '#94a3b8', fontSize: 12, fontWeight: 700 }}>{unknownLabel}</span>;
    return (
        <span style={{
            color: val ? '#f87171' : '#4ade80',
            background: val ? 'rgba(239,68,68,0.15)' : 'rgba(34,197,94,0.12)',
            border: `1px solid ${val ? 'rgba(239,68,68,0.35)' : 'rgba(34,197,94,0.3)'}`,
            borderRadius: 6, padding: '2px 10px', fontSize: 12, fontWeight: 700,
        }}>{val ? trueLabel : falseLabel}</span>
    );
}

function Pill({ label, color = '#94a3b8' }) {
    return (
        <span style={{
            display: 'inline-block', padding: '2px 10px', borderRadius: 20,
            background: `${color}22`, border: `1px solid ${color}44`,
            color, fontSize: 11, fontWeight: 700, letterSpacing: '0.04em',
        }}>{label}</span>
    );
}

function ImageUploadBox({ label, file, onSelect, onClear }) {
    const ref = useRef();
    return (
        <div
            onClick={() => ref.current.click()}
            onDragOver={e => e.preventDefault()}
            onDrop={e => {
                e.preventDefault();
                const f = e.dataTransfer.files[0];
                if (f && f.type.startsWith('image/')) onSelect(f);
            }}
            style={{
                border: `2px dashed ${file ? 'rgba(239,68,68,0.5)' : 'rgba(148,163,184,0.3)'}`,
                borderRadius: 12, padding: 20, textAlign: 'center', cursor: 'pointer',
                background: file ? 'rgba(239,68,68,0.06)' : 'rgba(15,23,42,0.4)',
                transition: 'all .3s ease', position: 'relative',
            }}
        >
            <input ref={ref} type="file" accept="image/*" hidden
                onChange={e => e.target.files[0] && onSelect(e.target.files[0])} />
            {file ? (
                <>
                    <img src={URL.createObjectURL(file)} alt="preview"
                        style={{ maxHeight: 160, borderRadius: 8, objectFit: 'cover', marginBottom: 8 }} />
                    <div style={{ color: '#94a3b8', fontSize: 12 }}>{file.name}</div>
                    <button onClick={e => { e.stopPropagation(); onClear(); }}
                        style={{
                            position: 'absolute', top: 8, right: 8, background: 'rgba(239,68,68,0.3)',
                            border: 'none', borderRadius: 6, color: '#f87171', padding: '2px 8px', cursor: 'pointer'
                        }}>✕</button>
                </>
            ) : (
                <>
                    <Upload size={28} style={{ color: 'rgba(148,163,184,0.5)', marginBottom: 8 }} />
                    <div style={{ color: '#94a3b8', fontSize: 13, fontWeight: 600 }}>{label}</div>
                    <div style={{ color: '#64748b', fontSize: 11, marginTop: 4 }}>Drag & drop or click to browse</div>
                </>
            )}
        </div>
    );
}

function RiskMeter({ score = 0 }) {
    const pct = score;
    const clamp = Math.min(100, Math.max(0, pct));
    const angle = (clamp / 100) * 180 - 90;
    const col = clamp <= 25 ? '#22c55e' : clamp <= 50 ? '#f59e0b' : clamp <= 75 ? '#ef4444' : '#dc2626';
    const r = 72, cx = 90, cy = 90;
    const arc = (deg) => {
        const rad = (deg - 90) * Math.PI / 180;
        return [cx + r * Math.cos(rad), cy + r * Math.sin(rad)];
    };
    const [x1, y1] = arc(-90); const [x2, y2] = arc(90);
    const [xv, yv] = arc(angle);
    return (
        <svg viewBox="0 0 180 100" style={{ width: '100%', maxWidth: 200 }}>
            <path d={`M ${x1} ${y1} A ${r} ${r} 0 0 1 ${x2} ${y2}`}
                fill="none" stroke="rgba(148,163,184,0.15)" strokeWidth={14} />
            <path d={`M ${x1} ${y1} A ${r} ${r} 0 0 1 ${xv} ${yv}`}
                fill="none" stroke={col} strokeWidth={14} strokeLinecap="round"
                style={{ filter: `drop-shadow(0 0 6px ${col})` }} />
            <text x={cx} y={cy - 4} textAnchor="middle" fill="#f1f5f9" fontSize="22" fontWeight="bold">{score}</text>
            <text x={cx} y={cy + 14} textAnchor="middle" fill="#94a3b8" fontSize="10">/ 100</text>
        </svg>
    );
}

function EvidenceCard({ label, icon: Icon, available, value, sub, color = '#94a3b8' }) {
    return (
        <div style={{
            background: available ? `${color}10` : 'rgba(15,23,42,0.5)',
            border: `1px solid ${available ? color + '35' : 'rgba(148,163,184,0.12)'}`,
            borderRadius: 10, padding: '14px 16px', display: 'flex', alignItems: 'center', gap: 12,
        }}>
            <div style={{
                width: 36, height: 36, borderRadius: 8,
                background: available ? `${color}20` : 'rgba(148,163,184,0.08)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
                <Icon size={18} style={{ color: available ? color : '#475569' }} />
            </div>
            <div>
                <div style={{ color: '#94a3b8', fontSize: 11, fontWeight: 600 }}>{label}</div>
                <div style={{
                    color: available ? '#f1f5f9' : '#475569', fontWeight: 700, fontSize: 13, marginTop: 1,
                }}>
                    {value ?? (available ? 'DETECTED' : 'NOT AVAILABLE')}
                </div>
                {sub && <div style={{ color: '#64748b', fontSize: 10, marginTop: 2 }}>{sub}</div>}
            </div>
        </div>
    );
}

export default function WildfireIntelligence() {
    const [mode, setMode] = useState('single');   // 'single' | 'temporal'
    const [singleFile, setSingleFile] = useState(null);
    const [beforeFile, setBeforeFile] = useState(null);
    const [afterFile, setAfterFile] = useState(null);
    const [query, setQuery] = useState('Detect wildfire activity, burned areas, smoke and fire risk in this region.');
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);
    const [viewAnnotated, setViewAnnotated] = useState(true);
    const [showLimitations, setShowLimitations] = useState(false);
    const [showFactors, setShowFactors] = useState(true);

    const handleAnalyze = async () => {
        setLoading(true); setError(null); setResult(null);
        try {
            const fd = new FormData();
            fd.append('query', query);
            if (mode === 'single' && singleFile) fd.append('image', singleFile);
            if (mode === 'temporal') {
                if (beforeFile) fd.append('before_image', beforeFile);
                if (afterFile) fd.append('after_image', afterFile);
            }
            const res = await axios.post(`${API_BASE}/api/disaster/wildfire/analyze`, fd,
                { headers: { 'Content-Type': 'multipart/form-data' } });
            setResult(res.data);
        } catch (err) {
            setError(err.response?.data?.detail || err.message || 'Analysis failed');
        } finally {
            setLoading(false);
        }
    };

    const risk = result?.risk_assessment ?? {};
    const wa = result?.wildfire_assessment ?? {};
    const ca = result?.change_analysis ?? {};
    const spread = result?.fire_spread ?? {};
    const impact = result?.potential_impact ?? {};
    const thermal = result?.thermal_evidence ?? {};
    const satInfo = result?.satellite_info ?? {};
    const vlm = result?.ai_visual_assessment ?? {};
    const lv = levelColor[risk.risk_level] ?? levelColor.LOW;
    const AlertIcon = alertIcon[risk.alert_state] ?? Shield;

    const canAnalyze = mode === 'single'
        ? (singleFile !== null)
        : (beforeFile !== null && afterFile !== null);

    return (
        <div style={{
            minHeight: '100vh', background: 'linear-gradient(135deg, #0a0e1a 0%, #0d1524 50%, #0a1120 100%)',
            color: '#f1f5f9', fontFamily: "'Inter', sans-serif", padding: '28px 24px',
        }}>
            {/* ── Header ─────────────────────────────────────────────────────── */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 28 }}>
                <div style={{
                    width: 48, height: 48, borderRadius: 12, display: 'flex',
                    alignItems: 'center', justifyContent: 'center',
                    background: 'linear-gradient(135deg, #dc2626, #ef4444)',
                    boxShadow: '0 0 24px rgba(239,68,68,0.4)',
                }}>
                    <Flame size={26} style={{ color: '#fff' }} />
                </div>
                <div>
                    <h1 style={{ margin: 0, fontSize: 22, fontWeight: 800, letterSpacing: '-0.02em' }}>
                        🔥 Wildfire Risk Intelligence
                    </h1>
                    <p style={{ margin: 0, color: '#64748b', fontSize: 13 }}>
                        Forest fire detection · Burned-area mapping · Fire-spread analysis
                    </p>
                </div>
            </div>

            {/* ── Transparency notice ─────────────────────────────────────────── */}
            <div style={{
                background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.25)',
                borderRadius: 10, padding: '10px 16px', marginBottom: 22,
                display: 'flex', alignItems: 'flex-start', gap: 10, fontSize: 12,
            }}>
                <Info size={15} style={{ color: '#f59e0b', flexShrink: 0, marginTop: 1 }} />
                <span style={{ color: '#94a3b8', lineHeight: 1.6 }}>
                    <strong style={{ color: '#f59e0b' }}>Data Transparency: </strong>
                    Analysis uses <strong>optical RGB spectral heuristics</strong> (WILDFIRE_SPECIALIST_LIMITED) — not a dedicated fire-detection model.
                    <strong> Thermal data (NASA FIRMS / MODIS / VIIRS / Sentinel-3) is NOT integrated</strong> and is explicitly reported as unavailable.
                    AI visual reasoning is labelled VLM_VISUAL_REASONING.
                    All results require ground verification and thermal confirmation before emergency response.
                </span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '380px 1fr', gap: 22, alignItems: 'start' }}>

                {/* ── LEFT PANEL ─────────────────────────────────────────────────── */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>

                    {/* Mode selector */}
                    <div style={{
                        background: 'rgba(15,23,42,0.7)', border: '1px solid rgba(148,163,184,0.1)',
                        borderRadius: 14, overflow: 'hidden',
                    }}>
                        <div style={{
                            display: 'grid', gridTemplateColumns: '1fr 1fr',
                            background: 'rgba(0,0,0,0.3)',
                        }}>
                            {[['single', FileImage, 'Single Image'], ['temporal', Layers, 'Before / After']].map(([m, Icon, lbl]) => (
                                <button key={m} onClick={() => { setMode(m); setResult(null); setError(null); }}
                                    style={{
                                        padding: '10px 0', display: 'flex', alignItems: 'center', justifyContent: 'center',
                                        gap: 7, border: 'none', cursor: 'pointer', fontWeight: 700, fontSize: 13,
                                        transition: 'all .2s',
                                        background: mode === m ? 'rgba(239,68,68,0.15)' : 'transparent',
                                        color: mode === m ? '#f87171' : '#64748b',
                                        borderBottom: mode === m ? '2px solid #ef4444' : '2px solid transparent',
                                    }}>
                                    <Icon size={15} />{lbl}
                                </button>
                            ))}
                        </div>

                        <div style={{ padding: 18, display: 'flex', flexDirection: 'column', gap: 14 }}>
                            {mode === 'single' ? (
                                <ImageUploadBox label="Upload Satellite Image" file={singleFile}
                                    onSelect={setSingleFile} onClear={() => setSingleFile(null)} />
                            ) : (
                                <>
                                    <ImageUploadBox label="Upload Before Image (Baseline)" file={beforeFile}
                                        onSelect={setBeforeFile} onClear={() => setBeforeFile(null)} />
                                    <ImageUploadBox label="Upload After Image (Recent)" file={afterFile}
                                        onSelect={setAfterFile} onClear={() => setAfterFile(null)} />
                                </>
                            )}

                            {/* Query */}
                            <div>
                                <label style={{ color: '#94a3b8', fontSize: 12, fontWeight: 600, display: 'block', marginBottom: 6 }}>
                                    Analysis Query
                                </label>
                                <textarea value={query} onChange={e => setQuery(e.target.value)} rows={3}
                                    style={{
                                        width: '100%', background: 'rgba(0,0,0,0.35)', border: '1px solid rgba(148,163,184,0.2)',
                                        borderRadius: 8, color: '#e2e8f0', padding: 10, fontSize: 13,
                                        resize: 'vertical', outline: 'none', fontFamily: 'inherit', boxSizing: 'border-box',
                                    }} />
                            </div>

                            <button onClick={handleAnalyze}
                                disabled={loading || (!canAnalyze && !loading)}
                                style={{
                                    padding: '12px 0', borderRadius: 10, border: 'none', cursor: canAnalyze && !loading ? 'pointer' : 'not-allowed',
                                    background: canAnalyze ? 'linear-gradient(135deg, #dc2626, #b91c1c)' : 'rgba(148,163,184,0.1)',
                                    color: canAnalyze ? '#fff' : '#4b5563', fontWeight: 800, fontSize: 15,
                                    display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                                    boxShadow: canAnalyze ? '0 0 20px rgba(239,68,68,0.3)' : 'none',
                                    transition: 'all .3s',
                                }}>
                                {loading ? <><Loader2 size={16} style={{ animation: 'spin 1s linear infinite' }} />Analyzing...</> :
                                    <><Flame size={16} />Analyze Wildfire</>}
                            </button>
                        </div>
                    </div>

                    {/* Satellite info (from results) */}
                    {result && (
                        <div style={{
                            background: 'rgba(15,23,42,0.7)', border: '1px solid rgba(148,163,184,0.1)',
                            borderRadius: 14, padding: 18,
                        }}>
                            <div style={{ color: '#94a3b8', fontSize: 12, fontWeight: 700, marginBottom: 12 }}>🛰 SATELLITE INFO</div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                                {[
                                    ['Platform', satInfo.platform],
                                    ['Data Source', satInfo.data_source],
                                    ['Thermal', satInfo.thermal_product],
                                    ['SAR Scar Prep', satInfo.sar_fire_scar],
                                    ['Mode', result.analysis_mode],
                                    ['Request ID', result.request_id],
                                ].map(([k, v]) => (
                                    <div key={k} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12 }}>
                                        <span style={{ color: '#64748b' }}>{k}</span>
                                        <span style={{ color: '#cbd5e1', fontFamily: 'monospace' }}>{v || '—'}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>

                {/* ── RIGHT PANEL ────────────────────────────────────────────────── */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>

                    {error && (
                        <div style={{
                            background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)',
                            borderRadius: 12, padding: 18, display: 'flex', gap: 10, alignItems: 'flex-start',
                        }}>
                            <XCircle size={18} style={{ color: '#f87171', flexShrink: 0 }} />
                            <div>
                                <div style={{ color: '#f87171', fontWeight: 700 }}>Analysis Error</div>
                                <div style={{ color: '#94a3b8', fontSize: 13, marginTop: 4 }}>{error}</div>
                            </div>
                        </div>
                    )}

                    {loading && (
                        <div style={{
                            background: 'rgba(15,23,42,0.7)', border: '1px solid rgba(148,163,184,0.12)',
                            borderRadius: 14, padding: 36, textAlign: 'center',
                        }}>
                            <Loader2 size={40} style={{ color: '#ef4444', animation: 'spin 1s linear infinite', marginBottom: 14 }} />
                            <div style={{ color: '#94a3b8', fontWeight: 600 }}>Running wildfire analysis pipeline...</div>
                            <div style={{ color: '#64748b', fontSize: 12, marginTop: 8 }}>
                                Spectral heuristics → Burned-area detection → AI visual reasoning → Risk scoring
                            </div>
                        </div>
                    )}

                    {result && !loading && (
                        <>
                            {/* ── Status header ─────────────────────────────────────── */}
                            <div style={{
                                background: `rgba(15,23,42,0.8)`,
                                border: `1px solid ${lv.ring}40`,
                                boxShadow: `0 0 30px ${lv.glow}`,
                                borderRadius: 14, padding: 20,
                                display: 'grid', gridTemplateColumns: '1fr auto', gap: 16, alignItems: 'center',
                            }}>
                                <div>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
                                        <AlertIcon size={20} style={{ color: lv.text }} />
                                        <span style={{ color: '#94a3b8', fontSize: 12, fontWeight: 700, letterSpacing: '0.08em' }}>
                                            WILDFIRE STATUS
                                        </span>
                                        <span style={{
                                            padding: '2px 10px', borderRadius: 20, fontSize: 11, fontWeight: 800,
                                            background: `${lv.ring}22`, color: lv.text, border: `1px solid ${lv.ring}44`,
                                        }}>{risk.alert_state ?? 'INFO'}</span>
                                    </div>
                                    <div style={{ fontSize: 26, fontWeight: 900, color: lv.text, marginBottom: 4 }}>
                                        {result.detection_status}
                                    </div>
                                    <div style={{ fontSize: 12, color: '#64748b' }}>
                                        Risk Level: <strong style={{ color: lv.text }}>{risk.risk_level}</strong> ·
                                        Confidence: <strong style={{ color: '#e2e8f0' }}>{((risk.confidence ?? 0) * 100).toFixed(0)}%</strong> ·
                                        Mode: <strong style={{ color: '#e2e8f0' }}>{result.analysis_mode?.replace(/_/g, ' ').toUpperCase()}</strong>
                                    </div>
                                </div>
                                <RiskMeter score={risk.risk_score ?? 0} />
                            </div>

                            {/* ── Detection badges ──────────────────────────────────── */}
                            <div style={{
                                background: 'rgba(15,23,42,0.7)', border: '1px solid rgba(148,163,184,0.1)',
                                borderRadius: 14, padding: 18,
                            }}>
                                <div style={{ color: '#94a3b8', fontSize: 11, fontWeight: 700, marginBottom: 14 }}>DETECTION FLAGS</div>
                                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10 }}>
                                    {[
                                        ['Fire Detected', wa.fire_detected],
                                        ['Active Fire', wa.active_fire_detected],
                                        ['Smoke Detected', wa.smoke_detected],
                                        ['Burned Area', wa.burned_area_detected],
                                        ['Change Detected', ca.change_detected],
                                        ['Fire Spreading', spread.trend === 'EXPANDING'],
                                    ].map(([lbl, val]) => (
                                        <div key={lbl} style={{
                                            background: 'rgba(0,0,0,0.3)', borderRadius: 10, padding: '10px 12px',
                                            border: '1px solid rgba(148,163,184,0.1)',
                                        }}>
                                            <div style={{ color: '#64748b', fontSize: 10, fontWeight: 600, marginBottom: 4 }}>{lbl}</div>
                                            <BoolBadge val={val} />
                                        </div>
                                    ))}
                                </div>
                                {wa.active_fire_note && (
                                    <div style={{ marginTop: 10, color: '#f59e0b', fontSize: 11, background: 'rgba(245,158,11,0.09)', borderRadius: 8, padding: '6px 10px' }}>
                                        ⚠️ {wa.active_fire_note}
                                    </div>
                                )}
                            </div>

                            {/* ── Metrics ───────────────────────────────────────────── */}
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10 }}>
                                {[
                                    ['Burned Area', `${(wa.burned_percentage ?? 0).toFixed(1)}%`, '#ef4444'],
                                    ['Smoke', `${(wa.smoke_percentage ?? 0).toFixed(1)}%`, '#94a3b8'],
                                    ['Fire Indicator', `${(wa.fire_indicator_percentage ?? 0).toFixed(1)}%`, '#f97316'],
                                    ['Vegetation', `${(wa.vegetation_percentage ?? 0).toFixed(1)}%`, '#22c55e'],
                                ].map(([label, val, col]) => (
                                    <div key={label} style={{
                                        background: 'rgba(15,23,42,0.7)', border: `1px solid ${col}25`,
                                        borderRadius: 12, padding: '14px 16px', textAlign: 'center',
                                    }}>
                                        <div style={{ color: '#64748b', fontSize: 10, fontWeight: 700, marginBottom: 4 }}>{label.toUpperCase()}</div>
                                        <div style={{ color: col, fontSize: 22, fontWeight: 900 }}>{val}</div>
                                    </div>
                                ))}
                            </div>

                            {/* ── Fire Spread ───────────────────────────────────────── */}
                            <div style={{
                                background: 'rgba(15,23,42,0.7)', border: '1px solid rgba(148,163,184,0.1)',
                                borderRadius: 14, padding: 18,
                            }}>
                                <div style={{ color: '#94a3b8', fontSize: 11, fontWeight: 700, marginBottom: 12 }}>🔥 FIRE SPREAD ANALYSIS</div>
                                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10 }}>
                                    {[
                                        ['Trend', spread.trend ?? 'NOT_AVAILABLE', spread.trend === 'EXPANDING' ? '#ef4444' : '#94a3b8'],
                                        ['Change', `${(spread.change_percentage ?? 0).toFixed(1)}%`, '#f97316'],
                                        ['Confidence', `${((spread.confidence ?? 0) * 100).toFixed(0)}%`, '#60a5fa'],
                                    ].map(([k, v, c]) => (
                                        <div key={k} style={{
                                            background: 'rgba(0,0,0,0.3)', borderRadius: 10, padding: '10px 14px',
                                            border: '1px solid rgba(148,163,184,0.1)',
                                        }}>
                                            <div style={{ color: '#64748b', fontSize: 10, fontWeight: 700, marginBottom: 4 }}>{k}</div>
                                            <div style={{ color: c, fontSize: 15, fontWeight: 800 }}>{v}</div>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* ── Evidence panel ────────────────────────────────────── */}
                            <div style={{
                                background: 'rgba(15,23,42,0.7)', border: '1px solid rgba(148,163,184,0.1)',
                                borderRadius: 14, padding: 18,
                            }}>
                                <div style={{ color: '#94a3b8', fontSize: 11, fontWeight: 700, marginBottom: 14 }}>EVIDENCE SOURCES</div>
                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                                    <EvidenceCard label="Fire Indicator" icon={Flame}
                                        available={wa.fire_indicator_detected}
                                        value={wa.fire_indicator_detected ? `${(wa.fire_indicator_percentage ?? 0).toFixed(1)}% pixels` : 'Not detected'}
                                        sub="RGB warm-pixel proxy"
                                        color="#ef4444" />
                                    <EvidenceCard label="Burned Area" icon={AlertTriangle}
                                        available={wa.burned_area_detected}
                                        value={wa.burned_area_detected ? `${(wa.burned_percentage ?? 0).toFixed(1)}% of image` : 'Not detected'}
                                        sub="Spectral char/ash index"
                                        color="#dc2626" />
                                    <EvidenceCard label="Smoke Signature" icon={Wind}
                                        available={wa.smoke_detected}
                                        value={wa.smoke_detected ? `${(wa.smoke_percentage ?? 0).toFixed(1)}% coverage` : 'Not detected'}
                                        sub="Grey/haze spectral proxy"
                                        color="#94a3b8" />
                                    <EvidenceCard label="Temporal Change" icon={RefreshCw}
                                        available={ca.change_detected}
                                        value={ca.change_detected ? `${(ca.estimated_change_percentage ?? 0).toFixed(1)}% changed` : 'Not detected'}
                                        sub={ca.change_type ?? 'Before/after comparison'}
                                        color="#60a5fa" />
                                    <EvidenceCard label="Thermal Hotspot" icon={Thermometer}
                                        available={false}
                                        value="UNAVAILABLE"
                                        sub="NASA FIRMS / MODIS / VIIRS"
                                        color="#f59e0b" />
                                    <EvidenceCard label="AI Visual Reasoning" icon={Eye}
                                        available={vlm.available}
                                        value={vlm.available ? 'VLM analysis complete' : 'Unavailable'}
                                        sub={vlm.available ? vlm.model : 'HuggingFace VLM'}
                                        color="#a78bfa" />
                                </div>
                            </div>

                            {/* ── Temporal change ───────────────────────────────────── */}
                            {ca.change_detected && (
                                <div style={{
                                    background: 'rgba(15,23,42,0.7)', border: '1px solid rgba(96,165,250,0.2)',
                                    borderRadius: 14, padding: 18,
                                }}>
                                    <div style={{ color: '#94a3b8', fontSize: 11, fontWeight: 700, marginBottom: 12 }}>TEMPORAL CHANGE BREAKDOWN</div>
                                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 10 }}>
                                        {[
                                            ['Type', ca.change_type ?? 'N/A', '#60a5fa'],
                                            ['Vegetation Loss', `${(ca.vegetation_loss_percentage ?? 0).toFixed(1)}%`, '#22c55e'],
                                            ['New Burned Area', `${(ca.new_burned_area_percentage ?? 0).toFixed(1)}%`, '#ef4444'],
                                            ['New Smoke', `${(ca.new_smoke_percentage ?? 0).toFixed(1)}%`, '#94a3b8'],
                                        ].map(([k, v, c]) => (
                                            <div key={k} style={{
                                                background: 'rgba(0,0,0,0.3)', borderRadius: 8, padding: '8px 12px',
                                                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                                            }}>
                                                <span style={{ color: '#64748b', fontSize: 12 }}>{k}</span>
                                                <span style={{ color: c, fontWeight: 700, fontSize: 13 }}>{v}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* ── Annotated image ───────────────────────────────────── */}
                            {result.annotated_image?.generated && (
                                <div style={{
                                    background: 'rgba(15,23,42,0.7)', border: '1px solid rgba(148,163,184,0.1)',
                                    borderRadius: 14, padding: 18,
                                }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                                        <div style={{ color: '#94a3b8', fontSize: 11, fontWeight: 700 }}>🗺 ANNOTATED ANALYSIS</div>
                                        <div style={{ display: 'flex', gap: 8 }}>
                                            {[['Annotated', true], ['Original', false]].map(([lbl, v]) => (
                                                <button key={lbl} onClick={() => setViewAnnotated(v)}
                                                    style={{
                                                        padding: '4px 12px', borderRadius: 8, border: 'none', cursor: 'pointer',
                                                        fontSize: 12, fontWeight: 600,
                                                        background: viewAnnotated === v ? 'rgba(239,68,68,0.2)' : 'transparent',
                                                        color: viewAnnotated === v ? '#f87171' : '#64748b',
                                                    }}>{lbl}</button>
                                            ))}
                                        </div>
                                    </div>
                                    {viewAnnotated ? (
                                        <img src={`${API_BASE}/${result.annotated_image.path_or_url}`}
                                            alt="Wildfire analysis overlay"
                                            style={{ width: '100%', borderRadius: 10, border: '1px solid rgba(148,163,184,0.1)' }} />
                                    ) : (
                                        (singleFile || afterFile) && (
                                            <img src={URL.createObjectURL(singleFile ?? afterFile)}
                                                alt="Original satellite"
                                                style={{ width: '100%', borderRadius: 10, border: '1px solid rgba(148,163,184,0.1)' }} />
                                        )
                                    )}
                                    <div style={{ color: '#64748b', fontSize: 10, marginTop: 8, lineHeight: 1.6 }}>
                                        🔴 Red/Orange = Fire candidate  ·  🟤 Dark red fill = Burned area  ·  ⬜ Grey = Smoke candidate
                                    </div>
                                </div>
                            )}

                            {/* ── Risk factors ──────────────────────────────────────── */}
                            {(risk.risk_factors ?? []).length > 0 && (
                                <div style={{
                                    background: 'rgba(15,23,42,0.7)', border: '1px solid rgba(148,163,184,0.1)',
                                    borderRadius: 14, padding: 18,
                                }}>
                                    <button onClick={() => setShowFactors(p => !p)}
                                        style={{
                                            background: 'none', border: 'none', cursor: 'pointer', width: '100%',
                                            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                                            color: '#94a3b8', fontSize: 11, fontWeight: 700, padding: 0,
                                        }}>
                                        <span>RISK FACTOR BREAKDOWN ({risk.risk_factors.length} factors · {risk.independent_sources ?? '?'} sources)</span>
                                        {showFactors ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                                    </button>
                                    {showFactors && (
                                        <div style={{ marginTop: 12, display: 'flex', flexDirection: 'column', gap: 8 }}>
                                            {risk.risk_factors.map((f, i) => (
                                                <div key={i} style={{
                                                    display: 'flex', alignItems: 'center', gap: 10,
                                                    background: 'rgba(0,0,0,0.3)', borderRadius: 8, padding: '10px 14px',
                                                }}>
                                                    <div style={{
                                                        width: 36, height: 36, borderRadius: 8, flexShrink: 0,
                                                        background: 'rgba(239,68,68,0.15)', display: 'flex',
                                                        alignItems: 'center', justifyContent: 'center',
                                                        color: '#f87171', fontWeight: 900, fontSize: 14,
                                                    }}>+{f.contribution}</div>
                                                    <div style={{ flex: 1 }}>
                                                        <div style={{ color: '#e2e8f0', fontSize: 13 }}>{f.factor}</div>
                                                        <div style={{ display: 'flex', gap: 8, marginTop: 4 }}>
                                                            <Pill label={`conf ${(f.evidence_confidence * 100).toFixed(0)}%`} color="#60a5fa" />
                                                            <Pill label={f.source?.replace(/_/g, ' ')} color="#94a3b8" />
                                                        </div>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            )}

                            {/* ── Infrastructure impact ─────────────────────────────── */}
                            <div style={{
                                background: 'rgba(15,23,42,0.7)', border: '1px solid rgba(148,163,184,0.1)',
                                borderRadius: 14, padding: 18,
                            }}>
                                <div style={{ color: '#94a3b8', fontSize: 11, fontWeight: 700, marginBottom: 12 }}>🏘 INFRASTRUCTURE IMPACT ESTIMATE</div>
                                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10 }}>
                                    {[
                                        ['Buildings', impact.potentially_affected_buildings, '#f87171'],
                                        ['Roads', impact.potentially_affected_roads, '#fb923c'],
                                        ['Infrastructure', impact.potentially_affected_infrastructure, '#fbbf24'],
                                    ].map(([lbl, val, col]) => (
                                        <div key={lbl} style={{
                                            background: 'rgba(0,0,0,0.3)', borderRadius: 10, padding: '12px 14px', textAlign: 'center',
                                        }}>
                                            <div style={{ color: '#64748b', fontSize: 10, fontWeight: 700 }}>{lbl.toUpperCase()}</div>
                                            <div style={{ color: col, fontSize: 22, fontWeight: 900 }}>~{val ?? 0}</div>
                                            <div style={{ color: '#475569', fontSize: 10 }}>potentially exposed</div>
                                        </div>
                                    ))}
                                </div>
                                {impact.note && (
                                    <div style={{ marginTop: 10, color: '#64748b', fontSize: 11, lineHeight: 1.5 }}>
                                        ℹ️ {impact.note}
                                    </div>
                                )}
                            </div>

                            {/* ── AI Visual Reasoning ───────────────────────────────── */}
                            {vlm.available && vlm.reasoning && (
                                <div style={{
                                    background: 'rgba(15,23,42,0.7)', border: '1px solid rgba(167,139,250,0.2)',
                                    borderRadius: 14, padding: 18,
                                }}>
                                    <div style={{ color: '#94a3b8', fontSize: 11, fontWeight: 700, marginBottom: 10 }}>
                                        🤖 AI VISUAL REASONING <Pill label="VLM_VISUAL_REASONING" color="#a78bfa" />
                                    </div>
                                    <div style={{ color: '#e2e8f0', fontSize: 13, lineHeight: 1.7, whiteSpace: 'pre-wrap' }}>
                                        {vlm.reasoning}
                                    </div>
                                    <div style={{ marginTop: 8, color: '#64748b', fontSize: 11 }}>{vlm.note}</div>
                                </div>
                            )}

                            {/* ── Thermal notice ────────────────────────────────────── */}
                            <div style={{
                                background: 'rgba(245,158,11,0.07)', border: '1px solid rgba(245,158,11,0.2)',
                                borderRadius: 14, padding: 16,
                            }}>
                                <div style={{ color: '#f59e0b', fontSize: 11, fontWeight: 700, marginBottom: 8 }}>
                                    🌡 THERMAL EVIDENCE STATUS
                                </div>
                                <div style={{ color: '#94a3b8', fontSize: 12, lineHeight: 1.6 }}>
                                    {thermal.note}
                                </div>
                                <div style={{ marginTop: 8, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                                    {['NASA FIRMS', 'MODIS NRT', 'VIIRS SNPP', 'VIIRS NOAA-20', 'Sentinel-3 SLSTR'].map(s => (
                                        <Pill key={s} label={s + ' — Not integrated'} color="#64748b" />
                                    ))}
                                </div>
                            </div>

                            {/* ── Recommendations ───────────────────────────────────── */}
                            <div style={{
                                background: 'rgba(15,23,42,0.7)', border: '1px solid rgba(148,163,184,0.1)',
                                borderRadius: 14, padding: 18,
                            }}>
                                <div style={{ color: '#94a3b8', fontSize: 11, fontWeight: 700, marginBottom: 12 }}>📋 RECOMMENDATIONS</div>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                                    {(result.recommendations ?? []).map((r, i) => (
                                        <div key={i} style={{
                                            background: 'rgba(0,0,0,0.3)', borderRadius: 8, padding: '8px 12px',
                                            color: '#cbd5e1', fontSize: 13, lineHeight: 1.5,
                                            borderLeft: `3px solid ${r.startsWith('🚨') ? '#dc2626' : r.startsWith('⚠️') ? '#f59e0b' : 'rgba(148,163,184,0.3)'}`,
                                        }}>{r}</div>
                                    ))}
                                </div>
                            </div>

                            {/* ── AI disclaimer ─────────────────────────────────────── */}
                            {risk.ai_disclaimer && (
                                <div style={{
                                    background: 'rgba(220,38,38,0.08)', border: '1px solid rgba(220,38,38,0.25)',
                                    borderRadius: 10, padding: '10px 14px',
                                    color: '#f87171', fontSize: 12, display: 'flex', gap: 8, alignItems: 'flex-start',
                                }}>
                                    <AlertTriangle size={14} style={{ flexShrink: 0, marginTop: 1 }} />
                                    {risk.ai_disclaimer}
                                </div>
                            )}

                            {/* ── Limitations ───────────────────────────────────────── */}
                            <div style={{
                                background: 'rgba(15,23,42,0.7)', border: '1px solid rgba(148,163,184,0.1)',
                                borderRadius: 14, padding: 18,
                            }}>
                                <button onClick={() => setShowLimitations(p => !p)}
                                    style={{
                                        background: 'none', border: 'none', cursor: 'pointer', width: '100%',
                                        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                                        color: '#94a3b8', fontSize: 11, fontWeight: 700, padding: 0,
                                    }}>
                                    <span>KNOWN LIMITATIONS ({(result.limitations ?? []).length})</span>
                                    {showLimitations ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                                </button>
                                {showLimitations && (
                                    <ul style={{ margin: '12px 0 0 0', padding: '0 0 0 16px', color: '#64748b', fontSize: 12, lineHeight: 1.9 }}>
                                        {(result.limitations ?? []).map((l, i) => <li key={i}>{l}</li>)}
                                    </ul>
                                )}
                            </div>
                        </>
                    )}

                    {/* Placeholder when no result */}
                    {!result && !loading && !error && (
                        <div style={{
                            background: 'rgba(15,23,42,0.5)', border: '1px solid rgba(148,163,184,0.08)',
                            borderRadius: 14, padding: 52, textAlign: 'center',
                        }}>
                            <Flame size={56} style={{ color: 'rgba(239,68,68,0.2)', marginBottom: 18 }} />
                            <div style={{ color: '#475569', fontWeight: 600, fontSize: 15 }}>
                                Upload a satellite image to begin wildfire analysis
                            </div>
                            <div style={{ color: '#334155', fontSize: 13, marginTop: 8 }}>
                                Supports single image (fire detection) or before/after pair (burned-area change)
                            </div>
                        </div>
                    )}
                </div>
            </div>

            <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>
        </div>
    );
}
