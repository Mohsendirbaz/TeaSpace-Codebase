import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import HomePage from './HomePage';
import ErrorBoundary from './utils/ErrorBoundary';
import './styles/HomePage.CSS/UIComponentStyles.css'

function getColorFromTheme(themeClass, varName) {
    try {
        const el = document.createElement("div");
        el.className = themeClass;
        el.style.display = "none";
        document.body.appendChild(el);

        const val = getComputedStyle(el).getPropertyValue(varName).trim();
        document.body.removeChild(el);

        // Validate that we have a proper hex color-
        if (val && /^#([A-Fa-f0-9]{3}){1,2}$/.test(val)) {
            return val;
        }
        console.warn(`Invalid color value for ${varName} in ${themeClass}: ${val}`);
        return "#000000"; // Default to black for invalid colors
    } catch (error) {
        console.error(`Error getting color from theme: ${error.message}`);
        return "#000000"; // Default to black on error
    }
}

function getAverageThemeColor(varName, themes) {
    const hexToRgb = (hex) => {
        const matches = hex && hex.match(/\w\w/g);
        return matches ? matches.map((x) => parseInt(x, 16)) : [0, 0, 0]; // Default to black if invalid
    };

    const rgbToHex = (rgb) =>
        "#" + rgb.map((x) => x.toString(16).padStart(2, "0")).join("");

    const rgbs = themes.map((theme) =>
        hexToRgb(getColorFromTheme(theme, varName))
    );

    // Handle case where no valid RGB values were found
    if (!rgbs.length || !rgbs[0]) {
        return "#000000"; // Default to black
    }

    const avg = rgbs[0].map((_, i) =>
        Math.floor(rgbs.reduce((sum, rgb) => sum + rgb[i], 0) / rgbs.length)
    );

    return rgbToHex(avg);
}

function applyAverageColors() {
    try {
        const avgText = getAverageThemeColor("--text-color", [
            "light-theme",
            "dark-theme",
            "creative-theme"
        ]);

        document.documentElement.style.setProperty("--avg-text-color", avgText);

        // You can add more average colors here if needed
        // For example:
        // const avgBackground = getAverageThemeColor("--background-color", [...]);
        // document.documentElement.style.setProperty("--avg-background-color", avgBackground);
    } catch (error) {
        console.error("Error applying average colors:", error);
        // Set fallback colors if averaging fails
        document.documentElement.style.setProperty("--avg-text-color", "#333333");
    }
}

function App() {
    useEffect(() => {
        applyAverageColors(); // Call after mount
    }, []);

    return (
        <ErrorBoundary>
            <Router>
                <Routes>
                    <Route path="/" element={<HomePage />} />
                </Routes>
            </Router>
        </ErrorBoundary>
    );
}

export default App;

