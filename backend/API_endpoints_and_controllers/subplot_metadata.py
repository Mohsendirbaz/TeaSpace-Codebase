from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import json
import os

app = Flask(__name__)
CORS(app)  # This enables CORS for all routes

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("subplot_metadata.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@app.route('/subplotMetadata', methods=['GET'])
def get_subplot_metadata():
    """
    Endpoint to retrieve metadata about available subplots
    Provides information about available metrics and visualizations
    
    Returns:
        JSON response with subplot metadata
    """
    try:
        # Define the standard metrics and their presentable names
        metrics = {
            'Annual_Cash_Flows': {
                'title': 'Annual Cash Flows',
                'description': 'Yearly cash flows after taxes',
                'abbreviation': 'ACF',
                'yAxisLabel': 'Cash Flow ($)',
                'defaultActive': True
            },
            'Annual_Revenues': {
                'title': 'Annual Revenues',
                'description': 'Yearly revenue before expenses',
                'abbreviation': 'ARV',
                'yAxisLabel': 'Revenue ($)', 
                'defaultActive': True
            },
            'Annual_Operating_Expenses': {
                'title': 'Annual Operating Expenses',
                'description': 'Yearly operating costs',
                'abbreviation': 'AOE',
                'yAxisLabel': 'Expenses ($)',
                'defaultActive': False
            },
            'Loan_Repayment_Terms': {
                'title': 'Loan Repayment Terms',
                'description': 'Yearly loan payments',
                'abbreviation': 'LRT',
                'yAxisLabel': 'Repayment ($)',
                'defaultActive': False
            },
            'Depreciation_Schedules': {
                'title': 'Depreciation Schedules',
                'description': 'Yearly asset depreciation',
                'abbreviation': 'DSC',
                'yAxisLabel': 'Depreciation ($)',
                'defaultActive': False
            },
            'State_Taxes': {
                'title': 'State Taxes',
                'description': 'Yearly state tax payments',
                'abbreviation': 'STX',
                'yAxisLabel': 'State Taxes ($)',
                'defaultActive': False
            },
            'Federal_Taxes': {
                'title': 'Federal Taxes',
                'description': 'Yearly federal tax payments',
                'abbreviation': 'FTX',
                'yAxisLabel': 'Federal Taxes ($)',
                'defaultActive': False
            },
            'Cumulative_Cash_Flows': {
                'title': 'Cumulative Cash Flows',
                'description': 'Running total of cash flows',
                'abbreviation': 'CCF',
                'yAxisLabel': 'Cumulative Cash Flow ($)',
                'defaultActive': False
            }
        }
        
        # Return the metadata as JSON
        return jsonify(metrics)
    
    except Exception as e:
        logger.error(f"Error getting subplot metadata: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5011))
    app.run(debug=True, port=port)