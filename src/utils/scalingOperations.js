/**
 * Scaling operations available for use in the scaling system
 * Each operation has an id, label, symbol, and description
 */
const scalingOperations = [
    {
        id: 'multiply',
        label: 'Multiply',
        symbol: '×',
        description: 'Multiplies the base value by the scaling factor'
    },
    {
        id: 'power',
        label: 'Power',
        symbol: '^',
        description: 'Raises the base value to the power of the scaling factor'
    },
    {
        id: 'divide',
        label: 'Divide',
        symbol: '÷',
        description: 'Divides the base value by the scaling factor'
    },
    {
        id: 'log',
        label: 'Logarithmic',
        symbol: 'ln',
        description: 'Applies logarithmic scaling using the natural log'
    },
    {
        id: 'exponential',
        label: 'Exponential',
        symbol: 'eˣ',
        description: 'Applies exponential scaling'
    },
    {
        id: 'add',
        label: 'Add',
        symbol: '+',
        description: 'Adds the scaling factor to the base value'
    },
    {
        id: 'subtract',
        label: 'Subtract',
        symbol: '-',
        description: 'Subtracts the scaling factor from the base value'
    }
];

export default scalingOperations;