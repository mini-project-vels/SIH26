import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Brain, Satellite, Activity, FileSearch, ShieldAlert } from 'lucide-react';

const steps = [
    { text: "Understanding Query...", icon: Brain },
    { text: "Processing Satellite Image...", icon: Satellite },
    { text: "Running AI Analysis...", icon: Activity },
    { text: "Extracting Detections...", icon: FileSearch },
    { text: "Calculating Intelligence & Risk...", icon: ShieldAlert },
];

const AnalysisLoader = () => {
    const [currentStep, setCurrentStep] = useState(0);

    useEffect(() => {
        const timer = setInterval(() => {
            setCurrentStep((prev) => (prev < steps.length - 1 ? prev + 1 : prev));
        }, 2500);
        return () => clearInterval(timer);
    }, []);

    return (
        <div className="w-full py-12 flex flex-col items-center justify-center">
            <div className="relative w-24 h-24 mb-8">
                <div className="absolute inset-0 border-4 border-slate-700 rounded-full"></div>
                <div className="absolute inset-0 border-4 border-accent-blue rounded-full border-t-transparent animate-spin"></div>
                <div className="absolute inset-0 flex items-center justify-center text-accent-blue">
                    <Brain className="w-8 h-8 animate-pulse" />
                </div>
            </div>

            <div className="h-8 relative w-full max-w-sm flex justify-center">
                <AnimatePresence mode="wait">
                    <motion.div
                        key={currentStep}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        transition={{ duration: 0.3 }}
                        className="flex items-center space-x-3 absolute"
                    >
                        {React.createElement(steps[currentStep].icon, { className: "w-5 h-5 text-accent-blue" })}
                        <span className="text-slate-300 font-medium text-lg">{steps[currentStep].text}</span>
                    </motion.div>
                </AnimatePresence>
            </div>
        </div>
    );
};

export default AnalysisLoader;
