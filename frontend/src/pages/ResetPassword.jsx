import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import api from '../lib/api';
import { Lock, Eye, EyeOff, Check, AlertCircle } from 'lucide-react';

export default function ResetPassword() {
    const [searchParams] = useSearchParams();
    const token = searchParams.get('token');

    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [showConfirmPassword, setShowConfirmPassword] = useState(false);

    const [status, setStatus] = useState('idle'); // idle, loading, success, error
    const [errorMessage, setErrorMessage] = useState('');
    const navigate = useNavigate();

    useEffect(() => {
        if (!token) {
            setStatus('error');
            setErrorMessage('Invalid or missing reset token.');
        }
    }, [token]);

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (password !== confirmPassword) {
            setErrorMessage("Passwords do not match");
            return;
        }

        setStatus('loading');
        setErrorMessage('');

        try {
            await api.post('/auth/reset-password', {
                token,
                new_password: password
            });
            setStatus('success');
            setTimeout(() => navigate('/'), 3000);
        } catch (err) {
            setStatus('error');
            setErrorMessage(err.response?.data?.detail || "Failed to reset password. Token may check expired.");
        }
    };

    // Password strength logic (reused)
    const getStrength = (pass) => {
        return {
            length: pass.length >= 8,
            upper: /[A-Z]/.test(pass),
            lower: /[a-z]/.test(pass),
            number: /[0-9]/.test(pass)
        };
    };
    const strength = getStrength(password);
    const validCount = Object.values(strength).filter(Boolean).length;
    const getStrengthColor = () => {
        if (validCount <= 1) return 'bg-red-500';
        if (validCount === 2) return 'bg-yellow-500';
        if (validCount === 3) return 'bg-blue-500';
        return 'bg-green-500';
    };

    if (status === 'success') {
        return (
            <div className="min-h-screen flex items-center justify-center p-4">
                <div className="glass w-full max-w-md p-8 rounded-2xl text-center">
                    <div className="w-16 h-16 bg-green-500/10 text-green-500 rounded-full flex items-center justify-center mx-auto mb-6">
                        <Check size={32} />
                    </div>
                    <h2 className="text-2xl font-bold mb-2">Password Reset!</h2>
                    <p className="text-muted-foreground mb-6">Your password has been successfully updated.</p>
                    <button onClick={() => navigate('/login')} className="bg-primary text-white px-6 py-2 rounded-lg">
                        Go to Login
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen flex items-center justify-center p-4">
            <div className="glass w-full max-w-md p-8 rounded-2xl">
                <div className="text-center mb-8">
                    <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-purple-400">
                        Reset Password
                    </h1>
                    <p className="text-muted-foreground mt-2">Enter your new secure password</p>
                </div>

                {errorMessage && (
                    <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-xl flex items-center gap-3 text-red-400">
                        <AlertCircle size={20} />
                        <span className="text-sm">{errorMessage}</span>
                    </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-5">
                    <div className="space-y-2">
                        <label className="text-sm font-medium text-gray-300">New Password</label>
                        <div className="relative">
                            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" size={18} />
                            <input
                                type={showPassword ? "text" : "password"}
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="w-full bg-black/20 border border-white/10 rounded-xl py-2.5 pl-10 pr-10 text-white focus:outline-none focus:border-primary/50 transition-colors"
                                placeholder="••••••••"
                                required
                            />
                            <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300">
                                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                            </button>
                        </div>
                    </div>

                    {/* Strength Meter */}
                    <div className="space-y-2 px-1 mb-4">
                        <div className="flex gap-1 h-1.5">
                            {[1, 2, 3, 4].map(i => (
                                <div key={i} className={`flex-1 rounded-full transition-all duration-300 ${validCount >= i ? getStrengthColor() : 'bg-white/10'}`} />
                            ))}
                        </div>
                        <div className="grid grid-cols-2 gap-2 text-xs text-muted-foreground pt-1">
                            <div className={`flex items-center gap-1.5 ${strength.length ? 'text-green-400 font-medium' : ''}`}>
                                {strength.length ? <Check size={12} strokeWidth={3} /> : <div className="w-3 h-3 rounded-full border border-current opacity-30" />} 8+ Chars
                            </div>
                            <div className={`flex items-center gap-1.5 ${strength.upper ? 'text-green-400 font-medium' : ''}`}>
                                {strength.upper ? <Check size={12} strokeWidth={3} /> : <div className="w-3 h-3 rounded-full border border-current opacity-30" />} Uppercase
                            </div>
                            <div className={`flex items-center gap-1.5 ${strength.lower ? 'text-green-400 font-medium' : ''}`}>
                                {strength.lower ? <Check size={12} strokeWidth={3} /> : <div className="w-3 h-3 rounded-full border border-current opacity-30" />} Lowercase
                            </div>
                            <div className={`flex items-center gap-1.5 ${strength.number ? 'text-green-400 font-medium' : ''}`}>
                                {strength.number ? <Check size={12} strokeWidth={3} /> : <div className="w-3 h-3 rounded-full border border-current opacity-30" />} Number
                            </div>
                        </div>
                    </div>

                    <div className="space-y-2">
                        <label className="text-sm font-medium text-gray-300">Confirm Password</label>
                        <div className="relative">
                            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" size={18} />
                            <input
                                type={showConfirmPassword ? "text" : "password"}
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
                                className="w-full bg-black/20 border border-white/10 rounded-xl py-2.5 pl-10 pr-10 text-white focus:outline-none focus:border-primary/50 transition-colors"
                                placeholder="••••••••"
                                required
                            />
                            <button type="button" onClick={() => setShowConfirmPassword(!showConfirmPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300">
                                {showConfirmPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                            </button>
                        </div>
                    </div>

                    <button
                        type="submit"
                        disabled={status === 'loading'}
                        className="w-full bg-primary hover:bg-primary/90 text-primary-foreground font-bold py-3 rounded-xl transition-all duration-300 shadow-lg shadow-primary/25 disabled:opacity-50"
                    >
                        {status === 'loading' ? 'Resetting...' : 'Reset Password'}
                    </button>
                </form>
            </div>
        </div>
    );
}
