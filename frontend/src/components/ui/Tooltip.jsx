import React from 'react';
import { Info } from 'lucide-react';

const Tooltip = ({ content }) => (
    <div className="group relative inline-block ml-2">
        <Info size={14} className="text-muted-foreground hover:text-primary cursor-help transition-colors" />
        <div className="invisible group-hover:visible opacity-0 group-hover:opacity-100 transition-opacity absolute z-50 w-64 p-3 mt-2 text-xs text-popover-foreground bg-popover/90 backdrop-blur-md rounded-xl shadow-xl -left-28 border border-white/10 pointer-events-none">
            {content}
        </div>
    </div>
);

export default Tooltip;
