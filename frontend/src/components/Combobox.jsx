import React, { useState, useRef, useEffect } from 'react';
import { ChevronDown, Check } from 'lucide-react';

export default function Combobox({ 
    options = [], 
    value, 
    onChange, 
    placeholder = "Select or type...", 
    className = "" 
}) {
    const [isOpen, setIsOpen] = useState(false);
    const [inputValue, setInputValue] = useState(value || '');
    const wrapperRef = useRef(null);

    useEffect(() => {
        setInputValue(value || '');
    }, [value]);

    useEffect(() => {
        function handleClickOutside(event) {
            if (wrapperRef.current && !wrapperRef.current.contains(event.target)) {
                setIsOpen(false);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, [wrapperRef]);

    const handleInputChange = (e) => {
        const val = e.target.value.toUpperCase();
        setInputValue(val);
        onChange(val);
        setIsOpen(true);
    };

    const handleSelect = (option) => {
        setInputValue(option);
        onChange(option);
        setIsOpen(false);
    };

    const filteredOptions = options.filter(opt => 
        opt.toUpperCase().includes(inputValue.toUpperCase())
    );

    return (
        <div className={`relative ${className}`} ref={wrapperRef}>
            <div className="relative">
                <input
                    type="text"
                    value={inputValue}
                    onChange={handleInputChange}
                    onFocus={() => setIsOpen(true)}
                    placeholder={placeholder}
                    className="w-full bg-black/20 border border-white/10 rounded-lg pl-3 pr-10 py-1.5 text-sm focus:border-primary/50 outline-none uppercase text-white placeholder-white/30"
                />
                <button
                    type="button"
                    onClick={() => setIsOpen(!isOpen)}
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-white transition-colors"
                >
                    <ChevronDown size={16} />
                </button>
            </div>

            {isOpen && (
                <div className="absolute z-50 w-full mt-1 bg-[#1a1b26] border border-white/10 rounded-lg shadow-xl max-h-60 overflow-y-auto custom-scrollbar">
                    {filteredOptions.length > 0 ? (
                        filteredOptions.map((option) => (
                            <button
                                key={option}
                                type="button"
                                onClick={() => handleSelect(option)}
                                className="w-full text-left px-3 py-2 text-sm hover:bg-white/10 transition-colors flex items-center justify-between group"
                            >
                                <span className="text-gray-300 group-hover:text-white">{option}</span>
                                {value === option && <Check size={14} className="text-primary" />}
                            </button>
                        ))
                    ) : (
                        <div className="px-3 py-2 text-xs text-muted-foreground">
                            No matches found. Type to add custom.
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
