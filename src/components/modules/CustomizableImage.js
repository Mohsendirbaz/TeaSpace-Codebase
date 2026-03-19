import React, { useState, useEffect } from 'react';

const CustomizableImage = ({ src, alt, width, height, style, onLoad }) => {
    const [imageState, setImageState] = useState({
        blobUrl: '',
        loading: true,
        error: null
    });

    useEffect(() => {
        let mounted = true;
        
        const loadImage = async () => {
            try {
                const response = await fetch(src);
                if (!mounted) return;
                
                const blob = await response.blob();
                if (!mounted) return;
                
                const objectUrl = URL.createObjectURL(blob);
                
                setImageState({
                    blobUrl: objectUrl,
                    loading: false,
                    error: null
                });
                
                if (onLoad) onLoad();
                
            } catch (error) {
                if (mounted) {
                    setImageState(prev => ({
                        ...prev,
                        loading: false,
                        error: error.message
                    }));
                }
            }
        };

        loadImage();

        return () => {
            mounted = false;
            if (imageState.blobUrl) {
                URL.revokeObjectURL(imageState.blobUrl);
            }
        };
    }, [src]); // Remove onLoad from dependencies

    if (imageState.loading) {
        return <div style={style}>Loading...</div>;
    }

    if (imageState.error) {
        return <div style={style}>Error loading image: {imageState.error}</div>;
    }

    return (
        <div style={{ ...style, position: 'relative' }}>
            <img
                src={imageState.blobUrl}
                alt={alt}
                width={width}
                height={height}
                style={{ cursor: 'pointer' }}
            />
            <button
                onClick={() => window.open(imageState.blobUrl, '_blank')}
                style={{
                    position: 'absolute',
                    bottom: '10px',
                    right: '10px',
                    backgroundColor: '#4CAF50',
                    color: 'white',
                    padding: '5px 10px',
                    border: 'none',
                    cursor: 'pointer',
                }}
            >
                Download
            </button>
        </div>
    );
};

export default CustomizableImage;