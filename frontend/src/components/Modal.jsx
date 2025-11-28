import React, { createContext, useContext, useState, useCallback } from 'react';
import { X, AlertTriangle } from 'lucide-react';
import { AnimatePresence, motion } from 'framer-motion';

const ModalContext = createContext(null);

export const useModal = () => {
    const context = useContext(ModalContext);
    if (!context) {
        throw new Error('useModal must be used within a ModalProvider');
    }
    return context;
};

export const ModalProvider = ({ children }) => {
    const [modal, setModal] = useState(null);

    const confirm = useCallback(({ title, message, onConfirm, onCancel, confirmText = 'Confirm', cancelText = 'Cancel', type = 'danger' }) => {
        setModal({
            isOpen: true,
            title,
            message,
            onConfirm: () => {
                if (onConfirm) onConfirm();
                close();
            },
            onCancel: () => {
                if (onCancel) onCancel();
                close();
            },
            confirmText,
            cancelText,
            type
        });
    }, []);

    const close = useCallback(() => {
        setModal(null);
    }, []);

    return (
        <ModalContext.Provider value={{ confirm, close }}>
            {children}
            <AnimatePresence>
                {modal && (
                    <>
                        {/* Backdrop */}
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            onClick={close}
                            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[100]"
                        />
                        {/* Modal */}
                        <div className="fixed inset-0 flex items-center justify-center z-[101] pointer-events-none">
                            <motion.div
                                initial={{ opacity: 0, scale: 0.95, y: 20 }}
                                animate={{ opacity: 1, scale: 1, y: 0 }}
                                exit={{ opacity: 0, scale: 0.95, y: 20 }}
                                className="bg-[#0f172a] border border-white/10 rounded-2xl shadow-2xl w-full max-w-md overflow-hidden pointer-events-auto"
                            >
                                <div className="p-6">
                                    <div className="flex items-start gap-4">
                                        <div className={`p-3 rounded-full ${modal.type === 'danger' ? 'bg-red-500/10 text-red-500' : 'bg-blue-500/10 text-blue-500'}`}>
                                            <AlertTriangle size={24} />
                                        </div>
                                        <div className="flex-1">
                                            <h3 className="text-lg font-bold text-foreground mb-2">{modal.title}</h3>
                                            <p className="text-muted-foreground text-sm leading-relaxed">
                                                {modal.message}
                                            </p>
                                        </div>
                                    </div>
                                </div>
                                <div className="bg-white/5 p-4 flex justify-end gap-3">
                                    <button
                                        onClick={modal.onCancel}
                                        className="px-4 py-2 text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-white/5 rounded-lg transition-colors"
                                    >
                                        {modal.cancelText}
                                    </button>
                                    <button
                                        onClick={modal.onConfirm}
                                        className={`px-4 py-2 text-sm font-medium text-white rounded-lg shadow-lg transition-all ${modal.type === 'danger'
                                                ? 'bg-red-500 hover:bg-red-600 shadow-red-500/20'
                                                : 'bg-primary hover:bg-primary/90 shadow-primary/20'
                                            }`}
                                    >
                                        {modal.confirmText}
                                    </button>
                                </div>
                            </motion.div>
                        </div>
                    </>
                )}
            </AnimatePresence>
        </ModalContext.Provider>
    );
};
