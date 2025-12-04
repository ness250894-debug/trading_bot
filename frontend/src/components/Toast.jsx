import React, { useState, useCallback } from 'react';
import { X, CheckCircle, AlertCircle, Info, AlertTriangle } from 'lucide-react';
import { AnimatePresence, motion } from 'framer-motion';
import { ToastContext } from './ToastContext';





const Toast = ({ id, type, message, onClose }) => {
    const icons = {
        success: <CheckCircle size={20} className="text-green-400" />,
        error: <AlertCircle size={20} className="text-red-400" />,
        info: <Info size={20} className="text-blue-400" />,
        warning: <AlertTriangle size={20} className="text-yellow-400" />
    };

    const bgColors = {
        success: 'bg-green-500/10 border-green-500/20',
        error: 'bg-red-500/10 border-red-500/20',
        info: 'bg-blue-500/10 border-blue-500/20',
        warning: 'bg-yellow-500/10 border-yellow-500/20'
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 50, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9, transition: { duration: 0.2 } }}
            layout
            className={`
                flex items-center gap-3 p-4 rounded-xl border backdrop-blur-md shadow-lg min-w-[300px] max-w-md pointer-events-auto
                ${bgColors[type] || bgColors.info}
            `}
        >
            <div className="shrink-0">{icons[type] || icons.info}</div>
            <p className="text-sm font-medium text-foreground flex-1">{message}</p>
            <button
                onClick={() => onClose(id)}
                className="p-1 hover:bg-white/10 rounded-full transition-colors text-muted-foreground hover:text-foreground"
            >
                <X size={16} />
            </button>
        </motion.div>
    );
};

export const ToastProvider = ({ children }) => {
    const [toasts, setToasts] = useState([]);

    const removeToast = useCallback((id) => {
        setToasts(prev => prev.filter(t => t.id !== id));
    }, []);

    const addToast = useCallback((message, type = 'info', duration = 5000) => {
        const id = Math.random().toString(36).substr(2, 9);
        setToasts(prev => [...prev, { id, message, type }]);

        if (duration) {
            setTimeout(() => {
                removeToast(id);
            }, duration);
        }
    }, [removeToast]);

    const success = (msg) => addToast(msg, 'success');
    const error = (msg) => addToast(msg, 'error');
    const info = (msg) => addToast(msg, 'info');
    const warning = (msg) => addToast(msg, 'warning');

    return (
        <ToastContext.Provider value={{ addToast, removeToast, success, error, info, warning }}>
            {children}
            <div className="fixed bottom-4 left-4 z-[100] flex flex-col gap-2 pointer-events-none">
                <AnimatePresence mode="popLayout">
                    {toasts.map(toast => (
                        <Toast key={toast.id} {...toast} onClose={removeToast} />
                    ))}
                </AnimatePresence>
            </div>
        </ToastContext.Provider>
    );
};
