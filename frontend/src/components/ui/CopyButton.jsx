import React, { useState } from 'react';
import { Copy, Check } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import toast from 'react-hot-toast';

/**
 * Copy to Clipboard Button Component
 * Provides one-click copy functionality with visual feedback
 */
const CopyButton = ({
    text,
    label = "Copy",
    successLabel = "Copied!",
    showLabel = false,
    size = "md",
    variant = "ghost", // ghost, solid, outline
    className = "",
    onCopy,
    toastMessage = "Copied to clipboard!"
}) => {
    const [copied, setCopied] = useState(false);

    const sizeClasses = {
        sm: "p-1.5",
        md: "p-2",
        lg: "p-3"
    };

    const iconSizes = {
        sm: 14,
        md: 16,
        lg: 20
    };

    const variantClasses = {
        ghost: "hover:bg-white/10 text-muted-foreground hover:text-foreground",
        solid: "bg-primary/20 hover:bg-primary/30 text-primary",
        outline: "border border-white/10 hover:border-white/20 text-muted-foreground hover:text-foreground"
    };

    const handleCopy = async (e) => {
        e.stopPropagation();

        try {
            await navigator.clipboard.writeText(text);
            setCopied(true);

            if (toastMessage) {
                toast.success(toastMessage, {
                    duration: 2000,
                    position: 'bottom-right',
                    style: {
                        background: 'rgba(16, 185, 129, 0.1)',
                        border: '1px solid rgba(16, 185, 129, 0.2)',
                        color: '#10b981'
                    }
                });
            }

            if (onCopy) {
                onCopy(text);
            }

            setTimeout(() => setCopied(false), 2000);
        } catch (err) {
            toast.error("Failed to copy", {
                position: 'bottom-right'
            });
        }
    };

    return (
        <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleCopy}
            className={`
        inline-flex items-center gap-1.5 rounded-lg transition-all duration-200
        ${sizeClasses[size]}
        ${variantClasses[variant]}
        ${className}
      `}
            title={copied ? successLabel : label}
        >
            <AnimatePresence mode="wait">
                {copied ? (
                    <motion.div
                        key="check"
                        initial={{ scale: 0, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        exit={{ scale: 0, opacity: 0 }}
                        transition={{ duration: 0.15 }}
                    >
                        <Check size={iconSizes[size]} className="text-green-400" />
                    </motion.div>
                ) : (
                    <motion.div
                        key="copy"
                        initial={{ scale: 0, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        exit={{ scale: 0, opacity: 0 }}
                        transition={{ duration: 0.15 }}
                    >
                        <Copy size={iconSizes[size]} />
                    </motion.div>
                )}
            </AnimatePresence>

            {showLabel && (
                <span className="text-sm">
                    {copied ? successLabel : label}
                </span>
            )}
        </motion.button>
    );
};

/**
 * Copyable Text - Text with inline copy button
 */
export const CopyableText = ({
    text,
    displayText,
    truncate = false,
    maxLength = 20,
    className = ""
}) => {
    const display = displayText || text;
    const truncatedText = truncate && display.length > maxLength
        ? `${display.slice(0, maxLength)}...`
        : display;

    return (
        <span className={`inline-flex items-center gap-2 ${className}`}>
            <code className="text-sm font-mono bg-black/20 px-2 py-1 rounded">
                {truncatedText}
            </code>
            <CopyButton text={text} size="sm" />
        </span>
    );
};

/**
 * Copy Input Field - Input with copy button
 */
export const CopyInput = ({
    value,
    label,
    placeholder = "",
    className = ""
}) => (
    <div className={`space-y-2 ${className}`}>
        {label && (
            <label className="text-sm font-medium text-gray-300">{label}</label>
        )}
        <div className="flex items-center gap-2">
            <input
                type="text"
                value={value}
                readOnly
                placeholder={placeholder}
                className="flex-1 bg-black/20 border border-white/10 rounded-xl py-2.5 px-4 
                   text-white text-sm font-mono focus:outline-none"
            />
            <CopyButton text={value} variant="outline" />
        </div>
    </div>
);

export default CopyButton;
