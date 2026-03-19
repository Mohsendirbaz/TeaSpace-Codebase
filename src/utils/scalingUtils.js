import * as math from 'mathjs';

/**
 * Calculate a scaled value based on a base value, operation, and scaling factor
 * 
 * @param {number} baseValue - The base value to scale
 * @param {string} operation - The operation to apply (multiply, power, divide, log, exponential, add, subtract)
 * @param {number} factor - The scaling factor to apply
 * @returns {number} - The scaled value
 * @throws {Error} - If the operation is invalid or results in an invalid value
 */
export const calculateScaledValue = (baseValue, operation, factor) => {
    try {
        if (baseValue === 0 && operation === 'divide') {
            throw new Error('Division by zero');
        }
        if (baseValue < 0 && operation === 'log') {
            throw new Error('Logarithm of negative number');
        }

        let result;
        switch (operation) {
            case 'multiply':
                result = math.multiply(baseValue, factor);
                break;
            case 'power':
                result = math.pow(baseValue, factor);
                break;
            case 'divide':
                result = math.divide(baseValue, factor);
                break;
            case 'log':
                result = math.multiply(math.log(baseValue), factor);
                break;
            case 'exponential':
                result = math.exp(math.multiply(math.log(baseValue), factor));
                break;
            case 'add':
                result = math.add(baseValue, factor);
                break;
            case 'subtract':
                result = math.subtract(baseValue, factor);
                break;
            default:
                result = baseValue;
        }

        if (!isFinite(result)) {
            throw new Error('Result is not a finite number');
        }

        return result;
    } catch (error) {
        throw error;
    }
};

/**
 * Propagate changes through a sequence of scaling groups
 * 
 * @param {Array} groups - The array of scaling groups
 * @param {number} startIndex - The index of the group to start propagation from
 * @returns {Array} - The updated array of scaling groups
 */
export const propagateChanges = (groups, startIndex) => {
    const updatedGroups = [...groups];

    // Skip processing if we're at the last group or beyond
    if (startIndex >= updatedGroups.length - 1) {
        return updatedGroups;
    }

    // For each subsequent group, update base values from the previous group's results
    for (let i = startIndex + 1; i < updatedGroups.length; i++) {
        const previousGroup = updatedGroups[i - 1];
        const currentGroup = {...updatedGroups[i]};

        // Create a map of previous results
        const previousResults = previousGroup.items.reduce((acc, item) => {
            acc[item.id] = {
                scaledValue: item.enabled ? item.scaledValue : item.baseValue,
                enabled: item.enabled
            };
            return acc;
        }, {});

        // Update each item in the current group
        currentGroup.items = currentGroup.items.map(item => {
            const prevResult = previousResults[item.id];
            if (!prevResult) return item;

            // Calculate new scaled value based on updated base value
            const newBaseValue = prevResult.scaledValue;
            const newScaledValue = calculateScaledValue(
                newBaseValue,
                item.operation,
                item.scalingFactor
            );

            return {
                ...item,
                originalBaseValue: item.originalBaseValue || item.baseValue, // Preserve original
                baseValue: newBaseValue,
                scaledValue: item.enabled ? newScaledValue : newBaseValue
            };
        });

        updatedGroups[i] = currentGroup;
    }

    return updatedGroups;
};

/**
 * Determine the correct insertion index for a new scaling group
 * 
 * @param {number} groupNumber - The number of the new group
 * @param {Array} groups - The existing array of scaling groups
 * @returns {number} - The index where the new group should be inserted
 */
export const determineInsertionIndex = (groupNumber, groups) => {
    // Look for the position where this group should be inserted based on numbering
    for (let i = 0; i < groups.length; i++) {
        const match = groups[i].name.match(/Scaling Group (\d+)/);
        if (match) {
            const currentNumber = parseInt(match[1], 10);
            if (currentNumber > groupNumber) {
                return i; // Insert before this group
            }
        }
    }
    return groups.length; // Append at the end if no suitable position found
};

/**
 * Process imported configuration for cumulative calculations
 * 
 * @param {Array} groups - The imported groups configuration
 * @param {string} filterKeyword - The current scaling type filter
 * @returns {Array} - The processed and validated groups
 */
export const processImportedConfiguration = (groups, filterKeyword = '') => {
    if (!Array.isArray(groups) || groups.length === 0) {
        throw new Error("Invalid or empty groups array");
    }

    // First, validate all groups and ensure they have the required structure
    const validatedGroups = groups.map((group, index) => {
        // Ensure group has all required properties
        const processedGroup = {
            id: group.id || `group-${Date.now()}-${index}`,
            name: group.name || `Scaling Group ${index + 1}`,
            isProtected: !!group.isProtected,
            _scalingType: group._scalingType || filterKeyword || "mixed", // Ensure scaling type is preserved
            items: Array.isArray(group.items) ? [...group.items] : []
        };

        // Process all items in the group to ensure they have required properties
        processedGroup.items = processedGroup.items.map(item => {
            const processedItem = {
                id: item.id || `item-${Date.now()}-${Math.random()}`,
                label: item.label || item.id || 'Unknown Item',
                originalBaseValue: item.originalBaseValue || item.baseValue || 0,
                baseValue: item.baseValue || 0,
                scalingFactor: item.scalingFactor !== undefined ? item.scalingFactor : 1,
                operation: item.operation || 'multiply',
                enabled: item.enabled !== undefined ? !!item.enabled : true,
                notes: item.notes || '',
                vKey: item.vKey || null,
                rKey: item.rKey || null,
                scaledValue: item.scaledValue !== undefined ? item.scaledValue :
                    calculateScaledValue(
                        item.baseValue || 0,
                        item.operation || 'multiply',
                        item.scalingFactor !== undefined ? item.scalingFactor : 1
                    )
            };

            return processedItem;
        });

        return processedGroup;
    });

    // Now process cumulative relationships to ensure mathematical integrity
    if (validatedGroups.length > 1) {
        // For the first group, ensure base values are original values
        validatedGroups[0].items = validatedGroups[0].items.map(item => ({
            ...item,
            baseValue: item.originalBaseValue || item.baseValue,
            scaledValue: calculateScaledValue(
                item.originalBaseValue || item.baseValue,
                item.operation,
                item.scalingFactor
            )
        }));

        // Then process all subsequent groups
        for (let i = 1; i < validatedGroups.length; i++) {
            // Get results from the previous group to use as base values
            const previousGroup = validatedGroups[i - 1];
            const previousResults = previousGroup.items.reduce((acc, item) => {
                acc[item.id] = {
                    scaledValue: item.enabled ? item.scaledValue : item.baseValue,
                    enabled: item.enabled
                };
                return acc;
            }, {});

            // Update base values and recalculate scaled values
            validatedGroups[i].items = validatedGroups[i].items.map(item => {
                const prevResult = previousResults[item.id];

                // If no previous result exists, keep original values
                if (!prevResult) return item;

                // Update base value to previous group's result
                const newBaseValue = prevResult.scaledValue;

                // Calculate new scaled value
                const newScaledValue = item.enabled
                    ? calculateScaledValue(newBaseValue, item.operation, item.scalingFactor)
                    : newBaseValue;

                return {
                    ...item,
                    baseValue: newBaseValue,
                    scaledValue: newScaledValue
                };
            });
        }
    }

    return validatedGroups;
};