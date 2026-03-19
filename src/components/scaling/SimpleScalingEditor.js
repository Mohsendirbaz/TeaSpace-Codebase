import React, { useEffect, useMemo } from 'react';

const OPERATIONS = [
    { id: 'multiply', label: 'Multiply' },
    { id: 'add', label: 'Add' },
    { id: 'subtract', label: 'Subtract' },
    { id: 'divide', label: 'Divide' },
    { id: 'power', label: 'Power' }
];

const toNumber = (value, fallback = 0) => {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : fallback;
};

const calculateScaledValue = (baseValue, operation, factor) => {
    switch (operation) {
        case 'add':
            return baseValue + factor;
        case 'subtract':
            return baseValue - factor;
        case 'divide':
            return factor === 0 ? baseValue : baseValue / factor;
        case 'power':
            return Math.pow(baseValue, factor);
        case 'multiply':
        default:
            return baseValue * factor;
    }
};

const normalizeBaseCosts = (baseCosts = []) => baseCosts.map((cost, index) => ({
    id: cost.id || `item-${index + 1}`,
    label: cost.label || cost.id || `Item ${index + 1}`,
    value: toNumber(cost.value ?? cost.baseValue),
    baseValue: toNumber(cost.baseValue ?? cost.value),
    vKey: cost.vKey || null,
    rKey: cost.rKey || null
}));

const buildDefaultGroup = (baseCosts, filterKeyword, index = 0) => ({
    id: `${filterKeyword || 'scaling'}-group-${index + 1}`,
    name: `Scaling Group ${index + 1}`,
    _scalingType: filterKeyword || '',
    items: baseCosts.map((cost) => ({
        ...cost,
        originalBaseValue: cost.baseValue,
        baseValue: cost.baseValue,
        scalingFactor: 1,
        operation: 'multiply',
        enabled: true,
        notes: '',
        scaledValue: cost.baseValue
    }))
});

const reconcileGroups = (groups, baseCosts, filterKeyword) => {
    const sourceGroups = groups && groups.length > 0
        ? groups
        : [buildDefaultGroup(baseCosts, filterKeyword)];

    let previousResults = Object.fromEntries(
        baseCosts.map((cost) => [cost.id, cost.baseValue])
    );

    return sourceGroups.map((group, groupIndex) => {
        const groupItems = baseCosts.map((cost) => {
            const existingItem = group.items?.find((item) => item.id === cost.id) || {};
            const baseValue = toNumber(previousResults[cost.id], cost.baseValue);
            const scalingFactor = toNumber(existingItem.scalingFactor, 1);
            const operation = existingItem.operation || 'multiply';
            const enabled = existingItem.enabled !== false;
            const scaledValue = enabled
                ? calculateScaledValue(baseValue, operation, scalingFactor)
                : baseValue;

            return {
                id: cost.id,
                label: cost.label,
                vKey: existingItem.vKey || cost.vKey || null,
                rKey: existingItem.rKey || cost.rKey || null,
                originalBaseValue: cost.baseValue,
                baseValue,
                scalingFactor,
                operation,
                enabled,
                notes: existingItem.notes || '',
                scaledValue
            };
        });

        previousResults = Object.fromEntries(
            groupItems.map((item) => [item.id, item.enabled ? item.scaledValue : item.baseValue])
        );

        return {
            id: group.id || `${filterKeyword || 'scaling'}-group-${groupIndex + 1}`,
            name: group.name || `Scaling Group ${groupIndex + 1}`,
            _scalingType: filterKeyword || group._scalingType || '',
            items: groupItems
        };
    });
};

