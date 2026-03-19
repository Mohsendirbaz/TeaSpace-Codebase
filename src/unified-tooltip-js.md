build an html file for the gneralized duration configuration visualization using techniques from the other two files.

specs:

matrix of variables as first column (all rows first cell) and canonical timescale (year) as default column headers
navigable nested directory of table (pop up window would be fine) with collapsible and expandable sublevels of specific timescale.

techniques from other files most useful for the task are tilted shlef like stacks with animation while interacting with, selectable state, and the services and features requested (i.e. ability to locate, inspect every cell of data in a stable manner)

tilted tiles to allow traversing multi level dimension

# unified-tooltip.js - Architectural Summary

## Overview
A comprehensive React tooltip component (965 lines) that provides a unified interface for displaying various types of contextual information. It supports value tooltips (financial data), climate tooltips (environmental data), and generic tooltips with advanced positioning and animation features.

## Core Architecture

### Level 1: Component Purpose
- **Unified Tooltip System**: Single component for all tooltip needs
- **Multi-Type Support**: Value, climate, and generic tooltips
- **Advanced Positioning**: Smart viewport-aware placement
- **Rich Content**: Complex data visualization within tooltips

### Level 2: Props Interface
```javascript
{
  children: ReactNode,          // Trigger elements
  type: string,                // Tooltip type (climate types)
  data: object,                // Data for climate tooltips
  itemId: string,              // ID for value tooltips
  showMatrix: boolean,         // Show matrix info (value)
  showDetails: boolean,        // Show detailed info (value)
  position: 'top'|'bottom'|'left'|'right',
  width: number,               // Tooltip width (default: 320)
  maxHeight: number,           // Max height (default: 400)
  showDelay: number,           // Show delay (default: 300ms)
  hideDelay: number            // Hide delay (default: 100ms)
}
```

### Level 3: State Management
```javascript
State:
- isVisible: boolean           // Tooltip visibility
- tooltipPosition: {top, left} // Absolute positioning
- tooltipContent: object       // Processed content data
- versions: Jotai atom         // Version state
- zones: Jotai atom           // Zone state
- efficacyGroups: Jotai atom  // Efficacy group data
```

### Level 4: Tooltip Types

#### Value Tooltips (itemId provided)
- Financial parameter display
- Base/scaled/effective values
- Change percentages
- Efficacy periods
- Matrix information

#### Climate Tooltips (type provided)
1. **emissionFactor**: CO₂ emission factors
2. **regulatoryThreshold**: Compliance thresholds
3. **assetCarbonIntensity**: Asset carbon metrics
4. **geographicContext**: Location information
5. **environmentalRisks**: Risk assessments
6. **energyGrid**: Energy mix data

### Level 5: Position Management

#### Smart Positioning Algorithm
```javascript
1. Calculate initial position based on preference
2. Get trigger and tooltip dimensions
3. Check viewport boundaries
4. Adjust to keep within viewport
5. Apply final position
```

#### Position Strategies
- **Top**: Above trigger, centered
- **Bottom**: Below trigger, centered
- **Left**: Left of trigger, middle-aligned
- **Right**: Right of trigger, middle-aligned

### Level 6: Animation System

#### Framer Motion Integration
```javascript
initial: { opacity: 0, scale: 0.9 }
animate: { opacity: 1, scale: 1 }
exit: { opacity: 0, scale: 0.9 }
transition: { duration: 0.2 }
```

#### Delay Management
- Show delay prevents flickering
- Hide delay allows hover continuation
- Timer cleanup on unmount

### Level 7: Content Renderers

#### Value Tooltip Features
- Item label and status
- Group information
- Value comparisons
- Percentage changes
- Efficacy period display
- Matrix context

#### Climate Tooltip Features

##### Emission Factor
- Value with units
- Industry benchmarks
- Confidence levels
- Regional applicability
- Reference examples

##### Regulatory Threshold
- Threshold values
- Compliance status
- Authority information
- Jurisdiction details
- Action recommendations

##### Asset Carbon Intensity
- Current intensity
- Benchmark comparisons
- Alternative technologies
- Decarbonization pathway
- Visual progress bars

##### Geographic Context
- Coordinates display
- Location hierarchy
- Climate classification
- Energy grid info
- Environmental risks
- Climate projections

##### Environmental Risks
- Risk categories
- Severity levels
- Detailed descriptions
- Mitigation recommendations
- Visual indicators

##### Energy Grid
- Carbon intensity
- Renewable percentage
- Energy source mix
- Visual charts
- Comparative scales

### Level 8: Helper Functions

#### Formatting Utilities
```javascript
formatDate(): Localized date display
formatNumber(): K/M suffixes for large numbers
formatRiskName(): Human-readable risk names
formatEnergySource(): Energy type labels
```

#### Content Generators
```javascript
getRiskDescription(): Risk level descriptions
getRiskRecommendation(): Mitigation advice
```

### Level 9: Visual Components

#### Charts and Visualizations
- Progress bars
- Pie charts (SVG)
- Scale indicators
- Benchmark comparisons
- Pathway visualizations

#### Status Indicators
- Compliance badges
- Confidence levels
- Risk severity
- Active/inactive states

### Level 10: CSS Architecture

#### Class Structure
```css
.unified-tooltip-container
.unified-tooltip
.tooltip-value
.tooltip-{type}
.tooltip-{position}
.tooltip-header
.tooltip-content
.tooltip-footer
```

#### Responsive Design
- Width constraints
- Max height with scrolling
- Mobile-friendly sizing
- Touch interaction support

## Advanced Features

### Jotai Integration
- Atom-based state management
- Reactive data updates
- Cross-component state sharing
- Efficient re-renders

### Performance Optimizations
- Conditional content rendering
- Memoized calculations
- Lazy data fetching
- Viewport-based positioning

### Accessibility
- Keyboard navigation support
- ARIA attributes
- Focus management
- Screen reader content

## Usage Patterns

### Value Tooltip
```javascript
<UnifiedTooltip itemId="param123" showMatrix showDetails>
  <span>Hover for details</span>
</UnifiedTooltip>
```

### Climate Tooltip
```javascript
<UnifiedTooltip 
  type="emissionFactor" 
  data={emissionData}
  position="right"
>
  <button>Info</button>
</UnifiedTooltip>
```

This component provides a sophisticated tooltip system capable of displaying complex financial and environmental data with rich visualizations and smart positioning.