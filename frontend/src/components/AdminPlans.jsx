import React, { useState, useEffect } from 'react';
import { toast } from 'react-hot-toast';
import { Plus, Edit, Trash2, Check, DollarSign, Calendar } from 'lucide-react';
import api from '../lib/api';
import { useModal } from './Modal';

const AdminPlans = () => {
    const [plans, setPlans] = useState([]);
    const [loading, setLoading] = useState(true);
    const [editingPlan, setEditingPlan] = useState(null);
    const [isCreating, setIsCreating] = useState(false);
    const { confirm } = useModal();

    // Form state
    const [formData, setFormData] = useState({
        id: '',
        name: '',
        price: '',
        currency: 'USD',
        duration_days: 30,
        features: '',
        is_active: true
    });

    useEffect(() => {
        fetchPlans();
    }, []);

    const fetchPlans = async () => {
        try {
            const response = await api.get('/admin/plans');
            setPlans(response.data);
        } catch (error) {
            console.error('Error fetching plans:', error);
            toast.error('Failed to load plans');
        } finally {
            setLoading(false);
        }
    };

    const handleEdit = (plan) => {
        setEditingPlan(plan.id);
        setFormData({
            ...plan,
            features: plan.features.join('\n') // Convert array to newline-separated string
        });
        setIsCreating(false);
    };

    const handleCreate = () => {
        setEditingPlan(null);
        setFormData({
            id: '',
            name: '',
            price: '',
            currency: 'USD',
            duration_days: 30,
            features: '',
            is_active: true
        });
        setIsCreating(true);
    };

    const handleCancel = () => {
        setEditingPlan(null);
        setIsCreating(false);
    };

    const handleSave = async () => {
        try {
            const payload = {
                ...formData,
                price: parseFloat(formData.price),
                duration_days: parseInt(formData.duration_days),
                features: formData.features.split('\n').filter(f => f.trim())
            };

            if (isCreating) {
                await api.post('/admin/plans', payload);
                toast.success('Plan created');
            } else {
                await api.put(`/admin/plans/${editingPlan}`, payload);
                toast.success('Plan updated');
            }

            fetchPlans();
            handleCancel();
        } catch (error) {
            console.error('Error saving plan:', error);
            toast.error(error.response?.data?.detail || 'Failed to save plan');
        }
    };

    const handleDelete = (planId) => {
        confirm({
            title: 'Deactivate Plan',
            message: 'Are you sure you want to deactivate this plan? Users currently on this plan will not be affected until their subscription expires.',
            confirmText: 'Deactivate',
            type: 'danger',
            onConfirm: async () => {
                try {
                    await api.delete(`/admin/plans/${planId}`);
                    toast.success('Plan deactivated');
                    fetchPlans();
                } catch (error) {
                    console.error('Error deleting plan:', error);
                    toast.error('Failed to deactivate plan');
                }
            }
        });
    };

    if (loading) return <div className="p-4">Loading plans...</div>;

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h2 className="text-xl font-semibold text-foreground">Subscription Plans</h2>
                <button
                    onClick={handleCreate}
                    className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
                >
                    <Plus size={18} />
                    Create Plan
                </button>
            </div>

            {isCreating && (
                <div className="bg-card border border-border rounded-xl p-6 shadow-sm mb-6">
                    <h3 className="text-lg font-medium mb-4">New Plan</h3>
                    <PlanForm
                        formData={formData}
                        setFormData={setFormData}
                        onSave={handleSave}
                        onCancel={handleCancel}
                        isCreating={true}
                    />
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {plans.map(plan => (
                    <div key={plan.id} className={`bg-card border border-border rounded-xl p-6 shadow-sm relative ${!plan.is_active ? 'opacity-60' : ''}`}>
                        {editingPlan === plan.id ? (
                            <PlanForm
                                formData={formData}
                                setFormData={setFormData}
                                onSave={handleSave}
                                onCancel={handleCancel}
                            />
                        ) : (
                            <>
                                <div className="absolute top-4 right-4 flex gap-2">
                                    <button
                                        onClick={() => handleEdit(plan)}
                                        className="p-2 text-muted-foreground hover:text-primary hover:bg-primary/10 rounded-lg transition-colors"
                                    >
                                        <Edit size={18} />
                                    </button>
                                    <button
                                        onClick={() => handleDelete(plan.id)}
                                        className="p-2 text-muted-foreground hover:text-red-500 hover:bg-red-500/10 rounded-lg transition-colors"
                                    >
                                        <Trash2 size={18} />
                                    </button>
                                </div>

                                <div className="mb-4">
                                    <h3 className="text-lg font-bold text-foreground">{plan.name}</h3>
                                    <div className="text-sm text-muted-foreground font-mono mt-1">{plan.id}</div>
                                </div>

                                <div className="flex items-baseline gap-1 mb-4">
                                    <span className="text-2xl font-bold text-primary">${plan.price}</span>
                                    <span className="text-muted-foreground">/ {plan.duration_days} days</span>
                                </div>

                                <div className="space-y-2 mb-4">
                                    {plan.features.map((feature, idx) => (
                                        <div key={idx} className="flex items-center gap-2 text-sm text-muted-foreground">
                                            <Check size={14} className="text-green-500" />
                                            {feature}
                                        </div>
                                    ))}
                                </div>

                                {!plan.is_active && (
                                    <div className="absolute top-4 left-4 bg-red-500/10 text-red-500 text-xs px-2 py-1 rounded-full font-medium">
                                        Inactive
                                    </div>
                                )}
                            </>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
};

const PlanForm = ({ formData, setFormData, onSave, onCancel, isCreating = false }) => {
    return (
        <div className="space-y-4">
            {isCreating && (
                <div>
                    <label className="block text-sm font-medium text-muted-foreground mb-1">Plan ID (Unique)</label>
                    <input
                        type="text"
                        value={formData.id}
                        onChange={e => setFormData({ ...formData, id: e.target.value })}
                        className="w-full bg-background border border-border rounded px-3 py-2 text-foreground"
                        placeholder="e.g. pro_monthly"
                    />
                </div>
            )}

            <div>
                <label className="block text-sm font-medium text-muted-foreground mb-1">Name</label>
                <input
                    type="text"
                    value={formData.name}
                    onChange={e => setFormData({ ...formData, name: e.target.value })}
                    className="w-full bg-background border border-border rounded px-3 py-2 text-foreground"
                    placeholder="e.g. Pro Monthly"
                />
            </div>

            <div className="grid grid-cols-2 gap-4">
                <div>
                    <label className="block text-sm font-medium text-muted-foreground mb-1">Price</label>
                    <div className="relative">
                        <DollarSign size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
                        <input
                            type="number"
                            value={formData.price}
                            onChange={e => setFormData({ ...formData, price: e.target.value })}
                            className="w-full bg-background border border-border rounded pl-9 pr-3 py-2 text-foreground"
                            placeholder="29.99"
                        />
                    </div>
                </div>
                <div>
                    <label className="block text-sm font-medium text-muted-foreground mb-1">Duration (Days)</label>
                    <div className="relative">
                        <Calendar size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
                        <input
                            type="number"
                            value={formData.duration_days}
                            onChange={e => setFormData({ ...formData, duration_days: e.target.value })}
                            className="w-full bg-background border border-border rounded pl-9 pr-3 py-2 text-foreground"
                            placeholder="30"
                        />
                    </div>
                </div>
            </div>

            <div>
                <label className="block text-sm font-medium text-muted-foreground mb-1">Features (One per line)</label>
                <textarea
                    value={formData.features}
                    onChange={e => setFormData({ ...formData, features: e.target.value })}
                    className="w-full bg-background border border-border rounded px-3 py-2 text-foreground min-h-[100px]"
                    placeholder="Feature 1&#10;Feature 2&#10;Feature 3"
                />
            </div>

            <div className="flex justify-end gap-2 pt-2">
                <button
                    onClick={onCancel}
                    className="px-3 py-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
                >
                    Cancel
                </button>
                <button
                    onClick={onSave}
                    className="px-3 py-1.5 text-sm bg-primary text-primary-foreground rounded hover:bg-primary/90 transition-colors"
                >
                    Save Plan
                </button>
            </div>
        </div>
    );
};

export default AdminPlans;
