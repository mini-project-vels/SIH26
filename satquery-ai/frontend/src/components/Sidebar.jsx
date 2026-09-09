import React from 'react';
import { NavLink } from 'react-router-dom';
import {
    Home, Satellite, RefreshCcw, MapPin, Waves, MountainSnow, Siren,
    Activity, ShieldAlert, Contact, Globe2, Radio, Mountain, Flame, Settings, FileText, HelpCircle, User
} from 'lucide-react';

const Sidebar = () => {

    const mainNav = [
        { name: 'Home', path: '/', icon: Home },
        { name: 'Satellite Analysis', path: '/satellite-analysis', icon: Satellite },
        { name: 'Change Detection', path: '/change-detection', icon: RefreshCcw },
        { name: 'Live Detection / Risk', path: '/live-risk-intelligence', icon: Radio },
        { name: 'Job Monitoring', path: '/live-monitoring', icon: Settings },
        { name: 'Visual Grounding', path: '/visual-grounding', icon: MapPin },
        { name: 'Disaster Intelligence', path: '/disaster-intelligence', icon: Siren },
    ];

    const disasterNav = [
        { name: 'Flood Detection', path: '/flood-intelligence', icon: Waves },
        { name: 'Glacier & GLOF', path: '/glacier-intelligence', icon: MountainSnow },
        { name: 'Landslide Risk', path: '/landslide-intelligence', icon: Mountain },
        { name: 'Wildfire Risk', path: '/wildfire-intelligence', icon: Flame },
    ];

    const systemNav = [
        { name: 'Reports', path: '/reports', icon: FileText },
        { name: 'Settings', path: '/settings', icon: Settings },
        { name: 'Help & Support', path: '/support', icon: HelpCircle },
    ];

    const NavGroup = ({ items, title }) => (
        <div className="mb-6">
            {title && <div className="px-6 mb-3 text-[10px] font-bold text-slate-500 uppercase tracking-widest">{title}</div>}
            <nav className="space-y-1 px-4">
                {items.map((item) => (
                    <NavLink
                        key={item.name}
                        to={item.path}
                        className={({ isActive }) =>
                            `flex items-center px-4 py-2.5 rounded-xl transition-all duration-200 ${isActive
                                ? 'bg-blue-600/90 text-white shadow-lg'
                                : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
                            }`
                        }
                    >
                        {({ isActive }) => (
                            <>
                                <item.icon className="w-4 h-4 mr-3" />
                                <span className={`text-sm ${isActive ? 'font-semibold' : 'font-medium'}`}>{item.name}</span>
                            </>
                        )}
                    </NavLink>
                ))}
            </nav>
        </div>
    );

    return (
        <div className="w-[260px] h-screen bg-[#0b1120] border-r border-slate-800 flex flex-col shrink-0">
            {/* Branding */}
            <div className="p-6 flex items-center mb-2">
                <div className="p-1.5 rounded-lg bg-blue-600 mr-3">
                    <Globe2 className="w-5 h-5 text-white" />
                </div>
                <div>
                    <h1 className="text-lg font-bold text-white leading-tight">SatQuery</h1>
                    <p className="text-[9px] font-bold tracking-[0.1em] text-blue-400 uppercase">Agentic AI</p>
                </div>
            </div>

            {/* Navigation Lists */}
            <div className="flex-1 overflow-y-auto custom-scrollbar">
                <NavGroup items={mainNav} />
                <NavGroup items={disasterNav} title="Disaster Modules" />
                <NavGroup items={systemNav} title="System" />
            </div>

            {/* Bottom Panel */}
            <div className="p-4 mx-4 mb-4 rounded-xl border border-slate-800 bg-slate-900/50 flex flex-col items-center justify-center text-center">
                <Globe2 className="w-8 h-8 text-blue-500 mb-2 opacity-80" />
                <p className="text-[10px] text-slate-400 font-medium leading-relaxed">
                    Earth's data.<br />
                    Smarter decisions.<br />
                    Greater impact.
                </p>
            </div>
        </div>
    );
};

export default Sidebar;
