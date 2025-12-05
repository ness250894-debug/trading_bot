/**
 * DraggableWidget - Unified container wrapper for Constructor Mode
 * Combines: resize, reorder, and field editing capabilities.
 * Only active in Constructor Mode for admins.
 */

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useConfig, useConstructorMode } from '../../lib/ConfigContext';
import {
    Settings2, Check, X, RotateCcw, GripVertical,
    Type, Maximize2, Palette
} from 'lucide-react';
import './DraggableWidget.css';

export default function DraggableWidget({
    id,
    children,
    className = '',
    defaultWidth = 'auto',
    defaultHeight = 'auto',
    defaultOrder = 0,
    minWidth = 200,
    minHeight = 100,
    editableFields = {},
    widgetName = 'Widget',
    style = {},
    ...props
}) {
    const { getValue } = useConfig();
    const { constructorMode, isAdmin, setValue } = useConstructorMode();

    // Get saved layout from config
    const configPath = `layout.${id}`;
    const savedLayout = getValue(configPath, {});

    // Layout state
    const [width, setWidth] = useState(savedLayout.width || defaultWidth);
    const [height, setHeight] = useState(savedLayout.height || defaultHeight);
    const [order, setOrder] = useState(savedLayout.order ?? defaultOrder);
    const [isResizing, setIsResizing] = useState(false);
    const [showControls, setShowControls] = useState(false);

    // Field editing state
    const [showFieldPanel, setShowFieldPanel] = useState(false);
    const [localFieldValues, setLocalFieldValues] = useState({});

    const containerRef = useRef(null);
    const fieldsPanelRef = useRef(null);
    const startPos = useRef({ x: 0, y: 0, width: 0, height: 0 });

    // Update local state when config changes
    useEffect(() => {
        if (savedLayout.width) setWidth(savedLayout.width);
        if (savedLayout.height) setHeight(savedLayout.height);
        if (savedLayout.order !== undefined) setOrder(savedLayout.order);
    }, [savedLayout.width, savedLayout.height, savedLayout.order]);

    // Initialize field values when panel opens
    useEffect(() => {
        if (showFieldPanel && Object.keys(editableFields).length > 0) {
            const initialValues = {};
            Object.keys(editableFields).forEach(key => {
                initialValues[key] = getValue(`layout.${id}.fields.${key}`, editableFields[key]);
            });
            setLocalFieldValues(initialValues);
        }
    }, [showFieldPanel, id, editableFields, getValue]);

    // Close field panel on outside click
    useEffect(() => {
        if (!showFieldPanel) return;
        const handleClickOutside = (e) => {
            if (fieldsPanelRef.current && !fieldsPanelRef.current.contains(e.target)) {
                setShowFieldPanel(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, [showFieldPanel]);

    // Handle resize
    const handleResizeStart = useCallback((e) => {
        e.preventDefault();
        e.stopPropagation();
        setIsResizing(true);

        const rect = containerRef.current.getBoundingClientRect();
        startPos.current = {
            x: e.clientX,
            y: e.clientY,
            width: rect.width,
            height: rect.height
        };

        const handleMouseMove = (moveEvent) => {
            const deltaX = moveEvent.clientX - startPos.current.x;
            const deltaY = moveEvent.clientY - startPos.current.y;

            const newWidth = Math.max(minWidth, startPos.current.width + deltaX);
            const newHeight = Math.max(minHeight, startPos.current.height + deltaY);

            setWidth(newWidth);
            setHeight(newHeight);
        };

        const handleMouseUp = () => {
            setIsResizing(false);
            document.removeEventListener('mousemove', handleMouseMove);
            document.removeEventListener('mouseup', handleMouseUp);
        };

        document.addEventListener('mousemove', handleMouseMove);
        document.addEventListener('mouseup', handleMouseUp);
    }, [minWidth, minHeight]);

    // Save layout changes
    const handleSaveLayout = () => {
        setValue(configPath, {
            ...savedLayout,
            width: typeof width === 'number' ? width : width,
            height: typeof height === 'number' ? height : height,
            order
        });
        setShowControls(false);
    };

    // Reset layout to defaults
    const handleResetLayout = () => {
        setWidth(defaultWidth);
        setHeight(defaultHeight);
        setOrder(defaultOrder);
    };

    // Cancel layout changes
    const handleCancelLayout = () => {
        setWidth(savedLayout.width || defaultWidth);
        setHeight(savedLayout.height || defaultHeight);
        setOrder(savedLayout.order ?? defaultOrder);
        setShowControls(false);
    };

    // Move order up/down
    const handleOrderChange = (delta) => {
        setOrder(prev => Math.max(0, prev + delta));
    };

    // Field editing handlers
    const handleFieldChange = (key, value) => {
        setLocalFieldValues(prev => ({ ...prev, [key]: value }));
    };

    const handleApplyFields = () => {
        const fieldsToSave = {};
        Object.entries(localFieldValues).forEach(([key, value]) => {
            fieldsToSave[key] = value;
        });
        setValue(`layout.${id}.fields`, fieldsToSave);
        setShowFieldPanel(false);
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

    // Format display name
    const formatDisplayName = (key) => {
        return key.replace(/([A-Z])/g, ' $1').replace(/^./, s => s.toUpperCase());
    };

    // Normal mode - render children as-is
    if (!isAdmin || !constructorMode) {
        return (
            <div className={className} style={style} {...props}>
                {children}
            </div>
        );
    }

    // Constructor mode - render with controls
    const hasEditableFields = Object.keys(editableFields).length > 0;

    const containerStyle = {
        ...style,
        width: typeof width === 'number' ? `${width}px` : width,
        height: typeof height === 'number' ? `${height}px` : height,
        order: order,
    };

    return (
        <div
            ref={containerRef}
            className={`draggable-widget ${className} ${showControls ? 'controls-visible' : ''} ${isResizing ? 'resizing' : ''}`}
            style={containerStyle}
            onMouseEnter={() => setShowControls(true)}
            onMouseLeave={() => !isResizing && !showFieldPanel && setShowControls(false)}
            {...props}
        >
            {/* Control Bar */}
            {showControls && (
                <div className="draggable-controls">
                    <div className="control-group">
                        {/* Edit Fields Button (if editable fields defined) */}
                        {hasEditableFields && (
                            <button
                                className="control-btn"
                                onClick={() => setShowFieldPanel(!showFieldPanel)}
                                title="Edit widget properties"
                            >
                                <Settings2 size={14} />
                            </button>
                        )}

                        {/* Order Controls */}
                        <div className="order-controls">
                            <button
                                className="control-btn small"
                                onClick={() => handleOrderChange(-1)}
                                title="Move up"
                            >
                                ↑
                            </button>
                            <span className="order-value">{order}</span>
                            <button
                                className="control-btn small"
                                onClick={() => handleOrderChange(1)}
                                title="Move down"
                            >
                                ↓
                            </button>
                        </div>
                    </div>

                    <div className="control-group">
                        <button
                            className="control-btn reset"
                            onClick={handleResetLayout}
                            title="Reset to default"
                        >
                            <RotateCcw size={14} />
                        </button>
                        <button
                            className="control-btn cancel"
                            onClick={handleCancelLayout}
                            title="Cancel"
                        >
                            <X size={14} />
                        </button>
                        <button
                            className="control-btn save"
                            onClick={handleSaveLayout}
                            title="Save layout"
                        >
                            <Check size={14} />
                        </button>
                    </div>
                </div>
            )}

            {/* Field Editor Panel */}
            {showFieldPanel && hasEditableFields && (
                <div className="draggable-field-panel" ref={fieldsPanelRef}>
                    <div className="field-panel-header">
                        <h4>Edit {widgetName}</h4>
                        <button onClick={() => setShowFieldPanel(false)} className="panel-close">
                            <X size={16} />
                        </button>
                    </div>
                    <div className="field-panel-content">
                        {Object.entries(editableFields).map(([key, defaultValue]) => {
                            const fieldType = getFieldType(key, defaultValue);
                            const currentValue = localFieldValues[key] ?? defaultValue;

                            return (
                                <div key={key} className="field-row">
                                    <label>
                                        <span className="field-icon">{getFieldIcon(key)}</span>
                                        {formatDisplayName(key)}
                                    </label>
                                    {fieldType === 'color' ? (
                                        <div className="color-input-wrapper">
                                            <input
                                                type="color"
                                                value={currentValue}
                                                onChange={(e) => handleFieldChange(key, e.target.value)}
                                            />
                                            <span className="color-value">{currentValue}</span>
                                        </div>
                                    ) : (
                                        <input
                                            type={fieldType}
                                            value={currentValue}
                                            onChange={(e) => handleFieldChange(key, fieldType === 'number' ? Number(e.target.value) : e.target.value)}
                                            className="field-input"
                                        />
                                    )}
                                </div>
                            );
                        })}
                    </div>
                    <div className="field-panel-actions">
                        <button onClick={() => setShowFieldPanel(false)} className="btn-cancel">
                            Cancel
                        </button>
                        <button onClick={handleApplyFields} className="btn-apply">
                            <Check size={14} /> Apply
                        </button>
                    </div>
                </div>
            )}

            {/* Size indicator while resizing */}
            {isResizing && (
                <div className="size-indicator">
                    {Math.round(typeof width === 'number' ? width : containerRef.current?.offsetWidth || 0)} × {Math.round(typeof height === 'number' ? height : containerRef.current?.offsetHeight || 0)}
                </div>
            )}

            {/* Resize handle */}
            {showControls && (
                <div
                    className="resize-handle"
                    onMouseDown={handleResizeStart}
                >
                    <GripVertical size={12} />
                </div>
            )}

            {/* Widget content - wrapped for centering */}
            <div className="widget-content">
                {children}
            </div>
        </div>
    );
}
