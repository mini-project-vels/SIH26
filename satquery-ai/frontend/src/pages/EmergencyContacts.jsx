import React, { useState } from 'react';
import { Phone, Radio, Mail, MapPin, Building, Search, PhoneCall } from 'lucide-react';

const MOCK_CONTACTS = [
    {
        id: 1,
        region: "Northern Himalayan Sector",
        station: "Glacial Outpost Alpha",
        officer: "Cmdr. Rajeev Singh",
        role: "GLOF Assessment Lead",
        phone: "+91 98765 43210",
        radio: "VHF Ch 16 (156.800 MHz)",
        email: "alpha.glof@satquery.gov",
        status: "ACTIVE"
    },
    {
        id: 2,
        region: "Eastern Coastal Delta",
        station: "Flood Monitoring Station Beta",
        officer: "Dr. Ananya Desai",
        role: "Coastal Hydrologist",
        phone: "+91 87654 32109",
        radio: "UHF 400.150 MHz",
        email: "beta.flood@satquery.gov",
        status: "ACTIVE"
    },
    {
        id: 3,
        region: "Central Urban Basin",
        station: "Urban Emergency Command",
        officer: "Director Vikram Patel",
        role: "Disaster Response Coordinator",
        phone: "+91 76543 21098",
        radio: "TETRA Network ID 8892",
        email: "urban.command@satquery.gov",
        status: "STANDBY"
    },
    {
        id: 4,
        region: "Southern Forest Reserve",
        station: "Wildfire Watchtower Gamma",
        officer: "Capt. Meera Reddy",
        role: "Fire Hazard Specialist",
        phone: "+91 65432 10987",
        radio: "VHF Ch 09 (156.450 MHz)",
        email: "gamma.fire@satquery.gov",
        status: "ACTIVE"
    }
];

export default function EmergencyContacts() {
    const [searchTerm, setSearchTerm] = useState("");

    const filteredContacts = MOCK_CONTACTS.filter(contact =>
        contact.region.toLowerCase().includes(searchTerm.toLowerCase()) ||
        contact.station.toLowerCase().includes(searchTerm.toLowerCase()) ||
        contact.officer.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <div className="max-w-7xl mx-auto space-y-8 pb-12 animate-in fade-in zoom-in-95 duration-700">
            <div className="mb-8 flex flex-col md:flex-row md:items-end md:justify-between gap-4 border-b border-white/5 pb-6">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2 flex items-center">
                        <PhoneCall className="mr-3 text-accent-blue" />
                        Impact Zone Contacts
                    </h1>
                    <p className="text-slate-400">Emergency response stations, field officers, and radio frequencies.</p>
                </div>
                <div className="relative w-full md:w-72">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                        <Search className="h-5 w-5 text-slate-500" />
                    </div>
                    <input
                        type="text"
                        className="w-full bg-slate-900 border border-slate-700 rounded-lg pl-10 pr-4 py-2.5 text-slate-200 focus:outline-none focus:border-accent-blue focus:ring-1 focus:ring-accent-blue placeholder-slate-500"
                        placeholder="Search regions or officers..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-8">
                {filteredContacts.map((contact, idx) => (
                    <div
                        key={contact.id}
                        className="group relative bg-slate-900/40 backdrop-blur-md border border-slate-800 rounded-2xl overflow-hidden hover:-translate-y-1.5 transition-all duration-300 hover:border-accent-blue/30 hover:shadow-[0_0_30px_-5px_rgba(59,130,246,0.15)] animate-in fade-in slide-in-from-bottom-8"
                        style={{ animationFillMode: 'both', animationDelay: `${idx * 150}ms` }}
                    >
                        <div className="absolute inset-0 bg-gradient-to-br from-accent-blue/5 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none"></div>

                        <div className="flex border-b border-white/5 bg-black/20 p-5 items-center justify-between relative z-10">
                            <div className="flex items-center">
                                <div className="p-2 bg-slate-800/50 rounded-lg mr-3 border border-slate-700/50 group-hover:border-accent-blue/30 group-hover:text-accent-blue transition-colors">
                                    <Building className="w-5 h-5 text-slate-400 group-hover:text-accent-blue transition-colors" />
                                </div>
                                <h2 className="text-xl font-bold text-white tracking-wide">{contact.station}</h2>
                            </div>
                            <span className={`text-[10px] uppercase font-bold tracking-widest px-2 py-1 rounded-full ${contact.status === 'ACTIVE' ? 'bg-impact-green/20 text-impact-green border border-impact-green/30' : 'bg-yellow-500/20 text-yellow-500 border border-yellow-500/30'}`}>
                                {contact.status}
                            </span>
                        </div>
                        <div className="p-6 space-y-5 relative z-10">
                            <div className="flex items-start bg-slate-800/20 p-3 rounded-lg border border-white/5">
                                <MapPin className="w-4 h-4 mt-1 mr-3 text-accent-blue shrink-0 animate-pulse" />
                                <div>
                                    <div className="text-xs text-slate-500 uppercase font-bold tracking-wider">Jurisdiction / Region</div>
                                    <div className="text-slate-300 font-medium">{contact.region}</div>
                                </div>
                            </div>

                            <hr className="border-white/5" />

                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                                <div>
                                    <div className="text-xs text-slate-500 uppercase font-bold tracking-wider mb-2">Commanding Officer</div>
                                    <div className="text-white font-semibold text-lg">{contact.officer}</div>
                                    <div className="text-sm text-accent-blue/80 font-medium">{contact.role}</div>
                                </div>
                                <div className="space-y-4">
                                    <div className="flex items-center text-sm group/item">
                                        <div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center mr-3 group-hover/item:bg-accent-blue/20 transition-colors">
                                            <Phone className="w-4 h-4 text-accent-blue" />
                                        </div>
                                        <span className="text-slate-300 font-medium group-hover/item:text-white transition-colors">{contact.phone}</span>
                                    </div>
                                    <div className="flex items-center text-sm group/item">
                                        <div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center mr-3 group-hover/item:bg-impact-red/20 transition-colors">
                                            <Radio className="w-4 h-4 text-impact-red" />
                                        </div>
                                        <span className="text-slate-300 font-medium group-hover/item:text-white transition-colors">{contact.radio}</span>
                                    </div>
                                    <div className="flex items-center text-sm group/item">
                                        <div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center mr-3 group-hover/item:bg-slate-700 transition-colors">
                                            <Mail className="w-4 h-4 text-slate-400" />
                                        </div>
                                        <span className="text-slate-300 font-medium group-hover/item:text-white transition-colors">{contact.email}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            {filteredContacts.length === 0 && (
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-12 flex flex-col items-center justify-center text-slate-500">
                    <Search className="w-12 h-12 mb-3 text-slate-700" />
                    <p className="text-lg">No impact zone contacts found for "{searchTerm}"</p>
                </div>
            )}
        </div>
    );
}
