import logging

# Function to calculate state tax
def calculate_state_tax(revenue, stateTaxRateAmount32, operating_expenses, depreciation):
    taxable_income = revenue - operating_expenses - depreciation
    tax = max(taxable_income, 0) * stateTaxRateAmount32

    return tax

# Function to calculate federal tax
def calculate_federal_tax(revenue, federalTaxRateAmount33, operating_expenses, depreciation):
    taxable_income = revenue - operating_expenses - depreciation
    tax = max(taxable_income, 0) * federalTaxRateAmount33

    return tax