import React, { useRef } from 'react';
import { useDrag, useDrop } from 'react-dnd';
import { motion } from 'framer-motion';
import '../../styles/HomePage.CSS/Consolidated.css';

/**
 * @file DraggableScalingItem.js
 * @description A draggable item component for scaling UI
 * @module components/scaling/DraggableScalingItem
 * @requires react
 * @requires react-dnd
 * @requires framer-motion
 */

/**
 * DraggableScalingItem Component
 * A draggable component that can be reordered in a list
 * 
 * @param {Object} item - The item data
 * @param {number} index - The current index of the item in the list
 * @param {Function} moveItem - Function to move the item to a new position
 * @param {Object} V - Object containing V values
 * @param {Object} R - Object containing R values
 * @param {Function} toggleV - Function to toggle V values
 * @param {Function} toggleR - Function to toggle R values
 */
const DraggableScalingItem = ({ item, index, moveItem, V, R, toggleV, toggleR, ...props }) => {
    const ref = useRef(null);

    const [{ handlerId }, drop] = useDrop({
        accept: 'scaling-item',
        collect(monitor) {
            return {
                handlerId: monitor.getHandlerId(),
            };
        },
        hover(item, monitor) {
            if (!ref.current) return;
            const dragIndex = item.index;
            const hoverIndex = index;
            if (dragIndex === hoverIndex) return;

            const hoverBoundingRect = ref.current?.getBoundingClientRect();
            const hoverMiddleY = (hoverBoundingRect.bottom - hoverBoundingRect.top) / 2;
            const clientOffset = monitor.getClientOffset();
            const hoverClientY = clientOffset.y - hoverBoundingRect.top;

            if (dragIndex < hoverIndex && hoverClientY < hoverMiddleY) return;
            if (dragIndex > hoverIndex && hoverClientY > hoverMiddleY) return;

            moveItem(dragIndex, hoverIndex);
            item.index = hoverIndex;
        },
    });

    const [{ isDragging }, drag] = useDrag({
        type: 'scaling-item',
        item: () => ({ id: item.id, index }),
        collect: (monitor) => ({
            isDragging: monitor.isDragging(),
        }),
    });

    drag(drop(ref));

    // Render V and R checkboxes if applicable
    const renderVRCheckboxes = () => {
        return (
            <div className="checkbox-section">
                {item.vKey && (
                    <div className="checkbox-group">
                        <span className="checkbox-label">{item.vKey}</span>
                        <input
                            type="checkbox"
                            className="custom-checkbox"
                            checked={V && V[item.vKey] === 'on'}
                            onChange={() => toggleV && toggleV(item.vKey)}
                        />
                    </div>
                )}
                {item.rKey && (
                    <div className="checkbox-group">
                        <span className="checkbox-label">{item.rKey}</span>
                        <input
                            type="checkbox"
                            className="custom-checkbox"
                            checked={R && R[item.rKey] === 'on'}
                            onChange={() => toggleR && toggleR(item.rKey)}
                        />
                    </div>
                )}
            </div>
        );
    };

    return (
        <motion.div
            ref={ref}
            layout
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.2 }}
            style={{ opacity: isDragging ? 0.5 : 1 }}
            data-handler-id={handlerId}
            {...props}
        >
            {(item.vKey || item.rKey) && renderVRCheckboxes()}
            {props.children}
        </motion.div>
    );
};

export default DraggableScalingItem;