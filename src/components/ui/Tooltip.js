/**
 * @file Tooltip.js
 * @description A reusable tooltip component for displaying additional information on hover
 * @module components/ui
 * @requires react, framer-motion
 */
import React, { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import '../../styles/HomePage.CSS/HCSS.css';

/**
 * Tooltip Component
 * Displays additional information when hovering over children elements
 * 
 * @param {Object} props - Component props
 * @param {React.ReactNode} props.content - Content to display in the tooltip
 * @param {React.ReactNode} props.children - Elements that trigger the tooltip on hover
 * @returns {React.ReactElement} Tooltip component
 */
const Tooltip = ({ content, children }) => {
    const [isVisible, setIsVisible] = useState(false);
    const tooltipRef = useRef(null);

    return (
        <div
            className="tooltip-container"
            onMouseEnter={() => setIsVisible(true)}
            onMouseLeave={() => setIsVisible(false)}
        >
            {children}
            <AnimatePresence>
                {isVisible && (
                    <motion.div
                        ref={tooltipRef}
                        className="tooltip"
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: 10 }}
                        transition={{ duration: 0.2 }}
                    >
                        {content}
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

export default Tooltip;