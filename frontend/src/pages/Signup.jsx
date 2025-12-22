import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from '../lib/api';
import secureStorage from '../lib/secureStorage';
import { z } from 'zod';
import { signupSchema } from '../lib/validators';
import { Lock, Mail, AlertCircle, UserPlus, User, Eye, EyeOff, Check, X } from 'lucide-react';


export default function Signup() {
    const [email, setEmail] = useState('');
    const [nickname, setNickname] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [showConfirmPassword, setShowConfirmPassword] = useState(false);
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');

        setLoading(true);

        try {
            // Validate input with Zod
            const validated = signupSchema.parse({
                email: email.trim(),
                password,
                confirmPassword,
                nickname: nickname.trim() || undefined,
            });

            // Proceed with API call if validation passes
            const response = await api.post('/auth/signup', {
                email: validated.email,
                nickname: validated.nickname || null,
                password: validated.password
            });

            secureStorage.setToken(response.data.access_token);

            // Verify the token works before redirecting
            // This prevents race conditions where the DB hasn't fully committed the new user
            let verified = false;
            for (let i = 0; i < 3; i++) {
                try {
                    await api.get('/auth/me');
                    verified = true;
                    break;
                } catch (e) {
                    // Wait 500ms and retry
                    await new Promise(resolve => setTimeout(resolve, 500));
                }
            }

            if (verified) {
                // Force a hard reload to ensure all auth state is correctly initialized
                window.location.href = '/main';
            } else {
                throw new Error("Account created but failed to verify login. Please log in manually.");
            }
        } catch (err) {
            // Handle validation errors
            if (err instanceof z.ZodError) {
                setError(err.errors[0].message);
            } else {
                setError(err.response?.data?.detail || 'Signup failed');
            }
        } finally {
            setLoading(false);
        }
    };

    // Password strength calculation
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
    const strengthScore = (validCount / 4) * 100;

    const getStrengthColor = () => {
        if (validCount <= 1) return 'bg-red-500';
        if (validCount === 2) return 'bg-yellow-500';
        if (validCount === 3) return 'bg-blue-500';
        return 'bg-green-500';
    };

    return (
        <div className="min-h-screen flex items-center justify-center p-4">
            <div className="glass w-full max-w-md p-8 rounded-2xl">
                <div className="text-center mb-8">
                    <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-purple-400">
                        Create Account
                    </h1>
                    <p className="text-muted-foreground mt-2">Start your automated trading journey</p>
                </div>

                {error && (
                    <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-xl flex items-center gap-3 text-red-400">
                        <AlertCircle size={20} />
                        <span className="text-sm">{error}</span>
                    </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-5">
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
                        <label className="text-sm font-medium text-gray-300">Nickname (Optional)</label>
                        <div className="relative">
                            <User className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" size={18} />
                            <input
                                type="text"
                                value={nickname}
                                onChange={(e) => setNickname(e.target.value)}
                                className="w-full bg-black/20 border border-white/10 rounded-xl py-2.5 pl-10 pr-4 text-white focus:outline-none focus:border-primary/50 transition-colors"
                                placeholder="Your display name"
                            />
                        </div>
                        <p className="text-xs text-muted-foreground">This is how other users will see you</p>
                    </div>

                    <div className="space-y-2">
                        <label className="text-sm font-medium text-gray-300">Password</label>
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
                            <button
                                type="button"
                                onClick={() => setShowPassword(!showPassword)}
                                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300 transition-colors"
                            >
                                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                            </button>
                        </div>
                    </div>

                    <div className="space-y-2 px-1 mb-4">
                        <div className="flex gap-1 h-1.5">
                            <div className={`flex-1 rounded-full transition-all duration-300 ${validCount >= 1 ? getStrengthColor() : 'bg-white/10'}`} />
                            <div className={`flex-1 rounded-full transition-all duration-300 ${validCount >= 2 ? getStrengthColor() : 'bg-white/10'}`} />
                            <div className={`flex-1 rounded-full transition-all duration-300 ${validCount >= 3 ? getStrengthColor() : 'bg-white/10'}`} />
                            <div className={`flex-1 rounded-full transition-all duration-300 ${validCount >= 4 ? getStrengthColor() : 'bg-white/10'}`} />
                        </div>
                        <div className="grid grid-cols-2 gap-2 text-xs text-muted-foreground pt-1">
                            <div className={`flex items-center gap-1.5 transition-colors ${strength.length ? 'text-green-400 font-medium' : ''}`}>
                                {strength.length ? <Check size={12} strokeWidth={3} /> : <div className="w-3 h-3 rounded-full border border-current opacity-30" />}
                                8+ Characters
                            </div>
                            <div className={`flex items-center gap-1.5 transition-colors ${strength.upper ? 'text-green-400 font-medium' : ''}`}>
                                {strength.upper ? <Check size={12} strokeWidth={3} /> : <div className="w-3 h-3 rounded-full border border-current opacity-30" />}
                                Uppercase Letter
                            </div>
                            <div className={`flex items-center gap-1.5 transition-colors ${strength.lower ? 'text-green-400 font-medium' : ''}`}>
                                {strength.lower ? <Check size={12} strokeWidth={3} /> : <div className="w-3 h-3 rounded-full border border-current opacity-30" />}
                                Lowercase Letter
                            </div>
                            <div className={`flex items-center gap-1.5 transition-colors ${strength.number ? 'text-green-400 font-medium' : ''}`}>
                                {strength.number ? <Check size={12} strokeWidth={3} /> : <div className="w-3 h-3 rounded-full border border-current opacity-30" />}
                                Number
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
                            <button
                                type="button"
                                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300 transition-colors"
                            >
                                {showConfirmPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                            </button>
                        </div>
                    </div>

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full bg-primary hover:bg-primary/90 text-primary-foreground font-bold py-3 rounded-xl transition-all duration-300 shadow-lg shadow-primary/25 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                    >
                        {loading ? 'Creating Account...' : <><UserPlus size={18} /> Sign Up</>}
                    </button>
                </form>

                <p className="text-center mt-6 text-sm text-muted-foreground">
                    Already have an account?{' '}
                    <Link to="/" className="text-primary hover:text-primary/80 font-medium transition-colors">
                        Sign in
                    </Link>
                </p>
            </div>
        </div>
    );
}
