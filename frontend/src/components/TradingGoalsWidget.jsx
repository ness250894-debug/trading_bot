import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom';
import { Target, Plus, Edit2, Trash2, Check, X, Calendar } from 'lucide-react';
import api from '../lib/api';

export default function TradingGoalsWidget() {
    const [goals, setGoals] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showAddModal, setShowAddModal] = useState(false);
    const [editingGoal, setEditingGoal] = useState(null);
    const [formData, setFormData] = useState({
        title: '',
        description: '',
        target_amount: '',
        target_date: ''
    });

    useEffect(() => {
        fetchGoals();
    }, []);

    const fetchGoals = async () => {
        try {
            const response = await api.get('/trading-goals');
            setGoals(response.data.goals || []);
        } catch (error) {
            console.error('Failed to fetch trading goals:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        try {
            const goalData = {
                title: formData.title,
                description: formData.description || null,
                target_amount: parseFloat(formData.target_amount),
                target_date: formData.target_date || null
            };

            if (editingGoal) {
                await api.put(`/trading-goals/${editingGoal.id}`, goalData);
            } else {
                await api.post('/trading-goals', goalData);
            }

            await fetchGoals();
            handleCloseModal();
        } catch (error) {
            console.error('Failed to save trading goal:', error);
            alert('Failed to save goal. Please try again.');
        }
    };

    const handleDelete = async (goalId) => {
        if (!window.confirm('Are you sure you want to delete this goal?')) return;

        try {
            await api.delete(`/trading-goals/${goalId}`);
            await fetchGoals();
        } catch (error) {
            console.error('Failed to delete trading goal:', error);
            alert('Failed to delete goal. Please try again.');
        }
    };

    const handleComplete = async (goalId) => {
        try {
            await api.post(`/trading-goals/${goalId}/complete`);
            await fetchGoals();
        } catch (error) {
            console.error('Failed to complete trading goal:', error);
            alert('Failed to complete goal. Please try again.');
        }
    };

    const handleEdit = (goal) => {
        setEditingGoal(goal);
        setFormData({
            title: goal.title,
            description: goal.description || '',
            target_amount: goal.target_amount,
            target_date: goal.target_date ? goal.target_date.split('T')[0] : ''
        });
        setShowAddModal(true);
    };

    const handleCloseModal = () => {
        setShowAddModal(false);
        setEditingGoal(null);
        setFormData({ title: '', description: '', target_amount: '', target_date: '' });
    };

    const calculateProgress = (goal) => {
        return Math.min((goal.current_progress / goal.target_amount) * 100, 100);
    };

    if (loading) {
        return (
            <div className="glass rounded-2xl p-6">
                <div className="animate-pulse space-y-4">
                    <div className="h-6 bg-white/10 rounded w-1/4"></div>
                    <div className="h-20 bg-white/10 rounded"></div>
                </div>
            </div>
        );
    }

    return (
        <div className="glass rounded-2xl p-6 border-l-4 border-l-primary/50">
            <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-semibold flex items-center gap-2">
                    <Target size={20} className="text-primary" />
                    Trading Goals
                </h3>
                <button
                    onClick={() => setShowAddModal(true)}
                    className="flex items-center gap-2 px-4 py-2 bg-primary/10 hover:bg-primary/20 text-primary rounded-lg transition-colors"
                >
                    <Plus size={16} />
                    Add Goal
                </button>
            </div>

            {goals.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground">
                    <Target size={48} className="mx-auto mb-4 opacity-30" />
                    <p>No trading goals yet. Create one to start tracking your progress!</p>
                </div>
            ) : (
                <div className="space-y-4">
                    {goals.map((goal) => {
                        const progress = calculateProgress(goal);
                        const isOverdue = goal.target_date && new Date(goal.target_date) < new Date();

                        return (
                            <div
                                key={goal.id}
                                className={`p-4 rounded-xl border transition-all ${goal.is_completed
                                    ? 'bg-green-500/5 border-green-500/20'
                                    : 'bg-white/5 border-white/10 hover:border-primary/30'
                                    }`}
                            >
                                <div className="flex items-start justify-between mb-3">
                                    <div className="flex-1">
                                        <h4 className={`font-semibold ${goal.is_completed ? 'text-green-400 line-through' : ''}`}>
                                            {goal.title}
                                        </h4>
                                        {goal.description && (
                                            <p className="text-sm text-muted-foreground mt-1">{goal.description}</p>
                                        )}
                                    </div>
                                    {!goal.is_completed && (
                                        <div className="flex items-center gap-2">
                                            <button
                                                onClick={() => handleEdit(goal)}
                                                className="p-1.5 hover:bg-white/10 rounded transition-colors"
                                                title="Edit goal"
                                            >
                                                <Edit2 size={14} />
                                            </button>
                                            <button
                                                onClick={() => handleComplete(goal.id)}
                                                className="p-1.5 hover:bg-green-500/20 text-green-400 rounded transition-colors"
                                                title="Mark as completed"
                                            >
                                                <Check size={14} />
                                            </button>
                                            <button
                                                onClick={() => handleDelete(goal.id)}
                                                className="p-1.5 hover:bg-red-500/20 text-red-400 rounded transition-colors"
                                                title="Delete goal"
                                            >
                                                <Trash2 size={14} />
                                            </button>
                                        </div>
                                    )}
                                </div>

                                <div className="space-y-2">
                                    <div className="flex justify-between text-sm">
                                        <span className="text-muted-foreground">Progress</span>
                                        <span className="font-medium">
                                            ${goal.current_progress.toFixed(2)} / ${goal.target_amount.toFixed(2)}
                                        </span>
                                    </div>
                                    <div className="w-full bg-white/10 rounded-full h-2 overflow-hidden">
                                        <div
                                            className={`h-full rounded-full transition-all ${goal.is_completed ? 'bg-green-500' : 'bg-primary'
                                                }`}
                                            style={{ width: `${progress}%` }}
                                        />
                                    </div>
                                    <div className="flex justify-between items-center text-xs">
                                        <span className={goal.is_completed ? 'text-green-400' : 'text-primary'}>
                                            {progress.toFixed(1)}% Complete
                                        </span>
                                        {goal.target_date && (
                                            <span className={`flex items-center gap-1 ${isOverdue && !goal.is_completed ? 'text-red-400' : 'text-muted-foreground'}`}>
                                                <Calendar size={12} />
                                                {new Date(goal.target_date).toLocaleDateString()}
                                            </span>
                                        )}
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}

            {/* Add/Edit Modal */}
            {showAddModal && ReactDOM.createPortal(
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[9999]" onClick={handleCloseModal}>
                    <div className="glass rounded-2xl p-6 max-w-md w-full mx-4" onClick={(e) => e.stopPropagation()}>
                        <div className="flex items-center justify-between mb-6">
                            <h3 className="text-xl font-semibold">
                                {editingGoal ? 'Edit Goal' : 'Add New Goal'}
                            </h3>
                            <button onClick={handleCloseModal} className="p-2 hover:bg-white/10 rounded transition-colors">
                                <X size={20} />
                            </button>
                        </div>

                        <form onSubmit={handleSubmit} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium mb-2">Goal Title *</label>
                                <input
                                    type="text"
                                    value={formData.title}
                                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                                    className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:border-primary transition-colors"
                                    placeholder="e.g., Reach $10,000 profit"
                                    required
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium mb-2">Description</label>
                                <textarea
                                    value={formData.description}
                                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                                    className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:border-primary transition-colors resize-none"
                                    rows="3"
                                    placeholder="Optional notes about this goal"
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium mb-2">Target Amount (USDT) *</label>
                                <input
                                    type="number"
                                    step="0.01"
                                    value={formData.target_amount}
                                    onChange={(e) => setFormData({ ...formData, target_amount: e.target.value })}
                                    className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:border-primary transition-colors"
                                    placeholder="1000.00"
                                    required
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium mb-2">Target Date</label>
                                <input
                                    type="date"
                                    value={formData.target_date}
                                    onChange={(e) => setFormData({ ...formData, target_date: e.target.value })}
                                    className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:border-primary transition-colors"
                                />
                            </div>

                            <div className="flex gap-3 pt-4">
                                <button
                                    type="button"
                                    onClick={handleCloseModal}
                                    className="flex-1 px-4 py-2 bg-white/5 hover:bg-white/10 rounded-lg transition-colors"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    className="flex-1 px-4 py-2 bg-primary hover:bg-primary/90 text-primary-foreground rounded-lg transition-colors"
                                >
                                    {editingGoal ? 'Update Goal' : 'Create Goal'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>,
                document.body
            )}
        </div>
    );
}
