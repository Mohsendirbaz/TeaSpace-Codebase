# Blueprints package initialization
from .health import health_bp
from .payload import payload_bp
from .baseline import baseline_bp
from .sensitivity import sensitivity_bp
from .runs import runs_bp
from .advanced_sensitivity import advanced_sensitivity_bp

# Export all blueprints for app registration
__all__ = [
    'health_bp',
    'payload_bp',
    'baseline_bp',
    'sensitivity_bp',
    'runs_bp',
    'advanced_sensitivity_bp'
]
