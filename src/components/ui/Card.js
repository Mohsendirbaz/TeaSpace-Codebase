import React from 'react';

/**
 * Card Component
 * A container component with styling for a card-like appearance
 */
export const Card = ({ children, className = '', ...props }) => {
    return (
        <div className={`card ${className}`} {...props}>
            {children}
        </div>
    );
};

/**
 * CardHeader Component
 * The header section of a card
 */
export const CardHeader = ({ children, className = '', ...props }) => {
    return (
        <div className={`card-header ${className}`} {...props}>
            {children}
        </div>
    );
};

/**
 * CardContent Component
 * The main content section of a card
 */
export const CardContent = ({ children, className = '', ...props }) => {
    return (
        <div className={`card-content ${className}`} {...props}>
            {children}
        </div>
    );
};