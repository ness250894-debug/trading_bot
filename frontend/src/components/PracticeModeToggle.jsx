import React from 'react';
import { Power } from 'lucide-react';

const PracticeModeToggle = ({ isPracticeMode, onToggle, isFreePlan }) => {
    return (
        <div className="flex items-center gap-3 bg-white/5 p-2 pr-4 rounded-xl border border-white/5">
            <button
                onClick={() => {
                    if (isFreePlan) return;
                    onToggle(!isPracticeMode);
                }}
                disabled={isFreePlan}
                className={`
                    relative w-12 h-7 rounded-full transition-colors duration-200 ease-in-out focus:outline-none
                    ${isPracticeMode ? 'bg-primary' : 'bg-gray-700'}
                    ${isFreePlan ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                `}
                title={isFreePlan ? "Upgrade to enable Real Trading" : "Toggle Practice Mode"}
            >
                <span
                    className={`
                        block w-5 h-5 bg-white rounded-full shadow transform transition-transform duration-200 ease-in-out mt-1 ml-1
                        ${isPracticeMode ? 'translate-x-5' : 'translate-x-0'}
                    `}
                />
            </button>
            <div className="flex flex-col">
                <span className={`text-sm font-semibold ${isPracticeMode ? 'text-primary' : 'text-gray-400'}`}>
                    {isPracticeMode ? 'Practice Mode' : 'Real Trading'}
                </span>
                {isFreePlan && (
                    <span className="text-[10px] text-muted-foreground">Free Plan Limited</span>
                )}
            </div>
        </div>
    );
};

export default PracticeModeToggle;
