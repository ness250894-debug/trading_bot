import React from 'react';
import { motion } from 'framer-motion';

/**
 * Skeleton Loader Component
 * Provides loading placeholders for various UI elements
 */

// Base shimmer animation
const shimmer = {
    initial: { backgroundPosition: '-200% 0' },
    animate: {
        backgroundPosition: '200% 0',
        transition: {
            duration: 1.5,
            repeat: Infinity,
            ease: 'linear'
        }
    }
};

// Skeleton base styles
const baseClass = "bg-gradient-to-r from-white/5 via-white/10 to-white/5 bg-[length:200%_100%] rounded";

/**
 * Text skeleton - single line
 */
export const SkeletonText = ({ width = "100%", height = "1rem", className = "" }) => (
    <motion.div
        variants={shimmer}
        initial="initial"
        animate="animate"
        className={`${baseClass} ${className}`}
        style={{ width, height }}
    />
);

/**
 * Avatar skeleton - circular
 */
export const SkeletonAvatar = ({ size = 40, className = "" }) => (
    <motion.div
        variants={shimmer}
        initial="initial"
        animate="animate"
        className={`${baseClass} rounded-full ${className}`}
        style={{ width: size, height: size }}
    />
);

/**
 * Card skeleton - full card placeholder
 */
export const SkeletonCard = ({ className = "" }) => (
    <div className={`glass rounded-xl p-6 space-y-4 ${className}`}>
        <div className="flex items-center gap-4">
            <SkeletonAvatar size={48} />
            <div className="flex-1 space-y-2">
                <SkeletonText width="60%" height="1.25rem" />
                <SkeletonText width="40%" height="0.875rem" />
            </div>
        </div>
        <SkeletonText height="3rem" />
        <div className="flex gap-2">
            <SkeletonText width="80px" height="2rem" />
            <SkeletonText width="80px" height="2rem" />
        </div>
    </div>
);

/**
 * Table row skeleton
 */
export const SkeletonTableRow = ({ columns = 5, className = "" }) => (
    <tr className={`border-b border-white/5 ${className}`}>
        {Array.from({ length: columns }).map((_, i) => (
            <td key={i} className="py-4 px-4">
                <SkeletonText width={i === 0 ? "120px" : "80px"} height="1rem" />
            </td>
        ))}
    </tr>
);

/**
 * Table skeleton - full table placeholder
 */
export const SkeletonTable = ({ rows = 5, columns = 5, className = "" }) => (
    <div className={`overflow-hidden rounded-xl ${className}`}>
        <table className="w-full">
            <thead>
                <tr className="border-b border-white/10">
                    {Array.from({ length: columns }).map((_, i) => (
                        <th key={i} className="py-3 px-4 text-left">
                            <SkeletonText width="80px" height="0.875rem" />
                        </th>
                    ))}
                </tr>
            </thead>
            <tbody>
                {Array.from({ length: rows }).map((_, i) => (
                    <SkeletonTableRow key={i} columns={columns} />
                ))}
            </tbody>
        </table>
    </div>
);

/**
 * Chart skeleton - chart placeholder
 */
export const SkeletonChart = ({ height = 300, className = "" }) => (
    <div className={`glass rounded-xl p-4 ${className}`}>
        <div className="flex justify-between items-center mb-4">
            <SkeletonText width="150px" height="1.5rem" />
            <div className="flex gap-2">
                <SkeletonText width="60px" height="2rem" />
                <SkeletonText width="60px" height="2rem" />
            </div>
        </div>
        <motion.div
            variants={shimmer}
            initial="initial"
            animate="animate"
            className={`${baseClass} w-full`}
            style={{ height }}
        />
    </div>
);

/**
 * Stats card skeleton
 */
export const SkeletonStats = ({ className = "" }) => (
    <div className={`glass rounded-xl p-6 ${className}`}>
        <SkeletonText width="100px" height="0.875rem" className="mb-2" />
        <SkeletonText width="150px" height="2rem" className="mb-1" />
        <SkeletonText width="80px" height="0.75rem" />
    </div>
);

/**
 * Widget skeleton - generic widget placeholder
 */
export const SkeletonWidget = ({ className = "" }) => (
    <div className={`glass rounded-xl p-6 ${className}`}>
        <div className="flex justify-between items-center mb-4">
            <SkeletonText width="120px" height="1.25rem" />
            <SkeletonAvatar size={24} />
        </div>
        <div className="space-y-3">
            <SkeletonText height="1rem" />
            <SkeletonText width="80%" height="1rem" />
            <SkeletonText width="60%" height="1rem" />
        </div>
    </div>
);

/**
 * Bot instance skeleton
 */
export const SkeletonBotInstance = ({ className = "" }) => (
    <div className={`glass rounded-xl p-4 flex items-center gap-4 ${className}`}>
        <SkeletonAvatar size={48} />
        <div className="flex-1 space-y-2">
            <SkeletonText width="150px" height="1rem" />
            <SkeletonText width="100px" height="0.75rem" />
        </div>
        <div className="flex gap-2">
            <SkeletonText width="70px" height="2rem" />
            <SkeletonText width="70px" height="2rem" />
        </div>
    </div>
);

/**
 * Grid of skeleton cards
 */
export const SkeletonGrid = ({ count = 4, columns = 2, className = "" }) => (
    <div
        className={`grid gap-4 ${className}`}
        style={{ gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))` }}
    >
        {Array.from({ length: count }).map((_, i) => (
            <SkeletonCard key={i} />
        ))}
    </div>
);

// Default export with all variants
const Skeleton = {
    Text: SkeletonText,
    Avatar: SkeletonAvatar,
    Card: SkeletonCard,
    TableRow: SkeletonTableRow,
    Table: SkeletonTable,
    Chart: SkeletonChart,
    Stats: SkeletonStats,
    Widget: SkeletonWidget,
    BotInstance: SkeletonBotInstance,
    Grid: SkeletonGrid
};

export default Skeleton;
