import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowUpRight } from 'lucide-react';
import ScrollExpand from '../components/ScrollExpand';

export default function Landing() {
    const navigate = useNavigate();

    return (
        <div className="bg-[#070b19] font-sans text-white selection:bg-blue-500 selection:text-white">
            <style>
                {`
          @keyframes float-slow {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-10px); }
          }
          @keyframes float-slower {
            0%, 100% { transform: translateY(0) rotate(0deg); }
            50% { transform: translateY(-15px) rotate(-1deg); }
          }
          .float-ani-1 { animation: float-slow 6s ease-in-out infinite; }
          .float-ani-2 { animation: float-slower 8s ease-in-out infinite; }
        `}
            </style>

            <div className="w-full relative">
                <ScrollExpand
                    src="https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?q=80&w=2600"
                    alt="Satellite"
                    scrollDistance={1.2}
                    useWindowScroll={true}
                    startWidth={65}
                    startHeight={85}
                    startRadius={32}
                    mediaZoom={1.2}
                    title={
                        <div className="relative w-full h-[100vh]">
                            {/* Background Gradients and Dotted Map */}
                            <div className="absolute inset-0 z-0 opacity-40 pointer-events-none" style={{ background: 'radial-gradient(circle at 70% 30%, #5b4636 0%, #070b19 60%)' }} />
                            <div className="absolute inset-0 z-0 opacity-30 pointer-events-none" style={{ background: 'radial-gradient(circle at 10% 80%, #0f3d8a 0%, transparent 60%)' }} />
                            <div className="absolute inset-0 z-0 opacity-[0.05] pointer-events-none mix-blend-screen" style={{ backgroundImage: 'radial-gradient(#ffffff 2px, transparent 2px)', backgroundSize: '24px 24px', backgroundPosition: '0 0' }} />

                            {/* Circular design rings around the satellite */}
                            <div className="absolute top-[40%] right-[10%] w-[40vw] h-[40vw] rounded-full border border-white/[0.08] z-0 pointer-events-none transform -translate-y-1/2 float-ani-1"></div>
                            <div className="absolute top-[40%] right-[5%] w-[50vw] h-[50vw] rounded-full border border-dashed border-white/[0.05] z-0 pointer-events-none transform -translate-y-1/2 float-ani-2" style={{ animationDuration: '15s' }}></div>

                            {/* MAIN CONTENT LAYER */}
                            <div className="relative z-40 px-6 lg:px-12 xl:px-16 pt-16 pb-8 h-full flex flex-col justify-between items-start text-left w-full pointer-events-none">

                                {/* Left Typography Block */}
                                <div className="max-w-2xl mt-8">
                                    <div className="inline-flex items-center bg-white/5 border border-white/10 rounded-full px-4 py-1.5 mb-8 backdrop-blur-sm">
                                        <div className="w-1.5 h-1.5 bg-white/80 rounded-full mr-2 shadow-[0_0_8px_white]"></div>
                                        <span className="text-[11px] font-semibold tracking-widest text-white/80 uppercase">REDEFINING CONNECTIVITY FROM SPACE</span>
                                    </div>

                                    <h1 className="text-[50px] sm:text-[70px] lg:text-[85px] xl:text-[105px] font-medium leading-[1] tracking-[-0.03em] text-white mb-8">
                                        <div className="mb-2 hover:translate-x-2 transition-transform duration-500 pointer-events-auto">Satellite Data</div>
                                        <div className="flex items-center mb-2 hover:translate-x-2 transition-transform duration-500 delay-75 pointer-events-auto">
                                            <div className="w-24 h-12 sm:w-32 sm:h-[68px] lg:h-[80px] lg:w-[150px] bg-[#1a1c23] border border-white/10 rounded-full mr-4 sm:mr-6 flex items-center p-2 relative shadow-inner">
                                                <div className="absolute right-2 w-8 h-8 sm:w-13 sm:h-13 lg:w-16 lg:h-16 bg-[#d6e184] rounded-full flex items-center justify-center shadow-lg transform hover:scale-105 transition-transform cursor-pointer">
                                                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#1a1c23" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="opacity-90">
                                                        <path d="M12 15l-3-3h6l-3 3z" /><path d="M12 9V2" /><circle cx="12" cy="12" r="9" />
                                                    </svg>
                                                </div>
                                            </div>
                                            <span>to Disaster</span>
                                        </div>
                                        <div className="hover:translate-x-2 transition-transform duration-500 delay-150 pointer-events-auto">Intelligence</div>
                                    </h1>
                                </div>

                                {/* Bottom Left Block */}
                                <div className="max-w-xs mt-12 pb-4 pointer-events-auto">
                                    <div className="flex space-x-4">
                                        {[
                                            <svg key="1" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"></path></svg>,
                                            <svg key="2" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><rect x="2" y="2" width="20" height="20" rx="5" ry="5"></rect><path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"></path><line x1="17.5" y1="6.5" x2="17.51" y2="6.5"></line></svg>,
                                            <svg key="3" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polygon points="3,11 11,11 11,3 21,3 21,13 13,13 13,21 3,21"></polygon></svg>,
                                            <svg key="4" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M2.5 22l6-4.5M2 2l12 18M22 2L9.5 20M22 22l-6-4.5"></path></svg>
                                        ].map((icon, idx) => (
                                            <div key={idx} className="w-11 h-11 rounded-full border border-white/20 flex items-center justify-center hover:bg-white/10 transition-all cursor-pointer hover:border-white/50 text-white/80 hover:text-white">
                                                {icon}
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                {/* 1. Enter Dashboard Card */}
                                <div className="absolute top-1/2 right-[8%] lg:right-[12%] -translate-y-1/2 z-50 hidden md:block pointer-events-auto">
                                    <div
                                        onClick={() => navigate('/dashboard')}
                                        className="group relative w-72 bg-[#070b19]/85 backdrop-blur-xl border border-white/10 hover:border-white/25 hover:bg-[#070b19]/95 rounded-[24px] p-6 cursor-pointer shadow-2xl transition-all duration-500 overflow-hidden"
                                    >
                                        <div className="flex justify-between items-start mb-8 relative z-10">
                                            <div className="flex items-center bg-white/5 border border-white/10 text-white/90 px-3 py-1.5 rounded-full text-[10px] font-bold tracking-widest uppercase">
                                                <span className="relative flex h-1.5 w-1.5 mr-2">
                                                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-slate-300 opacity-75"></span>
                                                    <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-white shadow-[0_0_8px_white]"></span>
                                                </span>
                                                System Live
                                            </div>
                                            <div className="w-10 h-10 rounded-full border border-white/10 bg-white/5 flex items-center justify-center group-hover:rotate-45 group-hover:bg-[#d6e184] group-hover:border-[#d6e184] group-hover:text-[#070b19] transition-all duration-500 text-white/70">
                                                <ArrowUpRight size={20} strokeWidth={2} />
                                            </div>
                                        </div>

                                        <div className="relative z-10">
                                            <h3 className="text-white text-2xl font-medium tracking-tight mb-2 group-hover:translate-x-1 transition-transform">Enter Dashboard</h3>
                                            <p className="text-[13px] text-white/50 leading-relaxed font-light">Access real-time satellite imagery and global disaster intelligence.</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    }
                />
            </div>
        </div >
    );
}
