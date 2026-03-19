import React, { useState, useEffect, useRef } from 'react';
import '../../styles/HomePage.CSS/HCSS.css';
import TicTacToe from './TicTacToe';
import WhakAMole from './WhakAMole';
import PendulumClock from './PendulumClock';

const StickerHeader = () => {
    const [stickers, setStickers] = useState([]);
    const stickersRef = useRef([]);
    const [animationSpeed, setAnimationSpeed] = useState(1.0);
    const [effectFrequency, setEffectFrequency] = useState(10);
    const [dipoleStrength, setDipoleStrength] = useState(50);
    const [dipoleRadius, setDipoleRadius] = useState(30);
    const animationFramesRef = useRef({});
    const [showClock, setShowClock] = useState(false);
    const toggleClock = () => {
        setShowClock(prev => !prev);
    };
    // Track dipole locations
    const [dipoles, setDipoles] = useState([
        { x: 25, y: 25, strength: 1, type: 'attractive' },  // Top left quadrant
        { x: 75, y: 25, strength: -1, type: 'repulsive' },  // Top right quadrant
        { x: 25, y: 75, strength: -1, type: 'repulsive' },  // Bottom left quadrant
        { x: 75, y: 75, strength: 1, type: 'attractive' }   // Bottom right quadrant
    ]);

    const messages = [
        'Synthesize disparate elements into cohesive strategies',
        'Manipulate, analyze, and internalize',
        'Transform complex data into actionable insights',
        'Bridge theory and practice',
        'Foster innovative thinking',
        'Develop systematic approaches',
        'Create sustainable solutions',
        'Integrate multiple perspectives'
    ];

    // Theme-based gradients using CSS variables
    const gradients = [
        `linear-gradient(135deg, var(--primary-color), var(--secondary-color))`,
        `linear-gradient(135deg, var(--accent-color), var(--info-color))`,
        `linear-gradient(135deg, var(--model-color-primary), var(--model-color-success))`,
        `linear-gradient(135deg, var(--spatial-gradient-start), var(--spatial-gradient-end))`,
        `linear-gradient(135deg, var(--primary-color), var(--info-color))`,
        `linear-gradient(135deg, var(--accent-color), var(--secondary-color))`,
        `linear-gradient(135deg, var(--warning-color), var(--accent-color))`,
        `linear-gradient(135deg, var(--model-color-primary), var(--info-color))`,
        `linear-gradient(135deg, var(--accent-color), var(--model-color-success))`,
        `linear-gradient(135deg, var(--spatial-gradient-start), var(--primary-color))`
    ];

    // Animation durations, with one value being significantly larger
    const baseDurations = [5, 6, 7, 8, 9, 10, 50, 7, 8, 9];

    // Calculate dipole effect on a sticker
    const calculateDipoleEffect = (stickerLeft, stickerTop) => {
        // Convert percentage positions to numeric values
        const stickerX = parseFloat(stickerLeft);
        const stickerY = parseFloat(stickerTop);

        let rotationMultiplier = 1.0;
        let velocityBoost = 0;
        let isInDipoleField = false;

        // Check each dipole's influence
        dipoles.forEach(dipole => {
            // Calculate distance to dipole center
            const dx = stickerX - dipole.x;
            const dy = stickerY - dipole.y;
            const distance = Math.sqrt(dx * dx + dy * dy);

            // If sticker is within dipole's field of influence
            if (distance < dipoleRadius) {
                isInDipoleField = true;
                // Inverse square law for field strength
                const fieldStrength = (dipoleStrength / 100) * dipole.strength * (1 - distance / dipoleRadius);

                // Adjust rotation multiplier based on field strength
                rotationMultiplier += fieldStrength * 5;

                // Add velocity boost
                velocityBoost += fieldStrength * 40;
            }
        });

        return { rotationMultiplier, velocityBoost, isInDipoleField };
    };

    // Physics-based rotation function with dipole effects
    const startPhysicsRotation = (stickerId) => {
        // Cancel any existing animation for this sticker
        if (animationFramesRef.current[stickerId]) {
            cancelAnimationFrame(animationFramesRef.current[stickerId]);
        }

        const sticker = stickersRef.current.find(s => s.id === stickerId);
        if (!sticker) return;

        // Calculate dipole effect
        const { rotationMultiplier, velocityBoost } = calculateDipoleEffect(sticker.left, sticker.top);

        // Set initial spinning state with higher velocity for multiple rotations
        updateSticker(stickerId, {
            isSpinning: true,
            rotation: 0,
            totalRotation: 0, // Track total rotation angle
            // Physics parameters adjusted for faster, multiple rotations
            angularVelocity: ((25 + Math.random() * 25) * animationSpeed + velocityBoost) * rotationMultiplier,
            dampingCoefficient: 0.99, // Reduced damping for longer rotation
            tangentialShear: (Math.random() * 4 - 2) * rotationMultiplier, // Stronger tangential force (-2 to 2)
            rotationDirection: Math.random() > 0.5 ? 1 : -1, // Random direction
            lastTimestamp: performance.now(),
            pauseFloating: true, // Pause the floating animation
            finalRotationApplied: false, // Track if we've applied the final rotation
            dipoleInfluenced: rotationMultiplier > 1.0 // Track if this rotation was influenced by dipoles
        });

        const startTime = performance.now();
        const maxDuration = 4000 / animationSpeed; // Extended duration for natural damping

        // Animate function
        const animate = (currentTime) => {
            const sticker = stickersRef.current.find(s => s.id === stickerId);
            if (!sticker) return;

            // Calculate time delta in seconds
            const deltaTime = (currentTime - sticker.lastTimestamp) / 1000;
            const elapsedTime = currentTime - startTime;
            const progress = Math.min(elapsedTime / maxDuration, 1);

            // Apply physics calculations
            let { angularVelocity, dampingCoefficient, tangentialShear, rotationDirection, rotation, totalRotation } = sticker;

            // Recalculate dipole effect during animation for dynamic response
            const { rotationMultiplier, velocityBoost, isInDipoleField } = calculateDipoleEffect(sticker.left, sticker.top);

            // Calculate effective shear that varies over time
            const effectiveShear = tangentialShear * Math.sin(progress * Math.PI) * 15 * rotationMultiplier;

            // Apply damping based on current velocity (time-based)
            // Reduce damping if in dipole field for more dramatic effects
            const effectiveDamping = isInDipoleField ?
                Math.max(0.995, dampingCoefficient) :
                dampingCoefficient;

            angularVelocity *= Math.pow(effectiveDamping, deltaTime * 60);

            // Apply tangential shear and velocity boost from dipoles
            angularVelocity += effectiveShear + (velocityBoost * deltaTime);

            // Calculate new rotation angle (in degrees)
            const rotationDelta = angularVelocity * deltaTime * rotationDirection;
            rotation = (rotation + rotationDelta); // Don't reset to 0-360 range for smoother animation
            totalRotation += Math.abs(rotationDelta); // Track total rotation for completion

            // Update sticker with new values
            updateSticker(stickerId, {
                rotation,
                totalRotation,
                angularVelocity,
                tangentialShear: tangentialShear * 0.98,
                lastTimestamp: currentTime,
                dipoleInfluenced: isInDipoleField || sticker.dipoleInfluenced
            });

            // Continue animation if not finished:
            // - Angular velocity is still significant, AND
            // - Haven't reached maximum duration
            // - Must have completed at least 1.5 full rotations (540 degrees)
            if (Math.abs(angularVelocity) > 0.2 && progress < 1 && (totalRotation < 540 || Math.abs(angularVelocity) > 5)) {
                animationFramesRef.current[stickerId] = requestAnimationFrame(animate);
            } else {
                // Natural transition to floating animation
                // Calculate the final rotation that will look natural with the floating animation
                const finalRotation = rotation % 360; // Normalize to 0-360 for compatibility

                // Apply a new gradient
                const newGradientIndex = Math.floor(Math.random() * gradients.length);

                // Calculate new rotation degree for the CSS animation that aligns with current rotation
                const newRotationDegree = (finalRotation > 180) ?
                    (finalRotation - 360) % 20 :
                    finalRotation % 20;

                // Apply the final state - keep the current rotation position
                updateSticker(stickerId, {
                    isSpinning: false,
                    pauseFloating: false,
                    rotationDegree: newRotationDegree, // New base rotation for floating animation
                    background: gradients[newGradientIndex],
                    finalRotationApplied: true,
                    dipoleInfluenced: false
                });
            }
        };

        // Start animation
        animationFramesRef.current[stickerId] = requestAnimationFrame(animate);
    };

    // Initialize stickers
    useEffect(() => {
        const initialStickers = messages.map((message, index) => {
            const left = `${Math.random() * 80}%`;
            const top = `${Math.random() * 80}%`;
            const durationIndex = Math.floor(Math.random() * baseDurations.length);
            const gradientIndex = Math.floor(Math.random() * gradients.length);

            return {
                id: index,
                message,
                left,
                top,
                duration: baseDurations[durationIndex],
                background: gradients[gradientIndex],
                isSpinning: false,
                rotation: 0,
                totalRotation: 0,
                pauseFloating: false,
                rotationDegree: Math.floor(Math.random() * 20) - 10,
                floatDistance: Math.floor(Math.random() * 20) + 10,
                finalRotationApplied: false,
                dipoleInfluenced: false
            };
        });

        setStickers(initialStickers);
        stickersRef.current = initialStickers;
    }, []);

    // Function to update a sticker's properties
    const updateSticker = (id, updates) => {
        setStickers(prevStickers =>
            prevStickers.map(sticker =>
                sticker.id === id ? { ...sticker, ...updates } : sticker
            )
        );

        // Also update the ref for immediate access
        stickersRef.current = stickersRef.current.map(sticker =>
            sticker.id === id ? { ...sticker, ...updates } : sticker
        );
    };

    // Random color changes
    useEffect(() => {
        const colorIntervals = stickers.map(sticker => {
            return setInterval(() => {
                // Only change colors for stickers that aren't spinning
                if (!sticker.isSpinning) {
                    const newGradientIndex = Math.floor(Math.random() * gradients.length);
                    updateSticker(sticker.id, {
                        background: gradients[newGradientIndex]
                    });
                }
            }, Math.random() * 10000 + 5000); // Change color every 5-15 seconds
        });

        return () => {
            colorIntervals.forEach(interval => clearInterval(interval));
        };
    }, [stickers]);

    // Random speed changes
    useEffect(() => {
        const speedIntervals = stickers.map(sticker => {
            return setInterval(() => {
                // Only change speeds for stickers that aren't spinning
                if (!sticker.isSpinning) {
                    const newDurationIndex = Math.floor(Math.random() * baseDurations.length);
                    const adjustedDuration = baseDurations[newDurationIndex] / animationSpeed;
                    updateSticker(sticker.id, { duration: adjustedDuration });
                }
            }, Math.random() * 15000 + 10000); // Change speed every 10-25 seconds
        });

        return () => {
            speedIntervals.forEach(interval => clearInterval(interval));
        };
    }, [stickers, animationSpeed]);

    // Surprise rotation effect with frequency control
    useEffect(() => {
        const spinInterval = setInterval(() => {
            if (stickersRef.current.length === 0) return;

            // Randomly select a sticker to spin (that isn't already spinning)
            const availableStickers = stickersRef.current.filter(s => !s.isSpinning);
            if (availableStickers.length === 0) return;

            const randomIndex = Math.floor(Math.random() * availableStickers.length);
            const stickerId = availableStickers[randomIndex].id;

            // Start physics-based rotation
            startPhysicsRotation(stickerId);

        }, effectFrequency * 1000); // Controlled by frequency slider

        return () => {
            clearInterval(spinInterval);

            // Clean up any active animations
            Object.keys(animationFramesRef.current).forEach(id => {
                cancelAnimationFrame(animationFramesRef.current[id]);
            });
        };
    }, [effectFrequency, animationSpeed, dipoleStrength, dipoleRadius]);

    // Update all stickers when animation speed changes
    useEffect(() => {
        if (stickersRef.current.length === 0) return;

        stickersRef.current.forEach(sticker => {
            if (!sticker.isSpinning) {
                const baseDuration = baseDurations[baseDurations.indexOf(sticker.duration) !== -1 ?
                    baseDurations.indexOf(sticker.duration) :
                    Math.floor(Math.random() * baseDurations.length)];
                const adjustedDuration = baseDuration / animationSpeed;
                updateSticker(sticker.id, { duration: adjustedDuration });
            }
        });
    }, [animationSpeed]);
    // Game control states
    const [showGamesMenu, setShowGamesMenu] = useState(false);
    const [activeGame, setActiveGame] = useState(null);

    // Toggle games menu
    const toggleGamesMenu = () => {
        setShowGamesMenu(prev => !prev);
    };

    // Launch a game
    const launchGame = (game) => {
        setActiveGame(game);
        setShowGamesMenu(false);
    };

    // Close active game
    const closeGame = () => {
        setActiveGame(null);
    };
    return (
        <header className="sticker-header">
            <div className="sticker-container">
                {stickers.map((sticker) => {
                    // Define custom CSS variables for each sticker
                    const stickerVars = {
                        '--sticker-rotate-degree': `${sticker.rotationDegree}deg`,
                        '--sticker-float-distance': `${sticker.floatDistance}px`,
                        left: sticker.left,
                        top: sticker.top,
                        boxShadow: sticker.isSpinning ? 'var(--neu-shadow-lg)' : 'var(--neu-shadow-md)',
                    };

                    // Calculation of transform based on state
                    if (sticker.isSpinning) {
                        // During physics rotation, use the calculated rotation value
                        stickerVars.transform = `rotate(${sticker.rotation}deg)`;
                        stickerVars.animationName = 'none'; // Pause floating animation

                        // Add glow effect for stickers influenced by dipoles
                        if (sticker.dipoleInfluenced) {
                            stickerVars.boxShadow = '0 0 15px rgba(var(--primary-color-rgb), 0.8), var(--neu-shadow-lg)';
                            stickerVars.zIndex = 5; // Bring to front
                        }
                    } else if (sticker.finalRotationApplied) {
                        // Just ended spinning animation - handle transition to floating
                        stickerVars.transform = 'none'; // Let the CSS animation take over
                        stickerVars.animationDuration = `${sticker.duration}s`;
                        stickerVars.animationName = 'floating';
                        sticker.finalRotationApplied = false; // Reset for next time
                    } else {
                        // Normal floating animation
                        stickerVars.transform = 'none';
                        stickerVars.animationDuration = `${sticker.duration}s`;
                        stickerVars.animationName = 'floating';
                    }

                    return (
                        <div
                            key={sticker.id}
                            className={`sticker ${!sticker.isSpinning ? 'sticker-floating' : ''} ${sticker.dipoleInfluenced ? 'dipole-influenced' : ''}`}
                            style={stickerVars}
                        >
                            <p className="sticker-text">
                                {sticker.message}
                            </p>
                        </div>
                    );
                })}
            </div>

            {/* Visualize dipoles for debugging/visibility */}
            {dipoles.map((dipole, index) => (
                <div
                    key={`dipole-${index}`}
                    className={`dipole-marker ${dipole.type}`}
                    style={{
                        left: `${dipole.x}%`,
                        top: `${dipole.y}%`,
                        width: `${dipoleRadius * 2}%`,
                        height: `${dipoleRadius * 2}%`,
                        transform: 'translate(-50%, -50%)',
                        opacity: dipoleStrength / 100
                    }}
                />
            ))}

            <div className="header-content">
                <h1 className="header-title">
                    Ziptovic
                </h1>
                <h2 className="header-subtitle">
                    Techno-Economic-Social Simulation and Dynamic Modeling
                </h2>
            </div>
            {/* Clock toggle button */}
            <button className="clock-toggle-button" onClick={toggleClock}>
                <span role="img" aria-label="Clock">⏰</span> {showClock ? 'Hide Clock' : 'Show Clock'}
            </button>

            {/* Pendulum Clock */}
            {showClock && (
                <div className="clock-overlay">
                    <PendulumClock size="medium" />
                </div>
            )}
            {/* Games Menu Button - Improved positioning */}
            <button className="games-menu-button" onClick={toggleGamesMenu}>
                <span role="img" aria-label="Games">🎮</span> Games
            </button>

            {/* Games Menu Dropdown */}
            {showGamesMenu && (
                <div className="games-menu">
                    <div className="games-menu-header">
                        <h3>Mini Games</h3>
                        <button className="close-button" onClick={() => setShowGamesMenu(false)}>×</button>
                    </div>
                    <div className="games-list">
                        <button className="game-option" onClick={() => launchGame('tictactoe')}>
                            <span role="img" aria-label="Tic-Tac-Toe">⭕❌</span> Tic-Tac-Toe
                        </button>
                        <button className="game-option" onClick={() => launchGame('whakamole')}>
                            <span role="img" aria-label="Whack-a-Mole">🔨</span> Whack-a-Mole
                        </button>
                    </div>
                </div>
            )}

            {/* Game Overlays */}
            <div className={`game-overlay ${activeGame ? 'active' : ''}`}>
                <div className="game-container">
                    {activeGame === 'tictactoe' && <TicTacToe onClose={closeGame} />}
                    {activeGame === 'whakamole' && <WhakAMole onClose={closeGame} />}
                </div>
            </div>
            <div className="animation-controls">
                <div className="control-group">
                    <label>Speed</label>
                    <input
                        type="range"
                        min="0.1"
                        max="2"
                        step="0.1"
                        value={animationSpeed}
                        onChange={(e) => setAnimationSpeed(parseFloat(e.target.value))}
                    />
                    <span className="control-value">{animationSpeed.toFixed(1)}x</span>
                </div>
                <div className="control-group">
                    <label>Effect Frequency</label>
                    <input
                        type="range"
                        min="2"
                        max="30"
                        step="1"
                        value={effectFrequency}
                        onChange={(e) => setEffectFrequency(parseInt(e.target.value))}
                    />
                    <span className="control-value">{effectFrequency}s</span>
                </div>
                <div className="control-group">
                    <label>Dipole Strength</label>
                    <input
                        type="range"
                        min="0"
                        max="100"
                        step="1"
                        value={dipoleStrength}
                        onChange={(e) => setDipoleStrength(parseInt(e.target.value))}
                    />
                    <span className="control-value">{dipoleStrength}%</span>
                </div>
                <div className="control-group">
                    <label>Dipole Radius</label>
                    <input
                        type="range"
                        min="10"
                        max="50"
                        step="1"
                        value={dipoleRadius}
                        onChange={(e) => setDipoleRadius(parseInt(e.target.value))}
                    />
                    <span className="control-value">{dipoleRadius}%</span>
                </div>
            </div>
        </header>
    );
};

export default StickerHeader;
