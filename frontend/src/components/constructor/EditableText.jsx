/**
 * EditableText - Inline editable text component for Constructor Mode
 * Renders normal text for regular users, click-to-edit for admins in constructor mode.
 */

import React, { useState, useRef, useEffect } from 'react';
import { useConfig, useConstructorMode } from '../../lib/ConfigContext';
import { Pencil, Check, X } from 'lucide-react';
import './EditableText.css';

/**
 * EditableText Component
 * @param {string} configPath - Dot notation path to config value (e.g., "pages.landing.heroTitle")
 * @param {string} defaultValue - Fallback value if config path doesn't exist
 * @param {string} as - HTML element type to render (default: 'span')
 * @param {string} className - Additional CSS classes
 * @param {boolean} multiline - Enable textarea for multiline editing
 * @param {object} style - Inline styles
 */
export default function EditableText({
    configPath,
    defaultValue = '',
    as: Component = 'span',
    className = '',
    multiline = false,
    style = {},
    children,
    ...props
}) {
    const { getValue } = useConfig();
    const { constructorMode, isAdmin, setValue } = useConstructorMode();

    const [isEditing, setIsEditing] = useState(false);
    const [editValue, setEditValue] = useState('');
    const inputRef = useRef(null);

    // Get the current value from config
    const currentValue = getValue(configPath, defaultValue) || defaultValue;

    // Focus input when editing starts
    useEffect(() => {
        if (isEditing && inputRef.current) {
            inputRef.current.focus();
            inputRef.current.select();
        }
    }, [isEditing]);

    // Start editing
    const handleStartEdit = (e) => {
        if (!constructorMode || !isAdmin) return;
        e.stopPropagation();
        setEditValue(currentValue);
        setIsEditing(true);
    };

    // Save changes
    const handleSave = (e) => {
        e?.stopPropagation();
        setValue(configPath, editValue);
        setIsEditing(false);
    };

    // Cancel editing
    const handleCancel = (e) => {
        e?.stopPropagation();
        setEditValue(currentValue);
        setIsEditing(false);
    };

    // Handle key events
    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !multiline) {
            handleSave(e);
        } else if (e.key === 'Escape') {
            handleCancel(e);
        }
    };

    // Normal rendering for non-admin or non-constructor mode
    if (!isAdmin || !constructorMode) {
        return (
            <Component className={className} style={style} {...props}>
                {children || currentValue}
            </Component>
        );
    }

    // Editing mode
    if (isEditing) {
        const InputComponent = multiline ? 'textarea' : 'input';

        return (
            <span className="editable-text-container editing">
                <InputComponent
                    ref={inputRef}
                    type="text"
                    value={editValue}
                    onChange={(e) => setEditValue(e.target.value)}
                    onKeyDown={handleKeyDown}
                    className="editable-text-input"
                    style={multiline ? { minHeight: '60px' } : {}}
                />
                <span className="editable-text-actions">
                    <button
                        onClick={handleSave}
                        className="editable-action-btn save"
                        title="Save"
                    >
                        <Check size={14} />
                    </button>
                    <button
                        onClick={handleCancel}
                        className="editable-action-btn cancel"
                        title="Cancel"
                    >
                        <X size={14} />
                    </button>
                </span>
            </span>
        );
    }

    // Constructor mode - editable state
    return (
        <Component
            className={`editable-text ${className}`}
            style={style}
            onClick={handleStartEdit}
            title="Click to edit"
            {...props}
        >
            {children || currentValue}
            <Pencil className="editable-text-icon" size={12} />
        </Component>
    );
}

/**
 * EditableNumber - Numeric input variant
 */
export function EditableNumber({
    configPath,
    defaultValue = 0,
    min,
    max,
    step = 1,
    suffix = '',
    className = '',
    ...props
}) {
    const { getValue } = useConfig();
    const { constructorMode, isAdmin, setValue } = useConstructorMode();

    const [isEditing, setIsEditing] = useState(false);
    const [editValue, setEditValue] = useState(0);
    const inputRef = useRef(null);

    const currentValue = getValue(configPath, defaultValue);

    useEffect(() => {
        if (isEditing && inputRef.current) {
            inputRef.current.focus();
            inputRef.current.select();
        }
    }, [isEditing]);

    const handleStartEdit = (e) => {
        if (!constructorMode || !isAdmin) return;
        e.stopPropagation();
        setEditValue(currentValue);
        setIsEditing(true);
    };

    const handleSave = (e) => {
        e?.stopPropagation();
        setValue(configPath, Number(editValue));
        setIsEditing(false);
    };

    const handleCancel = (e) => {
        e?.stopPropagation();
        setIsEditing(false);
    };

    if (!isAdmin || !constructorMode) {
        return <span className={className} {...props}>{currentValue}{suffix}</span>;
    }

    if (isEditing) {
        return (
            <span className="editable-text-container editing">
                <input
                    ref={inputRef}
                    type="number"
                    value={editValue}
                    onChange={(e) => setEditValue(e.target.value)}
                    onKeyDown={(e) => {
                        if (e.key === 'Enter') handleSave(e);
                        if (e.key === 'Escape') handleCancel(e);
                    }}
                    min={min}
                    max={max}
                    step={step}
                    className="editable-text-input number"
                />
                <span className="editable-text-actions">
                    <button onClick={handleSave} className="editable-action-btn save"><Check size={14} /></button>
                    <button onClick={handleCancel} className="editable-action-btn cancel"><X size={14} /></button>
                </span>
            </span>
        );
    }

    return (
        <span className={`editable-text ${className}`} onClick={handleStartEdit} title="Click to edit">
            {currentValue}{suffix}
            <Pencil className="editable-text-icon" size={12} />
        </span>
    );
}

/**
 * EditableColor - Color picker variant
 */
export function EditableColor({
    configPath,
    defaultValue = '#8b5cf6',
    label = '',
    className = '',
    ...props
}) {
    const { getValue } = useConfig();
    const { constructorMode, isAdmin, setValue } = useConstructorMode();

    const currentValue = getValue(configPath, defaultValue);

    if (!isAdmin || !constructorMode) {
        return null; // Don't show color picker to non-admins
    }

    return (
        <label className={`editable-color ${className}`} {...props}>
            {label && <span className="editable-color-label">{label}</span>}
            <input
                type="color"
                value={currentValue}
                onChange={(e) => setValue(configPath, e.target.value)}
                className="editable-color-input"
            />
            <span className="editable-color-value">{currentValue}</span>
        </label>
    );
}
