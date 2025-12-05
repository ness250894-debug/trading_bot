/**
 * ConstructorToolbar - Floating toolbar for Constructor Mode
 * Shows save/discard buttons and theme controls when constructor mode is active.
 */

import React, { useState } from 'react';
import { useConfig, useConstructorMode } from '../../lib/ConfigContext';
import { EditableColor } from './EditableText';
import {
    Save,
    X,
    Palette,
    ChevronUp,
    ChevronDown,
    Check,
    Eye,
    EyeOff
} from 'lucide-react';
import { toast } from 'react-hot-toast';
import './ConstructorToolbar.css';

export default function ConstructorToolbar() {
    const { getValue } = useConfig();
    const {
        constructorMode,
        isAdmin,
        saveChanges,
        discardChanges,
        hasChanges,
        toggleConstructorMode
    } = useConstructorMode();

    const [expanded, setExpanded] = useState(false);
    const [saving, setSaving] = useState(false);

    // Only show for admins in constructor mode
    if (!isAdmin || !constructorMode) {
        return null;
    }

    const handleSave = async () => {
        setSaving(true);
        try {
            const success = await saveChanges();
            if (success) {
                toast.success('Configuration saved successfully!');
            } else {
                toast.error('Failed to save configuration');
            }
        } catch (err) {
            toast.error('Error saving configuration');
            console.error(err);
        } finally {
            setSaving(false);
        }
    };

    const handleDiscard = () => {
        discardChanges();
        toast('Changes discarded', { icon: '🗑️' });
    };

    const handleExit = () => {
        if (hasChanges) {
            if (confirm('You have unsaved changes. Discard them?')) {
                discardChanges();
                toggleConstructorMode();
            }
        } else {
            toggleConstructorMode();
        }
    };

    return (
        <div className={`constructor-toolbar ${expanded ? 'expanded' : ''}`}>
            <div className="constructor-toolbar-header">
                <div className="constructor-toolbar-title">
                    <Palette size={18} />
                    <span>Constructor Mode</span>
                </div>

                <div className="constructor-toolbar-actions">
                    {hasChanges && (
                        <>
                            <button
                                onClick={handleSave}
                                className="toolbar-btn save"
                                disabled={saving}
                                title="Save changes"
                            >
                                {saving ? (
                                    <span className="saving-spinner" />
                                ) : (
                                    <Save size={16} />
                                )}
                                <span>Save</span>
                            </button>
                            <button
                                onClick={handleDiscard}
                                className="toolbar-btn discard"
                                title="Discard changes"
                            >
                                <X size={16} />
                                <span>Discard</span>
                            </button>
                        </>
                    )}

                    <button
                        onClick={handleExit}
                        className="toolbar-btn exit"
                        title="Exit Constructor Mode"
                    >
                        <EyeOff size={16} />
                        <span>Exit</span>
                    </button>

                    <button
                        onClick={() => setExpanded(!expanded)}
                        className="toolbar-btn toggle"
                        title={expanded ? 'Collapse' : 'Expand'}
                    >
                        {expanded ? <ChevronDown size={16} /> : <ChevronUp size={16} />}
                    </button>
                </div>
            </div>

            {expanded && (
                <div className="constructor-toolbar-content">
                    <div className="toolbar-section">
                        <h4>Theme Colors</h4>
                        <div className="color-pickers">
                            <EditableColor
                                configPath="theme.primaryColor"
                                defaultValue="#8b5cf6"
                                label="Primary"
                            />
                            <EditableColor
                                configPath="theme.accentColor"
                                defaultValue="#10b981"
                                label="Accent"
                            />
                            <EditableColor
                                configPath="theme.dangerColor"
                                defaultValue="#ef4444"
                                label="Danger"
                            />
                            <EditableColor
                                configPath="theme.warningColor"
                                defaultValue="#f59e0b"
                                label="Warning"
                            />
                        </div>
                    </div>

                    <div className="toolbar-section">
                        <h4>Branding</h4>
                        <div className="branding-inputs">
                            <label>
                                <span>App Name</span>
                                <input
                                    type="text"
                                    defaultValue={getValue('branding.appName', 'TradingBot Pro')}
                                    className="toolbar-input"
                                    placeholder="App Name"
                                />
                            </label>
                            <label>
                                <span>Tagline</span>
                                <input
                                    type="text"
                                    defaultValue={getValue('branding.tagline', 'Smart Crypto Trading')}
                                    className="toolbar-input"
                                    placeholder="Tagline"
                                />
                            </label>
                        </div>
                    </div>

                    <div className="toolbar-section help-text">
                        <p>
                            <Check size={14} /> Click on any highlighted text to edit
                        </p>
                        <p>
                            <Check size={14} /> Changes are applied in real-time
                        </p>
                        <p>
                            <Check size={14} /> Click Save to persist changes
                        </p>
                    </div>
                </div>
            )}

            {hasChanges && (
                <div className="unsaved-indicator">
                    <span className="pulse-dot" />
                    Unsaved changes
                </div>
            )}
        </div>
    );
}
