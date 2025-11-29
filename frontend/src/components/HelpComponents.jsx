import React from 'react';
import { HelpCircle, Info } from 'lucide-react';

export function PageHeader({ title, description, children }) {
    return (
        <div className="mb-6">
            <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-purple-400 mb-2">
                {title}
            </h1>
            {description && (
                <p className="text-muted-foreground text-base leading-relaxed max-w-3xl">
                    {description}
                </p>
            )}
            {children}
        </div>
    );
}

export function InfoBox({ title, children, variant = 'info' }) {
    const variants = {
        info: 'bg-blue-500/10 border-blue-500/20 text-blue-300',
        tip: 'bg-green-500/10 border-green-500/20 text-green-300',
        warning: 'bg-yellow-500/10 border-yellow-500/20 text-yellow-300',
        help: 'bg-purple-500/10 border-purple-500/20 text-purple-300',
    };

    return (
        <div className={`p-4 rounded-xl border ${variants[variant]} mb-4`}>
            {title && (
                <div className="flex items-center gap-2 mb-2">
                    <Info size={18} />
                    <h3 className="font-semibold">{title}</h3>
                </div>
            )}
            <div className="text-sm leading-relaxed opacity-90">
                {children}
            </div>
        </div>
    );
}

export function HelpTooltip({ content }) {
    const [isVisible, setIsVisible] = React.useState(false);

    return (
        <div className="relative inline-block">
            <button
                type="button"
                onMouseEnter={() => setIsVisible(true)}
                onMouseLeave={() => setIsVisible(false)}
                className="p-1 text-muted-foreground hover:text-foreground transition-colors"
            >
                <HelpCircle size={16} />
            </button>
            {isVisible && (
                <div className="absolute left-0 top-full mt-1 z-50 w-64 p-3 bg-card border border-white/10 rounded-lg shadow-xl text-sm">
                    {content}
                </div>
            )}
        </div>
    );
}

export function FieldDescription({ label, description, tooltip, children }) {
    return (
        <div className="space-y-2">
            <div className="flex items-center gap-2">
                <label className="text-sm font-medium text-gray-300">{label}</label>
                {tooltip && <HelpTooltip content={tooltip} />}
            </div>
            {description && (
                <p className="text-xs text-muted-foreground">{description}</p>
            )}
            {children}
        </div>
    );
}

export function GettingStartedGuide({ steps }) {
    return (
        <InfoBox title="Getting Started" variant="help">
            <ol className="list-decimal list-inside space-y-2">
                {steps.map((step, index) => (
                    <li key={index} className="text-sm">{step}</li>
                ))}
            </ol>
        </InfoBox>
    );
}
