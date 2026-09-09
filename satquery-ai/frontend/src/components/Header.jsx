import React from 'react';
import { User, Bell } from 'lucide-react';

const Header = () => {
    return (
        <header className="h-20 flex items-center justify-between px-8 shrink-0 bg-transparent">
            <div className="flex flex-col">
                <h1 className="text-xl font-bold text-white tracking-wide">
                    Multimodal Remote Sensing Intelligence Platform
                </h1>
                <span className="text-sm text-slate-500 mt-1">
                    Real-time insights. Safer tomorrow.
                </span>
            </div>

            <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2 bg-slate-900/80 border border-slate-700/50 px-4 py-2 rounded-full">
                    <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                    <span className="text-xs font-semibold text-slate-300">AI Agents Active</span>
                </div>

                <button className="w-10 h-10 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center hover:bg-slate-800 transition-colors">
                    <Bell className="w-4 h-4 text-slate-400" />
                </button>
                <button className="w-10 h-10 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center hover:bg-slate-700 transition-colors">
                    <User className="w-4 h-4 text-slate-300" />
                </button>
            </div>
        </header>
    );
};

export default Header;