const SimpleScalingEditor = ({
    title,
    baseCosts = [],
    initialScalingGroups = [],
    onScalingGroupsChange,
    onScaledValuesChange,
    filterKeyword = '',
    V = {},
    R = {},
    toggleV,
    toggleR,
    activeGroupIndex = 0,
    onActiveGroupChange,
    onFinalResultsGenerated
}) => {
    const normalizedBaseCosts = useMemo(() => normalizeBaseCosts(baseCosts), [baseCosts]);
    const resolvedGroups = useMemo(
        () => reconcileGroups(initialScalingGroups, normalizedBaseCosts, filterKeyword),
        [initialScalingGroups, normalizedBaseCosts, filterKeyword]
    );

    const boundedGroupIndex = Math.min(
        Math.max(activeGroupIndex, 0),
        Math.max(resolvedGroups.length - 1, 0)
    );
    const activeGroup = resolvedGroups[boundedGroupIndex] || resolvedGroups[0];
    const finalGroup = resolvedGroups[resolvedGroups.length - 1];

    useEffect(() => {
        if (!finalGroup) {
            return;
        }

        const summaryItems = finalGroup.items.map((item) => ({
            id: item.id,
            label: item.label,
            finalResult: item.scaledValue
        }));

        onScaledValuesChange?.(finalGroup.items, filterKeyword);
        onFinalResultsGenerated?.(summaryItems, filterKeyword);
    }, [finalGroup, filterKeyword, onFinalResultsGenerated, onScaledValuesChange]);

    useEffect(() => {
        if (boundedGroupIndex !== activeGroupIndex) {
            onActiveGroupChange?.(boundedGroupIndex, filterKeyword);
        }
    }, [activeGroupIndex, boundedGroupIndex, filterKeyword, onActiveGroupChange]);

    const commitGroups = (nextGroups) => {
        const reconciledGroups = reconcileGroups(nextGroups, normalizedBaseCosts, filterKeyword);
        onScalingGroupsChange?.(reconciledGroups);
    };

    const updateActiveGroup = (updater) => {
        const nextGroups = resolvedGroups.map((group, groupIndex) => {
            if (groupIndex !== boundedGroupIndex) {
                return group;
            }

            return updater(group);
        });

        commitGroups(nextGroups);
    };

    const handleItemFieldChange = (itemId, field, value) => {
        updateActiveGroup((group) => ({
            ...group,
            items: group.items.map((item) => item.id === itemId
                ? { ...item, [field]: value }
                : item)
        }));
    };

    const handleAddGroup = () => {
        const nextIndex = resolvedGroups.length;
        const nextGroups = [
            ...resolvedGroups,
            buildDefaultGroup(normalizedBaseCosts, filterKeyword, nextIndex)
        ];

        commitGroups(nextGroups);
        onActiveGroupChange?.(nextIndex, filterKeyword);
    };

    const handleRemoveGroup = () => {
        if (resolvedGroups.length <= 1) {
            return;
        }

        const nextGroups = resolvedGroups.filter((_, groupIndex) => groupIndex !== boundedGroupIndex);
        const nextIndex = Math.max(0, boundedGroupIndex - 1);

        commitGroups(nextGroups);
        onActiveGroupChange?.(nextIndex, filterKeyword);
    };

    return (
        <div className="simple-scaling-editor" style={{ marginTop: '1rem' }}>
            {title && <h3>{title}</h3>}

            <div
                className="simple-scaling-toolbar"
                style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', marginBottom: '0.75rem', flexWrap: 'wrap' }}
            >
                {resolvedGroups.map((group, groupIndex) => (
                    <button
                        key={group.id}
                        type="button"
                        className={`sub-tab-button ${groupIndex === boundedGroupIndex ? 'active' : ''}`}
                        onClick={() => onActiveGroupChange?.(groupIndex, filterKeyword)}
                    >
                        {group.name}
                    </button>
                ))}
                <button type="button" className="sub-tab-button" onClick={handleAddGroup}>
                    Add Group
                </button>
                <button
                    type="button"
                    className="sub-tab-button"
                    onClick={handleRemoveGroup}
                    disabled={resolvedGroups.length <= 1}
                >
                    Remove Group
                </button>
            </div>

            {!activeGroup ? (
                <div className="matrix-app-empty-state">No scaling inputs are available for this section.</div>
            ) : (
                <div className="simple-scaling-table-wrapper" style={{ overflowX: 'auto' }}>
                    <table className="results-table" style={{ width: '100%', borderCollapse: 'collapse' }}>
                        <thead>
                            <tr>
                                <th className="table-header">Item</th>
                                <th className="table-header">Base</th>
                                <th className="table-header">Operation</th>
                                <th className="table-header">Factor</th>
                                <th className="table-header">Scaled</th>
                                <th className="table-header">Controls</th>
                            </tr>
                        </thead>
                        <tbody>
                            {activeGroup.items.map((item) => (
                                <tr key={item.id}>
                                    <td className="table-cell">
                                        <div>{item.label}</div>
                                        <div style={{ fontSize: '0.8rem', opacity: 0.7 }}>{item.id}</div>
                                    </td>
                                    <td className="table-cell">{item.baseValue.toFixed(2)}</td>
                                    <td className="table-cell">
                                        <select
                                            value={item.operation}
                                            onChange={(event) => handleItemFieldChange(item.id, 'operation', event.target.value)}
                                        >
                                            {OPERATIONS.map((operation) => (
                                                <option key={operation.id} value={operation.id}>
                                                    {operation.label}
                                                </option>
                                            ))}
                                        </select>
                                    </td>
                                    <td className="table-cell">
                                        <input
                                            type="number"
                                            value={item.scalingFactor}
                                            step="0.01"
                                            onChange={(event) => handleItemFieldChange(item.id, 'scalingFactor', toNumber(event.target.value, 1))}
                                            style={{ width: '6rem' }}
                                        />
                                    </td>
                                    <td className="table-cell">{item.scaledValue.toFixed(2)}</td>
                                    <td className="table-cell">
                                        <label style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem', marginRight: '0.75rem' }}>
                                            <input
                                                type="checkbox"
                                                checked={item.enabled}
                                                onChange={(event) => handleItemFieldChange(item.id, 'enabled', event.target.checked)}
                                            />
                                            Enabled
                                        </label>
                                        {item.vKey && typeof toggleV === 'function' && (
                                            <label style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem', marginRight: '0.75rem' }}>
                                                <input
                                                    type="checkbox"
                                                    checked={V[item.vKey] === 'on'}
                                                    onChange={() => toggleV(item.vKey)}
                                                />
                                                {item.vKey}
                                            </label>
                                        )}
                                        {item.rKey && typeof toggleR === 'function' && (
                                            <label style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}>
                                                <input
                                                    type="checkbox"
                                                    checked={R[item.rKey] === 'on'}
                                                    onChange={() => toggleR(item.rKey)}
                                                />
                                                {item.rKey}
                                            </label>
                                        )}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
};

export default SimpleScalingEditor;
