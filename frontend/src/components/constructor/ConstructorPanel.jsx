/**
 * ConstructorPanel - Admin panel for UI Constructor Mode
 * Provides toggle and configuration interface for Constructor Mode.
 */

import React from 'react';
import { useConstructorMode, useConfig } from '../../lib/ConfigContext';
import { EditableColor } from './EditableText';
import {
    Palette,
    Eye,
    EyeOff,
    Type,
    Layout,
    Table,
    Settings,
    Sparkles,
    Save,
    RefreshCw
} from 'lucide-react';
import { toast } from 'react-hot-toast';
import api from '../../lib/api';
import './ConstructorPanel.css';

export default function ConstructorPanel() {
    const { getValue, reload } = useConfig();
    const {
        constructorMode,
        toggleConstructorMode,
        isAdmin
    } = useConstructorMode();

    const handleReset = async () => {
        if (!confirm('Reset all UI customizations to defaults? This cannot be undone.')) {
            return;
        }

        try {
            await api.post('/constructor/reset');
            await reload();
            toast.success('Configuration reset to defaults');
        } catch (err) {
            toast.error('Failed to reset configuration');
            console.error(err);
        }
    };

    if (!isAdmin) {
        return (
            <div className="constructor-panel">
                <div className="panel-message">
                    <p>Admin privileges required to access Constructor Mode.</p>
                </div>
            </div>
        );
    }

    return (
        <div className="constructor-panel">
            {/* Hero Section */}
            <div className="panel-hero">
                <div className="hero-icon">
                    <Palette size={48} />
                </div>
                <h2>UI Constructor</h2>
                <p>Customize your application's look and feel in real-time</p>
            </div>

            {/* Toggle Button */}
            <div className="toggle-section">
                <button
                    onClick={toggleConstructorMode}
                    className={`constructor-toggle ${constructorMode ? 'active' : ''}`}
                >
                    {constructorMode ? (
                        <>
                            <EyeOff size={20} />
                            <span>Exit Constructor Mode</span>
                        </>
                    ) : (
                        <>
                            <Eye size={20} />
                            <span>Enter Constructor Mode</span>
                        </>
                    )}
                </button>

                {constructorMode && (
                    <p className="toggle-hint">
                        <Sparkles size={14} />
                        Click on any highlighted text to edit it
                    </p>
                )}
            </div>

            {/* Features */}
            <div className="features-grid">
                <div className="feature-card">
                    <div className="feature-icon">
                        <Type size={24} />
                    </div>
                    <h3>Text & Labels</h3>
                    <p>Edit page titles, button text, widget labels, and all text content</p>
                </div>

                <div className="feature-card">
                    <div className="feature-icon">
                        <Palette size={24} />
                    </div>
                    <h3>Theme Colors</h3>
                    <p>Customize primary, accent, and semantic colors across the app</p>
                </div>

                <div className="feature-card">
                    <div className="feature-icon">
                        <Layout size={24} />
                    </div>
                    <h3>Widget Dimensions</h3>
                    <p>Adjust widget heights, card sizes, and layout proportions</p>
                </div>

                <div className="feature-card">
                    <div className="feature-icon">
                        <Table size={24} />
                    </div>
                    <h3>Table Columns</h3>
                    <p>Configure visible columns and headers in data tables</p>
                </div>
            </div>

            {/* Quick Theme Settings */}
            <div className="quick-settings">
                <h3>
                    <Settings size={18} />
                    Quick Theme Settings
                </h3>

                <div className="color-grid">
                    <div className="color-setting">
                        <label>Primary Color</label>
                        <div className="color-preview" style={{ background: getValue('theme.primaryColor', '#8b5cf6') }}>
                            <EditableColor
                                configPath="theme.primaryColor"
                                defaultValue="#8b5cf6"
                            />
                        </div>
                        <span className="color-code">{getValue('theme.primaryColor', '#8b5cf6')}</span>
                    </div>

                    <div className="color-setting">
                        <label>Accent Color</label>
                        <div className="color-preview" style={{ background: getValue('theme.accentColor', '#10b981') }}>
                            <EditableColor
                                configPath="theme.accentColor"
                                defaultValue="#10b981"
                            />
                        </div>
                        <span className="color-code">{getValue('theme.accentColor', '#10b981')}</span>
                    </div>

                    <div className="color-setting">
                        <label>Danger Color</label>
                        <div className="color-preview" style={{ background: getValue('theme.dangerColor', '#ef4444') }}>
                            <EditableColor
                                configPath="theme.dangerColor"
                                defaultValue="#ef4444"
                            />
                        </div>
                        <span className="color-code">{getValue('theme.dangerColor', '#ef4444')}</span>
                    </div>

                    <div className="color-setting">
                        <label>Warning Color</label>
                        <div className="color-preview" style={{ background: getValue('theme.warningColor', '#f59e0b') }}>
                            <EditableColor
                                configPath="theme.warningColor"
                                defaultValue="#f59e0b"
                            />
                        </div>
                        <span className="color-code">{getValue('theme.warningColor', '#f59e0b')}</span>
                    </div>
                </div>
            </div>

            {/* Branding Info */}
            <div className="branding-info">
                <h3>Current Branding</h3>
                <div className="info-grid">
                    <div className="info-item">
                        <span className="info-label">App Name</span>
                        <span className="info-value">{getValue('branding.appName', 'TradingBot Pro')}</span>
                    </div>
                    <div className="info-item">
                        <span className="info-label">Tagline</span>
                        <span className="info-value">{getValue('branding.tagline', 'Smart Crypto Trading')}</span>
                    </div>
                </div>
            </div>

            {/* Actions */}
            <div className="panel-actions">
                <button onClick={handleReset} className="reset-btn">
                    <RefreshCw size={16} />
                    Reset to Defaults
                </button>
            </div>

            {/* Help */}
            <div className="panel-help">
                <h4>How to use</h4>
                <ol>
                    <li>Click "Enter Constructor Mode" above</li>
                    <li>Navigate to any page you want to customize</li>
                    <li>Click on highlighted text elements to edit them</li>
                    <li>Use the floating toolbar to save or discard changes</li>
                </ol>
            </div>
        </div>
    );
}
