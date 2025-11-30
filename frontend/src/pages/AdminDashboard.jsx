import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import { Shield, Trash2, Edit, Check, X, Search, Users, CreditCard } from 'lucide-react';
import Disclaimer from '../components/Disclaimer';
import { useModal } from '../components/Modal';
import AdminPlans from '../components/AdminPlans';

const AdminDashboard = () => {
    const navigate = useNavigate();
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [editingUser, setEditingUser] = useState(null);
    const [currentUserId, setCurrentUserId] = useState(null);
    const [editingNickname, setEditingNickname] = useState(null);
    const [nicknameValue, setNicknameValue] = useState('');
    const [activeTab, setActiveTab] = useState('users');

    // Fetch users on mount and get current user ID
    useEffect(() => {
        fetchUsers();
        fetchCurrentUser();
    }, []);

    const fetchCurrentUser = async () => {
        try {
            const token = localStorage.getItem('token');
            const response = await fetch('/api/auth/me', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            if (response.ok) {
                const user = await response.json();
                setCurrentUserId(user.id);
            }
        } catch (error) {
            toast.error('Error fetching current user');
        }
    };

    const fetchUsers = async () => {
        try {
            const token = localStorage.getItem('token');

            const response = await fetch('/api/admin/users', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.status === 403) {
                toast.error("Access Denied: Admin privileges required");
                navigate('/dashboard');
                return;
            }

            if (!response.ok) throw new Error('Failed to fetch users');

            const data = await response.json();
            setUsers(data);
        } catch (error) {
            toast.error('Failed to load users');
            toast.error('Failed to load users');
        } finally {
            setLoading(false);
        }
    };

    const handleUpdateSubscription = async (userId, planId, status) => {
        try {
            const token = localStorage.getItem('token');
            const response = await fetch(`/api/admin/users/${userId}/subscription`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ plan_id: planId, status: status })
            });

            if (!response.ok) throw new Error('Failed to update subscription');

            toast.success('Subscription updated');
            setEditingUser(null);
            fetchUsers(); // Refresh list
        } catch (error) {
            toast.error('Update failed');
            toast.error('Update failed');
        }
    };

    const { confirm } = useModal();

    const handleDeleteUser = (userId) => {
        confirm({
            title: 'Delete User',
            message: 'Are you sure you want to delete this user? This action cannot be undone and will remove all user data including strategies and trade history.',
            confirmText: 'Delete User',
            type: 'danger',
            onConfirm: async () => {
                try {
                    const token = localStorage.getItem('token');
                    const response = await fetch(`/api/admin/users/${userId}`, {
                        method: 'DELETE',
                        headers: {
                            'Authorization': `Bearer ${token}`
                        }
                    });

                    if (!response.ok) throw new Error('Failed to delete user');

                    toast.success('User deleted');
                    fetchUsers();
                } catch (error) {
                    toast.error('Delete failed');
                    toast.error('Delete failed');
                }
            }
        });
    };

    const handleMakeAdmin = (userId) => {
        confirm({
            title: 'Grant Admin Privileges',
            message: 'Are you sure you want to make this user an administrator? They will have full access to manage users and system settings.',
            confirmText: 'Make Admin',
            type: 'warning',
            onConfirm: async () => {
                try {
                    const token = localStorage.getItem('token');
                    const response = await fetch(`/api/admin/users/${userId}/make_admin`, {
                        method: 'POST',
                        headers: {
                            'Authorization': `Bearer ${token}`
                        }
                    });

                    if (!response.ok) throw new Error('Failed to update admin status');

                    toast.success('User is now an admin');
                    fetchUsers();
                } catch (error) {
                    toast.error('Operation failed');
                    toast.error('Operation failed');
                }
            }
        });
    };

    const handleUpdateNickname = async (userId, nickname) => {
        try {
            const token = localStorage.getItem('token');
            const response = await fetch('/api/auth/update-profile', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ nickname })
            });

            if (!response.ok) throw new Error('Failed to update nickname');

            toast.success('Nickname updated');
            setEditingNickname(null);
            fetchUsers();
        } catch (error) {
            toast.error('Update failed');
            toast.error('Update failed');
        }
    };

    const filteredUsers = users.filter(user =>
        user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
        user.id.toString().includes(searchTerm) ||
        (user.nickname && user.nickname.toLowerCase().includes(searchTerm.toLowerCase()))
    );

    if (loading) {
        return (
            <div className="min-h-screen bg-background flex items-center justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
            </div>
        );
    }
    return (
        <div className="min-h-screen bg-background p-8">
            <div className="max-w-7xl mx-auto">
                <div className="flex justify-between items-center mb-8">
                    <div>
                        <h1 className="text-3xl font-bold text-foreground flex items-center gap-3">
                            <Shield className="w-8 h-8 text-primary" />
                            Admin Dashboard
                        </h1>
                        <p className="text-muted-foreground mt-2">Manage users and subscriptions</p>
                    </div>

                    {activeTab === 'users' && (
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
                            <input
                                type="text"
                                placeholder="Search users..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                className="pl-10 pr-4 py-2 bg-card border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary w-64 text-foreground"
                            />
                        </div>
                    )}
                </div>

                <div className="flex gap-4 mb-6 border-b border-border">
                    <button
                        onClick={() => setActiveTab('users')}
                        className={`pb-3 px-4 text-sm font-medium transition-colors border-b-2 ${activeTab === 'users'
                            ? 'border-primary text-primary'
                            : 'border-transparent text-muted-foreground hover:text-foreground'
                            }`}
                    >
                        <div className="flex items-center gap-2">
                            <Users size={18} />
                            Users
                        </div>
                    </button>
                    <button
                        onClick={() => setActiveTab('plans')}
                        className={`pb-3 px-4 text-sm font-medium transition-colors border-b-2 ${activeTab === 'plans'
                            ? 'border-primary text-primary'
                            : 'border-transparent text-muted-foreground hover:text-foreground'
                            }`}
                    >
                        <div className="flex items-center gap-2">
                            <CreditCard size={18} />
                            Plans
                        </div>
                    </button>
                </div>

                <Disclaimer compact />

                {activeTab === 'users' ? (
                    <div className="bg-card rounded-xl border border-border overflow-hidden shadow-sm">
                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead>
                                    <tr className="bg-muted/50 border-b border-border">
                                        <th className="px-6 py-4 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">User</th>
                                        <th className="px-6 py-4 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Nickname</th>
                                        <th className="px-6 py-4 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Joined</th>
                                        <th className="px-6 py-4 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Role</th>
                                        <th className="px-6 py-4 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Plan</th>
                                        <th className="px-6 py-4 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Status</th>
                                        <th className="px-6 py-4 text-right text-xs font-medium text-muted-foreground uppercase tracking-wider">Actions</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-border">
                                    {filteredUsers.length === 0 ? (
                                        <tr>
                                            <td colSpan="7" className="px-6 py-12 text-center">
                                                <div className="flex flex-col items-center gap-3">
                                                    <Shield className="w-12 h-12 text-muted-foreground opacity-50" />
                                                    <p className="text-muted-foreground">
                                                        {users.length === 0 ? 'No users found. Register an account to get started.' : 'No users match your search.'}
                                                    </p>
                                                </div>
                                            </td>
                                        </tr>
                                    ) : (
                                        filteredUsers.map((user) => (
                                            <tr key={user.id} className="hover:bg-muted/30 transition-colors">
                                                <td className="px-6 py-4 whitespace-nowrap">
                                                    <div className="flex items-center">
                                                        <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center text-primary font-bold">
                                                            {(user.nickname || user.email)[0].toUpperCase()}
                                                        </div>
                                                        <div className="ml-4">
                                                            <div className="text-sm font-medium text-foreground">{user.email}</div>
                                                            <div className="text-xs text-muted-foreground">ID: {user.id}</div>
                                                        </div>
                                                    </div>
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap">
                                                    {user.id === currentUserId && editingNickname === user.id ? (
                                                        <div className="flex items-center gap-2">
                                                            <input
                                                                type="text"
                                                                value={nicknameValue}
                                                                onChange={(e) => setNicknameValue(e.target.value)}
                                                                className="bg-background border border-border rounded px-2 py-1 text-sm w-32"
                                                                placeholder="Nickname"
                                                            />
                                                            <button
                                                                onClick={() => handleUpdateNickname(user.id, nicknameValue)}
                                                                className="p-1 text-green-500 hover:bg-green-500/10 rounded"
                                                            >
                                                                <Check className="w-4 h-4" />
                                                            </button>
                                                            <button
                                                                onClick={() => setEditingNickname(null)}
                                                                className="p-1 text-red-500 hover:bg-red-500/10 rounded"
                                                            >
                                                                <X className="w-4 h-4" />
                                                            </button>
                                                        </div>
                                                    ) : (
                                                        <div className="flex items-center gap-2">
                                                            <span className="text-sm text-foreground">
                                                                {user.nickname || <span className="text-muted-foreground italic">Not set</span>}
                                                            </span>
                                                            {user.id === currentUserId && (
                                                                <button
                                                                    onClick={() => {
                                                                        setEditingNickname(user.id);
                                                                        setNicknameValue(user.nickname || '');
                                                                    }}
                                                                    className="p-1 text-blue-500 hover:bg-blue-500/10 rounded"
                                                                    title="Edit Nickname"
                                                                >
                                                                    <Edit className="w-3 h-3" />
                                                                </button>
                                                            )}
                                                        </div>
                                                    )}
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-muted-foreground">
                                                    {new Date(user.created_at).toLocaleDateString()}
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap">
                                                    {user.is_admin ? (
                                                        <span className="px-2 py-1 text-xs font-medium bg-purple-500/10 text-purple-500 rounded-full border border-purple-500/20">
                                                            Admin
                                                        </span>
                                                    ) : (
                                                        <span className="px-2 py-1 text-xs font-medium bg-blue-500/10 text-blue-500 rounded-full border border-blue-500/20">
                                                            User
                                                        </span>
                                                    )}
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap">
                                                    {editingUser === user.id ? (
                                                        <select
                                                            className="bg-background border border-border rounded px-2 py-1 text-sm"
                                                            defaultValue={user.plan_id || 'free'}
                                                            id={`plan-${user.id}`}
                                                        >
                                                            <option value="free">Free</option>
                                                            <option value="pro_monthly">Pro Monthly</option>
                                                            <option value="pro_yearly">Pro Yearly</option>
                                                        </select>
                                                    ) : (
                                                        <span className={`px-2 py-1 text-xs font-medium rounded-full border ${(user.plan_id || 'free').includes('pro')
                                                            ? 'bg-green-500/10 text-green-500 border-green-500/20'
                                                            : 'bg-gray-500/10 text-gray-500 border-gray-500/20'
                                                            }`}>
                                                            {(user.plan_id || 'Free').replace('_', ' ').toUpperCase()}
                                                        </span>
                                                    )}
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap">
                                                    {editingUser === user.id ? (
                                                        <select
                                                            className="bg-background border border-border rounded px-2 py-1 text-sm"
                                                            defaultValue={user.status || 'active'}
                                                            id={`status-${user.id}`}
                                                        >
                                                            <option value="active">Active</option>
                                                            <option value="expired">Expired</option>
                                                            <option value="cancelled">Cancelled</option>
                                                        </select>
                                                    ) : (
                                                        <span className={`px-2 py-1 text-xs font-medium rounded-full border ${user.status === 'active'
                                                            ? 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20'
                                                            : 'bg-red-500/10 text-red-500 border-red-500/20'
                                                            }`}>
                                                            {(user.status || 'Active').toUpperCase()}
                                                        </span>
                                                    )}
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                                    <div className="flex items-center justify-end gap-2">
                                                        {editingUser === user.id ? (
                                                            <>
                                                                <button
                                                                    onClick={() => {
                                                                        const plan = document.getElementById(`plan-${user.id}`).value;
                                                                        const status = document.getElementById(`status-${user.id}`).value;
                                                                        handleUpdateSubscription(user.id, plan, status);
                                                                    }}
                                                                    className="p-1 text-green-500 hover:bg-green-500/10 rounded"
                                                                >
                                                                    <Check className="w-4 h-4" />
                                                                </button>
                                                                <button
                                                                    onClick={() => setEditingUser(null)}
                                                                    className="p-1 text-red-500 hover:bg-red-500/10 rounded"
                                                                >
                                                                    <X className="w-4 h-4" />
                                                                </button>
                                                            </>
                                                        ) : (
                                                            <>
                                                                {!user.is_admin && (
                                                                    <button
                                                                        onClick={() => handleMakeAdmin(user.id)}
                                                                        className="p-1 text-purple-500 hover:bg-purple-500/10 rounded"
                                                                        title="Grant Admin"
                                                                    >
                                                                        <Shield className="w-4 h-4" />
                                                                    </button>
                                                                )}
                                                                <button
                                                                    onClick={() => setEditingUser(user.id)}
                                                                    className="p-1 text-blue-500 hover:bg-blue-500/10 rounded"
                                                                    title="Edit Subscription"
                                                                >
                                                                    <Edit className="w-4 h-4" />
                                                                </button>
                                                                <button
                                                                    onClick={() => handleDeleteUser(user.id)}
                                                                    className="p-1 text-red-500 hover:bg-red-500/10 rounded"
                                                                    title="Delete User"
                                                                >
                                                                    <Trash2 className="w-4 h-4" />
                                                                </button>
                                                            </>
                                                        )}
                                                    </div>
                                                </td>
                                            </tr>
                                        ))
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                ) : (
                    <AdminPlans />
                )}
            </div >
        </div >
    );
};

export default AdminDashboard;
