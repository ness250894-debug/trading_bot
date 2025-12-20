import React from 'react';
import Tooltip from './Tooltip';

const SliderInput = ({ label, value, min, max, step, onChange, description }) => {
    return (
        <div className="mb-3 group">
            <div className="flex justify-between items-center mb-1">
                <label className="text-xs font-medium text-foreground flex items-center gap-1 group-hover:text-primary transition-colors">
                    {label}
                    {description && <Tooltip content={description} />}
                </label>
            </div>
            <div className="flex items-center gap-2">
                <input
                    type="range"
                    min={min}
                    max={max}
                    step={step}
                    value={value || min}
                    onChange={(e) => onChange(Number(e.target.value))}
                    className="w-full h-1.5 bg-secondary rounded-lg appearance-none cursor-pointer accent-primary hover:accent-primary/80 transition-all"
                />
                <input
                    type="number"
                    min={min}
                    max={max}
                    step={step}
                    value={value}
                    onChange={(e) => {
                        const val = e.target.value;
                        if (val === '') onChange('');
                        else onChange(Number(val));
                    }}
                    className="w-16 bg-black/20 border border-white/10 rounded-md px-2 py-1 text-xs text-right focus:ring-1 focus:ring-primary/50 outline-none transition-all"
                />
            </div>
        </div>
    );
};

export default SliderInput;
