import React, { useState, useEffect } from 'react';
import {
    DndContext,
    closestCenter,
    KeyboardSensor,
    PointerSensor,
    useSensor,
    useSensors,
    DragOverlay,
} from '@dnd-kit/core';
import {
    arrayMove,
    SortableContext,
    sortableKeyboardCoordinates,
    useSortable,
    rectSortingStrategy,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { motion } from 'framer-motion';
import { GripVertical, Lock } from 'lucide-react';

const STORAGE_KEY = 'dashboard_widget_order';

/**
 * Sortable Widget Wrapper
 * Makes any widget draggable within a DraggableWidgetGrid
 */
export const SortableWidget = ({
    id,
    children,
    disabled = false,
    className = ""
}) => {
    const {
        attributes,
        listeners,
        setNodeRef,
        transform,
        transition,
        isDragging,
    } = useSortable({ id, disabled });

    const style = {
        transform: CSS.Transform.toString(transform),
        transition,
        opacity: isDragging ? 0.5 : 1,
        zIndex: isDragging ? 100 : 1,
    };

    return (
        <div
            ref={setNodeRef}
            style={style}
            className={`relative group ${className}`}
        >
            {/* Drag Handle */}
            {!disabled && (
                <div
                    {...attributes}
                    {...listeners}
                    className="absolute top-2 right-2 z-10 p-2 rounded-lg 
                    opacity-0 group-hover:opacity-100 transition-opacity
                    cursor-grab active:cursor-grabbing
                    bg-black/40 hover:bg-black/60 backdrop-blur-sm"
                    title="Drag to reorder"
                >
                    <GripVertical size={16} className="text-white/70" />
                </div>
            )}

            {/* Locked indicator */}
            {disabled && (
                <div
                    className="absolute top-2 right-2 z-10 p-2 rounded-lg 
                    opacity-0 group-hover:opacity-100 transition-opacity
                    bg-black/40 backdrop-blur-sm"
                    title="This widget cannot be moved"
                >
                    <Lock size={14} className="text-white/50" />
                </div>
            )}

            {/* Widget content */}
            {children}
        </div>
    );
};

/**
 * Draggable Widget Grid
 * Container that enables drag-and-drop reordering of child widgets
 */
const DraggableWidgetGrid = ({
    widgets,
    onReorder,
    columns = 2,
    gap = 4,
    persistKey = STORAGE_KEY,
    className = ""
}) => {
    const [items, setItems] = useState(widgets.map(w => w.id));
    const [activeId, setActiveId] = useState(null);

    // Load saved order from localStorage
    useEffect(() => {
        const saved = localStorage.getItem(persistKey);
        if (saved) {
            try {
                const savedOrder = JSON.parse(saved);
                // Only use saved order if it contains the same items
                const currentIds = new Set(widgets.map(w => w.id));
                const savedIds = new Set(savedOrder);
                if (savedOrder.length === widgets.length &&
                    savedOrder.every(id => currentIds.has(id))) {
                    setItems(savedOrder);
                }
            } catch (e) {
                console.error('Failed to parse saved widget order:', e);
            }
        }
    }, [widgets, persistKey]);

    const sensors = useSensors(
        useSensor(PointerSensor, {
            activationConstraint: {
                distance: 8,
            },
        }),
        useSensor(KeyboardSensor, {
            coordinateGetter: sortableKeyboardCoordinates,
        })
    );

    const handleDragStart = (event) => {
        setActiveId(event.active.id);
    };

    const handleDragEnd = (event) => {
        const { active, over } = event;
        setActiveId(null);

        if (over && active.id !== over.id) {
            setItems((items) => {
                const oldIndex = items.indexOf(active.id);
                const newIndex = items.indexOf(over.id);
                const newOrder = arrayMove(items, oldIndex, newIndex);

                // Persist to localStorage
                localStorage.setItem(persistKey, JSON.stringify(newOrder));

                // Notify parent
                if (onReorder) {
                    onReorder(newOrder);
                }

                return newOrder;
            });
        }
    };

    // Sort widgets by current order
    const sortedWidgets = items
        .map(id => widgets.find(w => w.id === id))
        .filter(Boolean);

    const activeWidget = activeId ? widgets.find(w => w.id === activeId) : null;

    return (
        <DndContext
            sensors={sensors}
            collisionDetection={closestCenter}
            onDragStart={handleDragStart}
            onDragEnd={handleDragEnd}
        >
            <SortableContext items={items} strategy={rectSortingStrategy}>
                <div
                    className={`grid gap-${gap} ${className}`}
                    style={{
                        gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))`
                    }}
                >
                    {sortedWidgets.map((widget) => (
                        <SortableWidget
                            key={widget.id}
                            id={widget.id}
                            disabled={widget.locked}
                            className={widget.className}
                        >
                            {widget.component}
                        </SortableWidget>
                    ))}
                </div>
            </SortableContext>

            {/* Drag Overlay - shows floating widget while dragging */}
            <DragOverlay>
                {activeWidget ? (
                    <motion.div
                        initial={{ scale: 1.02 }}
                        animate={{ scale: 1.05 }}
                        className="shadow-2xl rounded-xl opacity-90"
                    >
                        {activeWidget.component}
                    </motion.div>
                ) : null}
            </DragOverlay>
        </DndContext>
    );
};

/**
 * Hook to manage widget order
 */
export const useWidgetOrder = (defaultWidgets, storageKey = STORAGE_KEY) => {
    const [order, setOrder] = useState(() => {
        const saved = localStorage.getItem(storageKey);
        if (saved) {
            try {
                return JSON.parse(saved);
            } catch {
                return defaultWidgets.map(w => w.id);
            }
        }
        return defaultWidgets.map(w => w.id);
    });

    const reorder = (newOrder) => {
        setOrder(newOrder);
        localStorage.setItem(storageKey, JSON.stringify(newOrder));
    };

    const reset = () => {
        const defaultOrder = defaultWidgets.map(w => w.id);
        setOrder(defaultOrder);
        localStorage.removeItem(storageKey);
    };

    const sortedWidgets = order
        .map(id => defaultWidgets.find(w => w.id === id))
        .filter(Boolean);

    return {
        order,
        reorder,
        reset,
        sortedWidgets
    };
};

/**
 * Reset Button for widget order
 */
export const ResetLayoutButton = ({ onClick, className = "" }) => (
    <button
        onClick={onClick}
        className={`text-xs text-muted-foreground hover:text-foreground 
               px-3 py-1.5 rounded-lg hover:bg-white/5 transition-colors ${className}`}
    >
        Reset Layout
    </button>
);

export default DraggableWidgetGrid;
