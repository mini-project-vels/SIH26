import React, { useCallback } from 'react';
import { UploadCloud, Image as ImageIcon, X } from 'lucide-react';

const ImageUploader = ({ label = 'Upload Image', file, setFile, preview, setPreview, onClear }) => {
    const handleFileChange = (e) => {
        const selected = e.target.files[0];
        if (selected) {
            setFile(selected);
            const objectUrl = URL.createObjectURL(selected);
            setPreview(objectUrl);
        }
    };

    const handleClear = (e) => {
        e.stopPropagation();
        setFile(null);
        if (preview) {
            URL.revokeObjectURL(preview);
        }
        setPreview(null);
        if (onClear) onClear();
    };

    return (
        <div className="w-full">
            <label className="block text-sm font-medium text-slate-400 mb-2">{label}</label>
            <div
                className={`relative border-2 border-dashed rounded-xl overflow-hidden transition-colors flex flex-col items-center justify-center p-4 bg-slate-900/50
          ${file ? 'border-accent-blue/50' : 'border-slate-700 hover:border-slate-500 hover:bg-slate-800'}
        `}
                style={{ minHeight: '160px' }}
            >
                <input
                    type="file"
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                    accept="image/png, image/jpeg, image/jpg, image/webp"
                    onChange={handleFileChange}
                    title=""
                />

                {preview ? (
                    <div className="relative w-full h-full flex items-center justify-center">
                        <img src={preview} alt="Preview" className="max-h-48 object-contain rounded-md" />
                        <button
                            onClick={handleClear}
                            className="absolute top-2 right-2 p-1.5 bg-red-500 hover:bg-red-600 rounded-full text-white z-10 transition-colors shadow-lg"
                        >
                            <X className="w-4 h-4" />
                        </button>
                    </div>
                ) : (
                    <div className="text-center pointer-events-none">
                        <div className="w-12 h-12 bg-slate-800 rounded-full flex items-center justify-center mx-auto mb-3 text-slate-400">
                            <UploadCloud className="w-6 h-6" />
                        </div>
                        <p className="text-sm font-medium text-slate-300">Click or drag image to upload</p>
                        <p className="text-xs text-slate-500 mt-1">PNG, JPG up to 10MB</p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default ImageUploader;
