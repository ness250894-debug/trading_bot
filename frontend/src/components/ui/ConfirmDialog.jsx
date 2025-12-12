import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle, Trash2, XCircle, RefreshCw, Power, X, Check } from 'lucide-react';

/**
 * Confirmation Dialog Component
 * Modal for confirming destructive or important actions
 */

const ConfirmDialog = ({
    isOpen,
    onClose,
    onConfirm,
    title = "Are you sure?",
    message = "This action cannot be undone.",
    confirmText = "Confirm",
    cancelText = "Cancel",
    variant = "danger", // danger, warning, info
    icon: CustomIcon,
    isLoading = false
}) => {
    const variants = {
        danger: {
            icon: Trash2,
            iconBg: "bg-red-500/20",
            iconColor: "text-red-400",
            buttonBg: "bg-red-500 hover:bg-red-600",
            buttonText: "text-white"
        },
        warning: {
            icon: AlertTriangle,
            iconBg: "bg-yellow-500/20",
            iconColor: "text-yellow-400",
            buttonBg: "bg-yellow-500 hover:bg-yellow-600",
            buttonText: "text-black"
        },
        info: {
            icon: XCircle,
            iconBg: "bg-blue-500/20",
            iconColor: "text-blue-400",
            buttonBg: "bg-blue-500 hover:bg-blue-600",
            buttonText: "text-white"
        }
    };

    const config = variants[variant];
    const Icon = CustomIcon || config.icon;

    const handleConfirm = async () => {
        if (onConfirm) {
            await onConfirm();
        }
        onClose();
    };

    return (
        <AnimatePresence>
            {isOpen && (
                <>
                    {/* Backdrop */}
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={onClose}
                        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[100]"
                    />

                    {/* Dialog */}
                    <div className="fixed inset-0 flex items-center justify-center z-[101] p-4">
                        <motion.div
                            initial={{ opacity: 0, scale: 0.95, y: 20 }}
                            animate={{ opacity: 1, scale: 1, y: 0 }}
                            exit={{ opacity: 0, scale: 0.95, y: 20 }}
                            transition={{ duration: 0.2 }}
                            className="glass w-full max-w-md p-6 rounded-2xl border border-white/10"
                            onClick={(e) => e.stopPropagation()}
                        >
                            {/* Close button */}
                            <button
                                onClick={onClose}
                                className="absolute top-4 right-4 p-2 text-muted-foreground 
                          hover:text-foreground hover:bg-white/5 rounded-lg transition-colors"
                            >
                                <X size={18} />
                            </button>

                            {/* Icon */}
                            <div className="flex justify-center mb-4">
                                <div className={`p-4 rounded-full ${config.iconBg}`}>
                                    <Icon size={32} className={config.iconColor} />
                                </div>
                            </div>

                            {/* Content */}
                            <div className="text-center mb-6">
                                <h3 className="text-xl font-semibold text-foreground mb-2">
                                    {title}
                                </h3>
                                <p className="text-muted-foreground">
                                    {message}
                                </p>
                            </div>

                            {/* Actions */}
                            <div className="flex gap-3">
                                <button
                                    onClick={onClose}
                                    disabled={isLoading}
                                    className="flex-1 py-3 px-4 rounded-xl border border-white/10 
                            text-foreground hover:bg-white/5 transition-colors
                            disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    {cancelText}
                                </button>
                                <button
                                    onClick={handleConfirm}
                                    disabled={isLoading}
                                    className={`flex-1 py-3 px-4 rounded-xl ${config.buttonBg} ${config.buttonText}
                            font-medium transition-colors flex items-center justify-center gap-2
                            disabled:opacity-50 disabled:cursor-not-allowed`}
                                >
                                    {isLoading ? (
                                        <>
                                            <RefreshCw size={18} className="animate-spin" />
                                            Processing...
                                        </>
                                    ) : (
                                        <>
                                            <Check size={18} />
                                            {confirmText}
                                        </>
                                    )}
                                </button>
                            </div>
                        </motion.div>
                    </div>
                </>
            )}
        </AnimatePresence>
    );
};

/**
 * Pre-configured confirm dialogs for common actions
 */
export const DeleteConfirmDialog = ({ isOpen, onClose, onConfirm, itemName = "item", isLoading }) => (
    <ConfirmDialog
        isOpen={isOpen}
        onClose={onClose}
        onConfirm={onConfirm}
        title={`Delete ${itemName}?`}
        message={`Are you sure you want to delete this ${itemName}? This action cannot be undone.`}
        confirmText="Delete"
        variant="danger"
        icon={Trash2}
        isLoading={isLoading}
    />
);

export const StopBotConfirmDialog = ({ isOpen, onClose, onConfirm, botName, isLoading }) => (
    <ConfirmDialog
        isOpen={isOpen}
        onClose={onClose}
        onConfirm={onConfirm}
        title="Stop Bot?"
        message={`Are you sure you want to stop ${botName || 'this bot'}? Any open positions will remain open.`}
        confirmText="Stop Bot"
        variant="warning"
        icon={Power}
        isLoading={isLoading}
    />
);

export const ResetBalanceConfirmDialog = ({ isOpen, onClose, onConfirm, isLoading }) => (
    <ConfirmDialog
        isOpen={isOpen}
        onClose={onClose}
        onConfirm={onConfirm}
        title="Reset Practice Balance?"
        message="This will reset your practice balance to $1,000. Your trade history will be preserved."
        confirmText="Reset Balance"
        variant="info"
        icon={RefreshCw}
        isLoading={isLoading}
    />
);

export default ConfirmDialog;
