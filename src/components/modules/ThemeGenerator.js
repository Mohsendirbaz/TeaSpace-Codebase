import chroma from 'chroma-js';

class ThemeGenerator {
    constructor() {
        this.apiEndpoint = 'http://localhost:8010/api/theme';
        this.cssRegistryEndpoint = 'http://localhost:8010/api/css-registry';
        this.originalThemeColors = {};
        
        // Initialize by capturing the original theme colors
        this.captureOriginalThemeColors();
    }

    // Capture current theme colors from CSS variables
    captureOriginalThemeColors() {
        // Get all CSS variables from :root
        const rootStyles = getComputedStyle(document.documentElement);
        const cssVariables = Array.from(rootStyles).filter(prop => 
            prop.startsWith('--')
        );
        
        // Store original values
        this.originalThemeColors = cssVariables.reduce((acc, varName) => {
            acc[varName] = rootStyles.getPropertyValue(varName).trim();
            return acc;
        }, {});
        
        console.log('Captured original theme colors:', this.originalThemeColors);
        return this.originalThemeColors; // Return for chaining
    }

    async applyGradientToCurrentTheme(gradientString) {
        console.group('Applying gradient theme');
        try {
            // Validate gradient format
            if (!gradientString.startsWith('linear-gradient(')) {
                throw new Error('Invalid gradient format');
            }

            // Extract color stops
            const colorStops = gradientString.match(/(rgba?\([^)]+\)|#[0-9a-fA-F]{3,8})/g);
            if (!colorStops || colorStops.length < 2) {
                throw new Error('Invalid gradient color stops');
            }

            // Create CSS variables
            const cssVariables = {
                '--gradient': gradientString,
                '--primary-color': colorStops[0],
                '--secondary-color': colorStops[1]
            };

            // Apply via API first
            try {
                const response = await fetch(`${this.apiEndpoint}/current`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(cssVariables)
                });

                if (response.ok) {
                    console.log('Gradient applied via API');
                    return;
                }
            } catch (apiError) {
                console.warn('API gradient apply failed, falling back to local');
            }

            // Fallback to local application
            const root = document.documentElement;
            Object.entries(cssVariables).forEach(([key, value]) => {
                root.style.setProperty(key, value);
            });

            console.log('Gradient applied locally');
        } catch (error) {
            console.error('Gradient application failed:', error);
            throw error;
        } finally {
            console.groupEnd();
        }
    }

    async loadCurrentThemeColors() {
        console.group('Loading current theme colors');
        try {
            // Try API first
            const response = await fetch(`${this.apiEndpoint}/current`);
            if (response.ok) {
                const colors = await response.json();
                console.log('Loaded colors from API:', colors);
                return colors;
            }
            
            // Fallback to local CSS variables
            console.log('Falling back to local color loading');
            const rootStyles = getComputedStyle(document.documentElement);
            const cssVariables = Array.from(rootStyles).filter(prop => 
                prop.startsWith('--')
            );
            
            const currentColors = cssVariables.reduce((acc, varName) => {
                acc[varName] = rootStyles.getPropertyValue(varName).trim();
                return acc;
            }, {});
            
            console.log('Loaded local colors:', currentColors);
            return currentColors;
        } catch (error) {
            console.error('Color loading failed:', error);
            return this.originalThemeColors; // Return cached colors as fallback
        } finally {
            console.groupEnd();
        }
    }
    
    // [Previous methods remain unchanged...]

    // Apply color change to the current theme
    applyColorToCurrentTheme(colorKey, value) {
        // Handle gradient strings - calculate combined color effect
        const extractColorFromValue = (val) => {
            if (typeof val !== 'string') return val;
            
            // Check if this is a gradient and properly process it
            if (val.trim().startsWith('linear-gradient(')) {
                try {
                    // If this is a gradient string but we're applying to a color, calculate combined effect
                    // For gradients tab, this should work directly
                    if (colorKey === 'gradient') {
                        return val; // Keep the full gradient string
                    }
                    
                    // For color fields, we need to calculate the combined color effect
                    const colors = val.match(/#[a-f0-9]{3,8}|rgba?\([^)]+\)/gi);
                    if (colors && colors.length > 0) {
                        // Calculate weighted average color from gradient stops
                        const colorScale = chroma.scale(colors);
                        let totalWeight = 0;
                        let weightedColor = chroma('black');
                        
                        // Calculate weighted average based on gradient stop positions
                        colors.forEach((color, index) => {
                            const position = index / (colors.length - 1);
                            const weight = 1 - Math.abs(position - 0.5); // More weight to middle colors
                            weightedColor = weightedColor.add(chroma(color).alpha(weight));
                            totalWeight += weight;
                        });
                        
                        const avgColor = weightedColor.alpha(1).hex();
                        
                        // Log detailed gradient processing
                        console.group('Gradient Processing');
                        console.log('Input gradient:', val);
                        console.log('Extracted colors:', colors);
                        console.log('Calculated average color:', avgColor);
                        console.groupEnd();
                        
                        return avgColor;
                    }
                    // If no colors found, return a default
                    return '#8a2be2';
                } catch (err) {
                    console.warn('Error processing gradient:', err);
                    return '#8a2be2';
                }
            }
            
            return val;
        };

        // [Rest of the method remains unchanged...]
    }

    // Apply CSS to selected files
    async applyCssToFiles(files, cssCode) {
        console.group('Starting CSS application process');
        console.log('Initial files to update:', files);
        console.log('CSS code to apply:', cssCode);
        
        try {
            console.log('Attempting to apply CSS via server API...');
            const response = await fetch(`${this.cssRegistryEndpoint}/apply`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ files, cssCode }),
            });
            
            if (response.ok) {
                console.log('CSS successfully applied via server API');
                console.groupEnd();
                return { success: true, message: 'CSS applied via server API' };
            } else {
                const errorData = await response.json();
                console.error('Server API failed:', errorData);
                throw new Error(errorData.message || 'Server failed to apply CSS');
            }
        } catch (error) {
            console.error('CSS application failed:', error);
            console.groupEnd();
            return { 
                success: false, 
                message: error.message,
                stack: error.stack 
            };
        }
    }
}

export default ThemeGenerator;
