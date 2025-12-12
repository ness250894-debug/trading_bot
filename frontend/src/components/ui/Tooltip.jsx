import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { HelpCircle, Info, AlertCircle } from 'lucide-react';
import * as TooltipPrimitive from '@radix-ui/react-tooltip';

/**
 * Tooltip Component
 * Provides hover tooltips with helpful explanations
 */

// Simple tooltip using CSS
export const SimpleTooltip = ({
    content,
    children,
    position = "top",
    className = ""
}) => {
    const positions = {
        top: "bottom-full left-1/2 -translate-x-1/2 mb-2",
        bottom: "top-full left-1/2 -translate-x-1/2 mt-2",
        left: "right-full top-1/2 -translate-y-1/2 mr-2",
        right: "left-full top-1/2 -translate-y-1/2 ml-2"
    };

    const arrowPositions = {
        top: "top-full left-1/2 -translate-x-1/2 border-t-white/20 border-x-transparent border-b-transparent",
        bottom: "bottom-full left-1/2 -translate-x-1/2 border-b-white/20 border-x-transparent border-t-transparent",
        left: "left-full top-1/2 -translate-y-1/2 border-l-white/20 border-y-transparent border-r-transparent",
        right: "right-full top-1/2 -translate-y-1/2 border-r-white/20 border-y-transparent border-l-transparent"
    };

    return (
        <div className={`group relative inline-flex ${className}`}>
            {children}
            <div className={`
        absolute ${positions[position]} z-50
        opacity-0 invisible group-hover:opacity-100 group-hover:visible
        transition-all duration-200 pointer-events-none
      `}>
                <div className="bg-gray-900/95 backdrop-blur-sm border border-white/10 
                       rounded-lg px-3 py-2 text-sm text-gray-200 shadow-xl
                       whitespace-nowrap max-w-xs">
                    {content}
                </div>
                <div className={`
          absolute ${arrowPositions[position]}
          border-4
        `} />
            </div>
        </div>
    );
};

/**
 * Info Tooltip - Icon with tooltip
 */
export const InfoTooltip = ({
    content,
    iconSize = 16,
    variant = "info", // info, help, warning
    position = "top",
    className = ""
}) => {
    const icons = {
        info: Info,
        help: HelpCircle,
        warning: AlertCircle
    };

    const colors = {
        info: "text-blue-400",
        help: "text-gray-400 hover:text-gray-300",
        warning: "text-yellow-400"
    };

    const Icon = icons[variant];

    return (
        <SimpleTooltip content={content} position={position}>
            <button
                type="button"
                className={`
          inline-flex items-center justify-center
          cursor-help transition-colors ${colors[variant]} ${className}
        `}
            >
                <Icon size={iconSize} />
            </button>
        </SimpleTooltip>
    );
};

/**
 * Label with Tooltip - Label text with info icon
 */
export const LabelWithTooltip = ({
    label,
    tooltip,
    htmlFor,
    required = false,
    className = ""
}) => (
    <label
        htmlFor={htmlFor}
        className={`flex items-center gap-2 text-sm font-medium text-gray-300 ${className}`}
    >
        <span>
            {label}
            {required && <span className="text-red-400 ml-0.5">*</span>}
        </span>
        <InfoTooltip content={tooltip} variant="help" iconSize={14} />
    </label>
);

/**
 * Radix UI based Tooltip (more robust)
 */
export const Tooltip = ({
    content,
    children,
    side = "top",
    align = "center",
    delayDuration = 200,
    className = ""
}) => (
    <TooltipPrimitive.Provider delayDuration={delayDuration}>
        <TooltipPrimitive.Root>
            <TooltipPrimitive.Trigger asChild>
                {children}
            </TooltipPrimitive.Trigger>
            <AnimatePresence>
                <TooltipPrimitive.Portal>
                    <TooltipPrimitive.Content
                        side={side}
                        align={align}
                        sideOffset={5}
                        asChild
                    >
                        <motion.div
                            initial={{ opacity: 0, scale: 0.95 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.95 }}
                            className={`
                bg-gray-900/95 backdrop-blur-sm border border-white/10 
                rounded-lg px-3 py-2 text-sm text-gray-200 shadow-xl
                z-50 max-w-xs ${className}
              `}
                        >
                            {content}
                            <TooltipPrimitive.Arrow className="fill-gray-900/95" />
                        </motion.div>
                    </TooltipPrimitive.Content>
                </TooltipPrimitive.Portal>
            </AnimatePresence>
        </TooltipPrimitive.Root>
    </TooltipPrimitive.Provider>
);

export default Tooltip;
