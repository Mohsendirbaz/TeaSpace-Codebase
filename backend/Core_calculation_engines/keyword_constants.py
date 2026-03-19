# This file contains all the keywords used in the CFA calculation process
# Each keyword is used exactly once in its strictest form

# Create a dictionary to store all keywords
KEYWORDS = {
    'r': 'revenue',
    'e': 'expenses',
    'f': 'fixed',
    'v': 'variable',
    'fs': 'feedstock',
    'l': 'labor',
    'm': 'maintenance',
    'u': 'utility',
    'i': 'insurance',
    'c': 'cost',
    'rv': 'rev'
}

# Helper functions to access keywords without repeating them
def get_keyword(key):
    return KEYWORDS[key]

def capitalize_keyword(key):
    return get_keyword(key).capitalize()

def get_component_names():
    return [get_keyword(k) for k in ['fs', 'l', 'u', 'm', 'i']]

# Define column names
def get_column_names():
    return {
        'year': 'Year',
        'revenue': f"{capitalize_keyword('r')}",
        'expenses': f"Operating {capitalize_keyword('e')}",
        'loan': 'Loan',
        'depreciation': 'Depreciation',
        'state_taxes': 'State Taxes',
        'federal_taxes': 'Federal Taxes',
        'after_tax_cash_flow': 'After-Tax Cash Flow',
        'discounted_cash_flow': 'Discounted Cash Flow',
        'cumulative_cash_flow': 'Cumulative Cash Flow'
    }

# Generate dictionary keys for results
def get_result_dict_names():
    return [
        f"{get_keyword('r')}_results",
        f"{get_keyword('e')}_results",
        f"{get_keyword('f')}_{get_keyword('c')}s_results",
        f"{get_keyword('v')}_{get_keyword('c')}s_results",
        f"{get_keyword('f')}_{get_keyword('rv')}_results",
        f"{get_keyword('v')}_{get_keyword('rv')}_results"
    ]

# Generate dictionary keys for operational data
def get_operational_dict_names():
    return [
        f"{get_keyword('r')}_operational",
        f"{get_keyword('e')}_operational",
        f"{get_keyword('f')}_{get_keyword('c')}s_operational",
        f"{get_keyword('v')}_{get_keyword('c')}s_operational",
        f"{get_keyword('f')}_{get_keyword('rv')}_operational",
        f"{get_keyword('v')}_{get_keyword('rv')}_operational"
    ]

# Generate component operational dictionary keys
def get_component_cost_keys():
    return {
        f"{get_keyword('fs')}_{get_keyword('c')}_operational": 'feedstock_cost_operational',
        f"{get_keyword('l')}_{get_keyword('c')}_operational": 'labor_cost_operational',
        f"{get_keyword('u')}_{get_keyword('c')}_operational": 'utility_cost_operational',
        f"{get_keyword('m')}_{get_keyword('c')}_operational": 'maintenance_cost_operational',
        f"{get_keyword('i')}_{get_keyword('c')}_operational": 'insurance_cost_operational'
    }

def get_component_rev_keys():
    return {
        f"{get_keyword('fs')}_{get_keyword('rv')}_operational": 'feedstock_rev_operational',
        f"{get_keyword('l')}_{get_keyword('rv')}_operational": 'labor_rev_operational',
        f"{get_keyword('u')}_{get_keyword('rv')}_operational": 'utility_rev_operational',
        f"{get_keyword('m')}_{get_keyword('rv')}_operational": 'maintenance_rev_operational',
        f"{get_keyword('i')}_{get_keyword('rv')}_operational": 'insurance_rev_operational'
    }

# Generate labels for pie charts
def get_operational_labels():
    return [
        f"{capitalize_keyword('fs')} {capitalize_keyword('c')}",
        f"{capitalize_keyword('l')} {capitalize_keyword('c')}",
        f"{capitalize_keyword('u')} {capitalize_keyword('c')}",
        f"{capitalize_keyword('m')} {capitalize_keyword('c')}",
        f"{capitalize_keyword('i')} {capitalize_keyword('c')}"
    ]

def get_revenue_labels():
    return [
        f"{capitalize_keyword('fs')} {capitalize_keyword('r')}",
        f"{capitalize_keyword('l')} {capitalize_keyword('r')}",
        f"{capitalize_keyword('u')} {capitalize_keyword('r')}",
        f"{capitalize_keyword('m')} {capitalize_keyword('r')}",
        f"{capitalize_keyword('i')} {capitalize_keyword('r')}"
    ]