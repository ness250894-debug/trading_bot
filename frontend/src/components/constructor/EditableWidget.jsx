/**
 * EditableWidget - Container wrapper that adds edit functionality in Constructor Mode
 * Adds a visible edit icon to the top-right corner of widgets/cards/tables.
 */

import React, { useState, useRef, useEffect } from 'react';
import { useConfig, useConstructorMode } from '../../lib/ConfigContext';
import { Settings2, X, Check, Type, Maximize2, Palette } from 'lucide-react';
import './EditableWidget.css';

/**
 * EditableWidget Component
 * Wraps any widget/card/table to make it editable in Constructor Mode.
 * 
 * @param {string} configPath - Base path for widget config (e.g., "widgets.balanceCard")
 * @param {string} widgetName - Display name for the widget (shown in edit panel)
 * @param {React.ReactNode} children - The widget content
 * @param {string} className - Additional CSS classes
 * @param {object} editableFields - Fields that can be edited, e.g., { title: 'Card Title', height: 200 }
 */
export default function EditableWidget({
    configPath,
    widgetName = 'Widget',
    children,
    className = '',
    editableFields = {},
    style = {},
    ...props
}) {
    const { getValue } = useConfig();
    const { constructorMode, isAdmin, setValue } = useConstructorMode();

    const [showPanel, setShowPanel] = useState(false);
    const [localValues, setLocalValues] = useState({});
    const panelRef = useRef(null);

    // Initialize local values from config
    useEffect(() => {
        if (showPanel) {
            const initialValues = {};
            Object.keys(editableFields).forEach(key => {
                initialValues[key] = getValue(`${configPath}.${key}`, editableFields[key]);
            });
            setLocalValues(initialValues);
        }
    }, [showPanel, configPath, editableFields]);

    // Close panel on outside click
    useEffect(() => {
        if (!showPanel) return;

        const handleClickOutside = (e) => {
            if (panelRef.current && !panelRef.current.contains(e.target)) {
                setShowPanel(false);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, [showPanel]);

    // Update local value
    const handleChange = (key, value) => {
        setLocalValues(prev => ({ ...prev, [key]: value }));
    };

    // Apply changes
    const handleApply = () => {
        Object.entries(localValues).forEach(([key, value]) => {
            setValue(`${configPath}.${key}`, value);
        });
        setShowPanel(false);
    };

    // Cancel changes
    const handleCancel = () => {
        setShowPanel(false);
    };

    // Determine field type
    const getFieldType = (key, value) => {
        if (typeof value === 'number') return 'number';
        if (key.toLowerCase().includes('color')) return 'color';
        if (key.toLowerCase().includes('height') || key.toLowerCase().includes('width')) return 'number';
        return 'text';
    };

    // Get field icon
    const getFieldIcon = (key) => {
        const keyLower = key.toLowerCase();
        if (keyLower.includes('color')) return <Palette size={14} />;
        if (keyLower.includes('height') || keyLower.includes('width') || keyLower.includes('size')) return <Maximize2 size={14} />;
        return <Type size={14} />;
    };

    // Don't show edit icon if not in constructor mode or not admin
    if (!isAdmin || !constructorMode) {
        return (
            <div className={className} style={style} {...props}>
                {children}
            </div>
        );
    }

    return (
        <div
            className={`editable-widget ${className}`}
            style={style}
            {...props}
        >
            {/* Edit Icon Button */}
            <button
                className="editable-widget-icon"
                onClick={(e) => {
                    e.stopPropagation();
                    setShowPanel(!showPanel);
                }}
                title={`Edit ${widgetName}`}
            >
                <Settings2 size={16} />
            </button>

            {/* Edit Panel */}
            {showPanel && (
                <div className="editable-widget-panel" ref={panelRef}>
                    <div className="panel-header">
                        <h4>Edit {widgetName}</h4>
                        <button onClick={handleCancel} className="panel-close">
                            <X size={16} />
                        </button>
                    </div>

                    <div className="panel-content">
                        {Object.entries(editableFields).length === 0 ? (
                            <p className="no-fields">No editable fields defined for this widget.</p>
                        ) : (
                            Object.entries(editableFields).map(([key, defaultValue]) => {
                                const fieldType = getFieldType(key, defaultValue);
                                const currentValue = localValues[key] ?? defaultValue;
                                const displayName = key.replace(/([A-Z])/g, ' $1').replace(/^./, s => s.toUpperCase());

                                return (
                                    <div key={key} className="panel-field">
                                        <label>
                                            <span className="field-icon">{getFieldIcon(key)}</span>
                                            {displayName}
                                        </label>
                                        {fieldType === 'color' ? (
                                            <div className="color-input-wrapper">
                                                <input
                                                    type="color"
                                                    value={currentValue}
                                                    onChange={(e) => handleChange(key, e.target.value)}
                                                />
                                                <span className="color-value">{currentValue}</span>
                                            </div>
                                        ) : fieldType === 'number' ? (
                                            <input
                                                type="number"
                                                value={currentValue}
                                                onChange={(e) => handleChange(key, Number(e.target.value))}
                                                className="panel-input"
                                            />
                                        ) : (
                                            <input
                                                type="text"
                                                value={currentValue}
                                                onChange={(e) => handleChange(key, e.target.value)}
                                                className="panel-input"
                                            />
                                        )}
                                    </div>
                                );
                            })
                        )}
                    </div>

                    <div className="panel-actions">
                        <button onClick={handleCancel} className="btn-cancel">
                            Cancel
                        </button>
                        <button onClick={handleApply} className="btn-apply">
                            <Check size={14} />
                            Apply
                        </button>
                    </div>
                </div>
            )}

            {children}
        </div>
    );
}

/**
 * EditableCard - Convenience wrapper for card/glass components
 */
export function EditableCard({
    configPath,
    title = 'Card',
    children,
    className = '',
    ...props
}) {
    return (
        <EditableWidget
            configPath={configPath}
            widgetName={title}
            className={`editable-card ${className}`}
            editableFields={{
                title: title,
                backgroundColor: '#1a1a2e'
            }}
            {...props}
        >
            {children}
        </EditableWidget>
    );
}

/**
 * EditableTable - Wrapper for data tables with column configuration
 */
export function EditableTable({
    configPath,
    tableName = 'Table',
    columns = [],
    children,
    className = '',
    ...props
}) {
    const { constructorMode, isAdmin, setValue } = useConstructorMode();
    const { getValue } = useConfig();
    const [showColumnEditor, setShowColumnEditor] = useState(false);
    const [visibleColumns, setVisibleColumns] = useState([]);
    const panelRef = useRef(null);

    // Initialize visible columns
    useEffect(() => {
        const savedColumns = getValue(`${configPath}.visibleColumns`, null);
        if (savedColumns) {
            setVisibleColumns(savedColumns);
        } else {
            setVisibleColumns(columns.map(c => c.key));
        }
    }, [configPath, columns]);

    // Close on outside click
    useEffect(() => {
        if (!showColumnEditor) return;
        const handleClickOutside = (e) => {
            if (panelRef.current && !panelRef.current.contains(e.target)) {
                setShowColumnEditor(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, [showColumnEditor]);

    const toggleColumn = (key) => {
        setVisibleColumns(prev => {
            if (prev.includes(key)) {
                return prev.filter(k => k !== key);
            }
            return [...prev, key];
        });
    };

    const handleApply = () => {
        setValue(`${configPath}.visibleColumns`, visibleColumns);
        setShowColumnEditor(false);
    };

    if (!isAdmin || !constructorMode) {
        return <div className={className} {...props}>{children}</div>;
    }

    return (
        <div className={`editable-table ${className}`} {...props}>
            <button
                className="editable-widget-icon"
                onClick={(e) => {
                    e.stopPropagation();
                    setShowColumnEditor(!showColumnEditor);
                }}
                title={`Edit ${tableName} Columns`}
            >
                <Settings2 size={16} />
            </button>

            {showColumnEditor && (
                <div className="editable-widget-panel column-editor" ref={panelRef}>
                    <div className="panel-header">
                        <h4>{tableName} Columns</h4>
                        <button onClick={() => setShowColumnEditor(false)} className="panel-close">
                            <X size={16} />
                        </button>
                    </div>
                    <div className="panel-content">
                        {columns.map(col => (
                            <label key={col.key} className="column-toggle">
                                <input
                                    type="checkbox"
                                    checked={visibleColumns.includes(col.key)}
                                    onChange={() => toggleColumn(col.key)}
                                />
                                <span>{col.label}</span>
                            </label>
                        ))}
                    </div>
                    <div className="panel-actions">
                        <button onClick={() => setShowColumnEditor(false)} className="btn-cancel">
                            Cancel
                        </button>
                        <button onClick={handleApply} className="btn-apply">
                            <Check size={14} />
                            Apply
                        </button>
                    </div>
                </div>
            )}

            {children}
        </div>
    );
}
