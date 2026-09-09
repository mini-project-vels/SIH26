import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Activity, Bell, User, Map, AlertTriangle, ShieldCheck, ChevronRight, ArrowRight, Waves, Mountain, MountainSnow, Flame, Globe2, Layers, Cpu, Server, Database, Network } from 'lucide-react';

const Dashboard = () => {
    const navigate = useNavigate();

    const modules = [
        {
            id: 'flood',
            title: 'Flood Detection',
            desc: 'Identify flood-prone areas, water extent and monitor changes using satellite imagery.',
            icon: Waves,
            bg: 'https://loremflickr.com/600/400/flood,disaster,water/all',
            color: 'text-cyan-400',
            route: '/flood-intelligence'
        },
        {
            id: 'glacier',
            title: 'Glacier & GLOF',
            desc: 'Monitor glacier movement, detect GLOF risks and analyze ice dynamics using satellite data.',
            icon: MountainSnow,
            bg: 'https://loremflickr.com/600/400/glacier,ice/all',
            color: 'text-purple-400',
            route: '/glacier-intelligence'
        },
        {
            id: 'landslide',
            title: 'Landslide Risk',
            desc: 'Detect slope changes, landslide indicators and assess risk in mountainous regions.',
            icon: AlertTriangle,
            bg: 'https://loremflickr.com/600/400/landslide,mountain,rock/all',
            color: 'text-orange-400',
            route: '/landslide-intelligence'
        },
        {
            id: 'wildfire',
            title: 'Wildfire Risk',
            desc: 'Detect active fires, smoke, burned areas and assess fire risk using satellite data.',
            icon: Flame,
            bg: 'https://loremflickr.com/600/400/wildfire,forest,fire/all',
            color: 'text-red-500',
            route: '/wildfire-intelligence'
        }
    ];

    const activities = [
        { title: "Flood monitoring started", location: "Nepal (28.0, 86.9)", time: "2h ago", status: "Active", icon: Waves, color: "text-cyan-400" },
        { title: "Landslide analysis completed", location: "Uttarakhand (30.3, 79.9)", time: "4h ago", status: "Completed", icon: AlertTriangle, color: "text-orange-400" },
        { title: "Glacier monitoring update", location: "Himachal (32.1, 77.6)", time: "6h ago", status: "Analyzing", icon: MountainSnow, color: "text-purple-400" },
        { title: "Wildfire risk check", location: "California (34.1, -118.2)", time: "8h ago", status: "Processing", icon: Flame, color: "text-red-500" },
        { title: "System health check completed", location: "", time: "12h ago", status: "Healthy", icon: ShieldCheck, color: "text-green-500" }
    ];

    const systemStatus = [
        { label: "Satellite Data Source", icon: Map, status: "Online" },
        { label: "AI Models", icon: Cpu, status: "Online" },
        { label: "Monitoring Service", icon: Activity, status: "Online" },
        { label: "Database", icon: Database, status: "Online" },
        { label: "STAC API Connection", icon: Network, status: "Online" },
        { label: "Background Workers", icon: Server, status: "Online" }
    ];

    return (
        <div className="min-h-screen text-slate-300 font-sans p-2">

            {/* HERO BANNER */}
            <div className="w-full rounded-2xl overflow-hidden relative mb-6 border border-slate-800 shadow-xl h-[320px] bg-slate-900">
                {/* Background image covering full area */}
                <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1614730321146-b6fa6a46bcb4?q=80&w=1974')] bg-cover bg-center bg-no-repeat opacity-40 mix-blend-screen scale-105 transform origin-center"></div>
                <div className="absolute inset-0 bg-gradient-to-r from-slate-950 via-slate-950/80 to-transparent"></div>

                <div className="relative z-10 p-10 flex flex-col h-full justify-between">
                    <div className="max-w-2xl">
                        <div className="flex items-center text-xs font-bold text-cyan-400 tracking-[0.15em] uppercase mb-4">
                            <Activity className="w-4 h-4 mr-2" />
                            Real-Time Monitoring & Disaster Intelligence
                        </div>
                        <h2 className="text-5xl font-extrabold text-white mb-4 tracking-tight">
                            Monitor. Detect. <span className="text-cyan-400">Protect.</span>
                        </h2>
                        <p className="text-slate-400 text-sm leading-relaxed max-w-xl">
                            Leverage satellite data, AI and multi-modal analysis to detect and monitor natural disasters across the globe.
                        </p>
                    </div>

                    <div className="flex gap-4 mt-8">
                        <div className="flex items-center bg-slate-900/60 backdrop-blur-md border border-slate-700/50 rounded-xl px-4 py-3">
                            <div className="w-10 h-10 bg-cyan-900/40 rounded-full flex items-center justify-center mr-3">
                                <Globe2 className="w-5 h-5 text-cyan-400" />
                            </div>
                            <div>
                                <div className="text-xs font-bold text-white">Real Satellite Data</div>
                                <div className="text-[10px] text-slate-400">Sentinel-1 & more</div>
                            </div>
                        </div>
                        <div className="flex items-center bg-slate-900/60 backdrop-blur-md border border-slate-700/50 rounded-xl px-4 py-3">
                            <div className="w-10 h-10 bg-purple-900/40 rounded-full flex items-center justify-center mr-3">
                                <Cpu className="w-5 h-5 text-purple-400" />
                            </div>
                            <div>
                                <div className="text-xs font-bold text-white">Multi-Modal AI</div>
                                <div className="text-[10px] text-slate-400">Satellite + Vision + Context</div>
                            </div>
                        </div>
                        <div className="flex items-center bg-slate-900/60 backdrop-blur-md border border-slate-700/50 rounded-xl px-4 py-3">
                            <div className="w-10 h-10 bg-emerald-900/40 rounded-full flex items-center justify-center mr-3">
                                <ShieldCheck className="w-5 h-5 text-emerald-400" />
                            </div>
                            <div>
                                <div className="text-xs font-bold text-white">Early Warnings</div>
                                <div className="text-[10px] text-slate-400">Save lives & property</div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Floating Widgets Top Right */}
                <div className="absolute top-8 right-8 flex flex-col gap-4">
                    <div className="bg-slate-900/80 backdrop-blur-md border border-slate-700/50 rounded-xl p-4 shadow-xl min-w-[240px]">
                        <div className="flex items-center text-xs font-bold text-white mb-2">
                            <Server className="w-4 h-4 mr-2 text-slate-400" /> System Status
                        </div>
                        <div className="flex items-center justify-between">
                            <div className="flex items-center text-sm font-semibold text-emerald-400">
                                <span className="w-2.5 h-2.5 bg-emerald-500 rounded-full mr-2"></span> All Systems Operational
                            </div>
                            <ChevronRight className="w-4 h-4 text-slate-500" />
                        </div>
                    </div>
                    <div className="bg-slate-900/80 backdrop-blur-md border border-slate-700/50 rounded-xl p-4 shadow-xl min-w-[240px]">
                        <div className="flex items-center text-xs font-bold text-slate-400 mb-2">
                            <Map className="w-4 h-4 mr-2" /> Latest Satellite Pass
                        </div>
                        <div className="text-sm font-semibold text-white">Sentinel-1A</div>
                        <div className="text-xs text-slate-500 mt-1">Sep 1, 2026 03:42 PM</div>
                    </div>
                </div>
            </div>

            {/* DISASTER MODULES */}
            <div className="mb-6">
                <div className="flex justify-between items-end mb-4 px-2">
                    <div>
                        <div className="flex items-center">
                            <Layers className="w-6 h-6 text-cyan-400 mr-2" />
                            <h2 className="text-xl font-bold text-white tracking-wide">Disaster Modules</h2>
                        </div>
                        <p className="text-sm text-slate-500 mt-1">Select a module to detect, analyze and monitor specific natural disasters.</p>
                    </div>
                    <button className="text-xs font-semibold text-cyan-400 flex items-center hover:text-cyan-300">
                        View All Modules <ArrowRight className="w-3 h-3 ml-1" />
                    </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    {modules.map((mod) => {
                        const Icon = mod.icon;
                        return (
                            <div key={mod.id} onClick={() => navigate(mod.route)} className="group relative h-[320px] rounded-2xl overflow-hidden cursor-pointer border border-slate-800 shadow-lg hover:border-slate-600 transition-all duration-500 hover:-translate-y-1">
                                <div className="absolute inset-0 bg-cover bg-center transition-transform duration-700 group-hover:scale-110" style={{ backgroundImage: `url('${mod.bg}')` }}></div>
                                <div className="absolute inset-0 bg-gradient-to-t from-slate-950/80 via-slate-900/20 to-transparent"></div>

                                <div className="absolute inset-0 p-6 flex flex-col justify-end">
                                    <div className={`w-12 h-12 rounded-2xl bg-slate-900/80 backdrop-blur-md border border-slate-700/50 flex items-center justify-center mb-4 ${mod.color}`}>
                                        <Icon className="w-6 h-6" />
                                    </div>
                                    <h3 className="text-xl font-bold text-white mb-2">{mod.title}</h3>
                                    <p className="text-xs text-slate-300 leading-relaxed max-w-[90%] mb-6 line-clamp-3">{mod.desc}</p>

                                    <div className="flex items-center justify-between w-full pb-2">
                                        <button className="w-full bg-slate-900/40 backdrop-blur-sm border border-slate-600 hover:border-slate-400 text-slate-200 text-sm font-semibold py-2.5 px-4 rounded-full flex items-center justify-between transition-colors">
                                            Launch <ArrowRight className="w-4 h-4" />
                                        </button>
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>

            {/* BOTTOM PANELS */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

                {/* Recent Activity */}
                <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6">
                    <div className="flex justify-between items-center mb-6">
                        <h3 className="text-sm font-bold text-white flex items-center"><Activity className="w-4 h-4 mr-2 text-slate-400" /> Recent Activity</h3>
                        <button className="text-xs text-cyan-400 hover:text-cyan-300 font-semibold flex items-center">View All <ChevronRight className="w-3 h-3 ml-1" /></button>
                    </div>
                    <div className="space-y-4">
                        {activities.map((act, i) => {
                            const ActIcon = act.icon;
                            let statusColor = "text-slate-400 bg-slate-800/50 border-slate-700";
                            if (act.status === "Active" || act.status === "Healthy") statusColor = "text-emerald-400 bg-emerald-900/20 border-emerald-800";
                            if (act.status === "Completed" || act.status === "Analyzing") statusColor = "text-blue-400 bg-blue-900/20 border-blue-800";

                            return (
                                <div key={i} className="flex items-center justify-between py-2 border-b border-slate-800/50 last:border-0 last:pb-0">
                                    <div className="flex items-center flex-1">
                                        <div className={`w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center mr-3 shrink-0 ${act.color}`}>
                                            <ActIcon className="w-4 h-4" />
                                        </div>
                                        <div>
                                            <div className="text-xs font-semibold text-slate-200">{act.title}</div>
                                            {(act.location) ? (
                                                <div className="text-[10px] text-slate-500">{act.location}</div>
                                            ) : null}
                                        </div>
                                    </div>
                                    <div className="flex items-center space-x-4 shrink-0">
                                        <span className="text-[10px] text-slate-500 whitespace-nowrap">{act.time}</span>
                                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${statusColor} w-16 text-center`}>{act.status}</span>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>

                {/* System Status Detail */}
                <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6">
                    <div className="flex justify-between items-center mb-6">
                        <h3 className="text-sm font-bold text-white flex items-center"><Activity className="w-4 h-4 mr-2 text-slate-400" /> System Status</h3>
                        <button className="text-xs text-cyan-400 hover:text-cyan-300 font-semibold flex items-center">View Details <ChevronRight className="w-3 h-3 ml-1" /></button>
                    </div>
                    <div className="space-y-1">
                        {systemStatus.map((sys, i) => {
                            const SysIcon = sys.icon;
                            return (
                                <div key={i} className="flex items-center justify-between py-2.5">
                                    <div className="flex items-center">
                                        <div className="w-7 h-7 rounded-full bg-slate-800 flex items-center justify-center mr-3">
                                            <SysIcon className="w-3.5 h-3.5 text-slate-400" />
                                        </div>
                                        <span className="text-xs text-slate-300 font-medium">{sys.label}</span>
                                    </div>
                                    <div className="flex items-center text-xs font-semibold text-emerald-400">
                                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-2"></span> {sys.status}
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>

                {/* Global Coverage Map Snippet */}
                <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 flex flex-col">
                    <div className="flex justify-between items-center mb-4">
                        <h3 className="text-sm font-bold text-white flex items-center"><Globe2 className="w-4 h-4 mr-2 text-slate-400" /> Global Coverage</h3>
                        <button className="text-xs text-cyan-400 hover:text-cyan-300 font-semibold flex items-center">View More <ChevronRight className="w-3 h-3 ml-1" /></button>
                    </div>
                    <div className="flex-1 min-h-[160px] bg-[url('https://upload.wikimedia.org/wikipedia/commons/8/80/World_map_-_low_resolution.svg')] bg-contain bg-center bg-no-repeat opacity-40 filter invert sepia saturate-200 hue-rotate-180 brightness-75 drop-shadow-[0_0_15px_rgba(0,200,255,0.4)]"></div>

                    <div className="flex justify-between items-center border-t border-slate-800 pt-4 mt-4">
                        <div className="flex items-center text-[10px] text-slate-400">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mr-1.5"></span> Active Monitoring
                        </div>
                        <div className="flex items-center text-[10px] text-slate-400">
                            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 mr-1.5"></span> Recent Activity
                        </div>
                        <div className="flex items-center text-[10px] text-slate-400">
                            <span className="w-1.5 h-1.5 rounded-full bg-slate-600 mr-1.5"></span> Coverage Area
                        </div>
                    </div>
                </div>

            </div>
        </div>
    );
};

export default Dashboard;
