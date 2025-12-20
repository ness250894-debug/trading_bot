import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../lib/api';
import secureStorage from '../lib/secureStorage';
import { z } from 'zod';
import { loginSchema } from '../lib/validators';
import { Lock, Mail, AlertCircle, X, Eye, EyeOff } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useModal } from './Modal';

export default function LoginModal({ isOpen, onClose, onSwitchToSignup, onSuccess }) {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();
    const { show } = useModal();

    const handleForgotPassword = () => {
        onClose(); // Close existing login modal first
        show({
            title: 'Reset Password',
            content: <ForgotPasswordForm onClose={() => show(null)} />,
            type: 'info'
        });
    };

    // Helper component for the modal form
    const ForgotPasswordForm = ({ onClose }) => {
        const [resetEmail, setResetEmail] = useState('');
        const [status, setStatus] = useState('idle'); // idle, loading, success, error
        const [msg, setMsg] = useState('');

        const onResetSubmit = async (e) => {
            e.preventDefault();
            setStatus('loading');
            try {
                await api.post('/auth/forgot-password', { email: resetEmail });
                setStatus('success');
                setMsg('If this email is registered, you will receive a reset link shortly.');
            } catch (err) {
                setStatus('error');
                setMsg('Failed to process request. Please try again.');
            }
        };

        if (status === 'success') {
            return (
                <div className="text-center space-y-4">
                    <div className="p-3 bg-green-500/10 text-green-400 rounded-lg text-sm">
                        {msg}
                    </div>
                    <button onClick={onClose} className="text-sm text-muted-foreground hover:text-white">Close</button>
                </div>
            );
        }

        return (
            <form onSubmit={onResetSubmit} className="space-y-4">
                <p className="text-sm text-gray-300">Enter your email address and we'll send you a link to reset your password.</p>
                <div className="space-y-2">
                    <input
                        type="email"
                        value={resetEmail}
                        onChange={(e) => setResetEmail(e.target.value)}
                        className="w-full bg-black/20 border border-white/10 rounded-lg py-2 px-3 text-white focus:outline-none focus:border-primary/50"
                        placeholder="name@example.com"
                        required
                    />
                </div>
                {status === 'error' && <p className="text-xs text-red-400">{msg}</p>}
                <button
                    type="submit"
                    disabled={status === 'loading'}
                    className="w-full bg-primary hover:bg-primary/90 text-white rounded-lg py-2 font-medium disabled:opacity-50"
                >
                    {status === 'loading' ? 'Sending...' : 'Send Reset Link'}
                </button>
            </form>
        );
    };

    // Clear form and errors when modal opens/closes
    useEffect(() => {
        if (!isOpen) {
            setEmail('');
            setPassword('');
            setError('');
            setShowPassword(false);
        }
    }, [isOpen]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            // Validate input with Zod
            const validated = loginSchema.parse({
                email: email.trim(),
                password,
            });

            const formData = new FormData();
            formData.append('username', validated.email);
            formData.append('password', validated.password);

            const response = await api.post('/auth/login', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });

            secureStorage.setToken(response.data.access_token);
            onClose();
            if (onSuccess) {
                onSuccess();
            } else {
                navigate('/main');
            }
        } catch (err) {
            // Handle validation errors
            if (err instanceof z.ZodError) {
                setError(err.errors[0].message);
            } else {
                setError(err.response?.data?.detail || 'Invalid email or password. Please try again.');
            }
        } finally {
            setLoading(false);
        }
    };

    if (!isOpen) return null;

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
                    {/* Modal */}
                    <div className="fixed inset-0 flex items-center justify-center z-[101] pointer-events-none p-4">
                        <motion.div
                            initial={{ opacity: 0, scale: 0.95, y: 20 }}
                            animate={{ opacity: 1, scale: 1, y: 0 }}
                            exit={{ opacity: 0, scale: 0.95, y: 20 }}
                            transition={{ duration: 0.2 }}
                            className="glass w-full max-w-md p-8 rounded-2xl border border-white/10 pointer-events-auto relative"
                            onClick={(e) => e.stopPropagation()}
                        >
                            {/* Close button */}
                            <button
                                onClick={onClose}
                                className="absolute top-4 right-4 p-2 text-muted-foreground hover:text-foreground hover:bg-white/5 rounded-lg transition-colors"
                            >
                                <X size={20} />
                            </button>

                            <div className="text-center mb-8">
                                <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-purple-400">
                                    Welcome Back
                                </h1>
                                <p className="text-muted-foreground mt-2">Sign in to manage your trading bot</p>
                            </div>

                            {error && (
                                <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-xl flex items-center gap-3 text-red-400">
                                    <AlertCircle size={20} />
                                    <span className="text-sm">{error}</span>
                                </div>
                            )}

                            <form onSubmit={handleSubmit} className="space-y-6">
                                <div className="space-y-2">
                                    <label className="text-sm font-medium text-gray-300">Email</label>
                                    <div className="relative">
                                        <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" size={18} />
                                        <input
                                            type="email"
                                            value={email}
                                            onChange={(e) => setEmail(e.target.value)}
                                            className="w-full bg-black/20 border border-white/10 rounded-xl py-2.5 pl-10 pr-4 text-white focus:outline-none focus:border-primary/50 transition-colors"
                                            placeholder="name@example.com"
                                            required
                                        />
                                    </div>
                                </div>

                                <div className="space-y-2">
                                    <label className="text-sm font-medium text-gray-300">Password</label>
                                    <div className="relative">
                                        <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" size={18} />
                                        <input
                                            type={showPassword ? "text" : "password"}
                                            value={password}
                                            onChange={(e) => setPassword(e.target.value)}
                                            className="w-full bg-black/20 border border-white/10 rounded-xl py-2.5 pl-10 pr-12 text-white focus:outline-none focus:border-primary/50 transition-colors"
                                            placeholder="••••••••"
                                            required
                                        />
                                        <button
                                            type="button"
                                            onClick={() => setShowPassword(!showPassword)}
                                            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300 transition-colors"
                                        >
                                            {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                                        </button>
                                    </div>
                                </div>

                                <div className="flex justify-end">
                                    <button
                                        type="button"
                                        onClick={handleForgotPassword}
                                        className="text-sm text-primary hover:text-primary/80 transition-colors"
                                    >
                                        Forgot password?
                                    </button>
                                </div>

                                <button
                                    type="submit"
                                    disabled={loading}
                                    className="w-full bg-primary hover:bg-primary/90 text-primary-foreground font-bold py-3 rounded-xl transition-all duration-300 shadow-lg shadow-primary/25 disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    {loading ? 'Signing in...' : 'Sign In'}
                                </button>
                            </form>

                            <p className="text-center mt-6 text-sm text-muted-foreground">
                                Don't have an account?{' '}
                                <button
                                    onClick={onSwitchToSignup}
                                    className="text-primary hover:text-primary/80 font-medium transition-colors"
                                >
                                    Sign up
                                </button>
                            </p>
                        </motion.div>
                    </div>
                </>
            )}
        </AnimatePresence>
    );
}
