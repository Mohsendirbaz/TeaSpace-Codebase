# centered-perspective-demo.js - Architectural Summary

## Overview
A React component (135 lines) that creates an interactive 3D perspective demonstration with rotating tiles. It showcases advanced CSS 3D transforms with synchronized rotation and selection states.

## Core Architecture

### Level 1: Component Purpose
- **3D Showcase**: Demonstrates CSS 3D perspective
- **Interactive Tiles**: Clickable tile selection
- **Synchronized Animation**: All tiles rotate together
- **Visual Effects**: Depth, scale, and glow effects

### Level 2: State Management
```javascript
State:
- selectedIndex: number|null  // Currently selected tile
- rotationAngle: number      // Shared rotation angle (-60 default)
```

### Level 3: Data Structure
```javascript
tiles = [
  {
    id: string,        // Unique identifier
    title: string,     // Display name
    icon: string,      // Unicode symbol
    color: string      // Hex color (#4338ca)
  }
]
```

### Level 4: Interaction Logic

#### handleTileClick(index)
```javascript
Logic:
- If clicking selected tile: Deselect and reset rotation
- If clicking new tile: Select and change rotation
- Rotation angles: -60° (default) → -30° (selected)
```

### Level 5: Layout Calculation

#### getTilePositions()
```javascript
Parameters:
- tileWidth: 100px
- spacing: 80px
- visibleWidth: 180px (tile + spacing)

Calculation:
- Total width based on tile count
- Center alignment using negative margins
- Equal spacing between tiles
```

### Level 6: 3D Transform System

#### Perspective Container
```css
perspective: 1200px
perspectiveOrigin: 50% 50%  // Centered view
```

#### Transform Properties
```javascript
transform: `
  translate3d(0, 0, ${zDepth}px)    // Z-axis positioning
  rotateY(${rotationAngle}deg)      // Y-axis rotation
  scale(${scale})                   // Size scaling
`
```

### Level 7: Visual States

#### Selected Tile
- zDepth: 50px (forward)
- scale: 1.25 (enlarged)
- opacity: 1 (full)
- Glow shadow effect

#### Unselected Tiles
- zDepth: -30px (back)
- scale: 1 (normal)
- opacity: 0.8 (dimmed)

#### When Another Selected
- zDepth: -50px (further back)
- scale: 0.9 (smaller)
- opacity: 0.6 (more dimmed)

### Level 8: Styling Details

#### Tile Appearance
```javascript
- Size: 100×140px
- Background: Linear gradient
- Border: Semi-transparent white
- Border radius: 12px
- Centered content layout
```

#### Shadow Effects
- Selected: Glowing blue shadow
- Normal: Standard drop shadow
- Edge highlight: Inset shadows

### Level 9: Animation Properties

#### Transition Configuration
```css
transform: 0.5s cubic-bezier(0.34, 1.56, 0.64, 1)
opacity: 0.3s ease
```

#### Animation Features
- Smooth rotation transitions
- Elastic cubic-bezier curve
- Synchronized movement
- Hardware acceleration (3D)

### Level 10: Performance Optimizations

#### CSS Properties
- transformStyle: preserve-3d
- backfaceVisibility: hidden
- will-change implied by 3D
- GPU acceleration via translate3d

## Visual Design

### Tile Icons
- ◈ Quartz White
- ◆ Granite Black
- ◇ Marble Grey
- ◯ Terrazzo Mix
- ▢ Slate Blue

### Color Scheme
- Primary: #4338ca (Indigo)
- Gradient: Indigo to dark blue
- White accents and text
- Semi-transparent overlays

## Key Features
1. **Synchronized Rotation**: All tiles rotate together
2. **Depth Perception**: Z-axis positioning
3. **Interactive Selection**: Click to focus
4. **Smooth Animations**: Elastic transitions
5. **Visual Hierarchy**: Selected tile prominence

## Usage Pattern
```javascript
<CenteredPerspectiveDemo />
```

This component creates an engaging 3D interface perfect for product showcases, galleries, or interactive selections with sophisticated visual effects.