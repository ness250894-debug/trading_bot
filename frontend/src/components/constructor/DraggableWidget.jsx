/**
 * DraggableWidget - Advanced container for repositioning, resizing, and editing widgets
 * Only active in Constructor Mode for admins.
 */

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useConfig, useConstructorMode } from '../../lib/ConfigContext';
import { Move, Maximize2, GripVertical, Check, X, RotateCcw } from 'lucide-react';
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
    style = {},
    ...props
}) {
    const { getValue } = useConfig();
    const { constructorMode, isAdmin, setValue } = useConstructorMode();

    // Get saved position/size from config
    const configPath = `layout.${id}`;
    const savedLayout = getValue(configPath, {});

    const [width, setWidth] = useState(savedLayout.width || defaultWidth);
    const [height, setHeight] = useState(savedLayout.height || defaultHeight);
    const [order, setOrder] = useState(savedLayout.order ?? defaultOrder);
    const [isResizing, setIsResizing] = useState(false);
    const [isDragging, setIsDragging] = useState(false);
    const [showControls, setShowControls] = useState(false);

    const containerRef = useRef(null);
    const startPos = useRef({ x: 0, y: 0, width: 0, height: 0 });

    // Update local state when config changes
    useEffect(() => {
        if (savedLayout.width) setWidth(savedLayout.width);
        if (savedLayout.height) setHeight(savedLayout.height);
        if (savedLayout.order !== undefined) setOrder(savedLayout.order);
    }, [savedLayout.width, savedLayout.height, savedLayout.order]);

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
    const handleSave = () => {
        setValue(configPath, {
            width: typeof width === 'number' ? width : width,
            height: typeof height === 'number' ? height : height,
            order
        });
        setShowControls(false);
    };

    // Reset to defaults
    const handleReset = () => {
        setWidth(defaultWidth);
        setHeight(defaultHeight);
        setOrder(defaultOrder);
    };

    // Cancel changes
    const handleCancel = () => {
        setWidth(savedLayout.width || defaultWidth);
        setHeight(savedLayout.height || defaultHeight);
        setOrder(savedLayout.order ?? defaultOrder);
        setShowControls(false);
    };

    // Move order up/down
    const handleOrderChange = (delta) => {
        setOrder(prev => Math.max(0, prev + delta));
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
            onMouseLeave={() => !isResizing && setShowControls(false)}
            {...props}
        >
            {/* Control Bar */}
            {showControls && (
                <div className="draggable-controls">
                    <div className="control-group">
                        <button
                            className="control-btn"
                            onMouseDown={handleResizeStart}
                            title="Drag to resize"
                        >
                            <Maximize2 size={14} />
                        </button>
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
                            onClick={handleReset}
                            title="Reset to default"
                        >
                            <RotateCcw size={14} />
                        </button>
                        <button
                            className="control-btn cancel"
                            onClick={handleCancel}
                            title="Cancel"
                        >
                            <X size={14} />
                        </button>
                        <button
                            className="control-btn save"
                            onClick={handleSave}
                            title="Save layout"
                        >
                            <Check size={14} />
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

            {children}
        </div>
    );
}
