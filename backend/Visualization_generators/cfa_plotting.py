"""
CFA Plotting Module

This module contains functions for generating and saving plots related to Cash Flow Analysis (CFA).
It includes functions for creating pie charts and other visualizations to represent economic data.
"""

import os
import numpy as np
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def generate_economic_breakdown_pie_chart(results_folder, version, economic_data):
    """
    Generate and save a pie chart showing the economic breakdown using Plotly.
    
    Args:
        results_folder (str): Path to the folder where results will be saved
        version (str): Version identifier
        economic_data (dict): Dictionary containing economic data with keys:
            - average_annual_revenue
            - average_annual_operating_expenses
            - average_annual_state_taxes
            - average_annual_federal_taxes
    """
    # Extract data
    labels = [
        'Annual Revenue',
        'Annual Operating Expenses',
        'Annual State Taxes',
        'Annual Federal Taxes'
    ]
    sizes = [
        economic_data['average_annual_revenue'],
        economic_data['average_annual_operating_expenses'],
        economic_data['average_annual_state_taxes'],
        economic_data['average_annual_federal_taxes']
    ]

    # Create pie chart
    pie_chart = px.pie(
        values=sizes, 
        names=labels, 
        title='Economic Breakdown', 
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    
    # Customize layout and styling
    pie_chart.update_layout(
        title=dict(
            text='Macro Economics Breakdown', 
            font=dict(family='Georgia', size=18, color='black'),
            x=0.5,  # Center title
            xanchor='center'
        ),
        legend=dict(
            font=dict(family='Georgia', size=12),
            yanchor='top',
            y=0.95,
            xanchor='right',
            x=1.2,
            title='Macro Economics Breakdown'
        ),
        margin=dict(l=50, r=150, t=50, b=50),  # Add margins for better layout
        showlegend=True,
        paper_bgcolor='#f0f0f0'  # Light grey background
    )
    
    # Construct paths for HTML saving
    pie_chart_folder = os.path.join(results_folder, f'v{version}_DynamicEconomicBreakdown')
    pie_chart_file = os.path.join(pie_chart_folder, f"Economic_Breakdown_Pie_Chart({version}).html")
    
    # Ensure the directory exists
    os.makedirs(pie_chart_folder, exist_ok=True)
    
    # Save the pie chart as HTML
    pie_chart.write_html(pie_chart_file)
    logging.info(f"Economic breakdown pie chart saved to {pie_chart_file}")

def generate_operational_cost_pie_chart_dynamic(results_folder, version, operational_costs):
    """
    Generate and save a dynamic pie chart showing operational cost breakdown using Plotly.
    
    Args:
        results_folder (str): Path to the folder where results will be saved
        version (str): Version identifier
        operational_costs (dict): Dictionary containing operational cost data with keys:
            - average_feedstock_cost
            - average_labor_cost
            - average_utility_cost
            - average_maintenance_cost
            - average_insurance_cost
    """
    # Define labels and corresponding average operational costs
    labels = [
        'Feedstock Cost',
        'Labor Cost',
        'Utility Cost',
        'Maintenance Cost',
        'Insurance Cost'
    ]
    sizes = [
        operational_costs['average_feedstock_cost'],
        operational_costs['average_labor_cost'],
        operational_costs['average_utility_cost'],
        operational_costs['average_maintenance_cost'],
        operational_costs['average_insurance_cost']
    ]

    # Generate the pie chart for operational costs with custom styling
    pie_chart = px.pie(
        values=sizes,
        names=labels,
        title='Operational Cost Breakdown',
        color_discrete_sequence=px.colors.qualitative.Set3  # Use a qualitative color set
    )

    # Customize layout and styling
    pie_chart.update_layout(
        title=dict(
            text='Operational Cost Breakdown',
            font=dict(family='Georgia', size=18, color='black'),
            x=0.5,  # Center title
            xanchor='center'
        ),
        legend=dict(
            font=dict(family='Georgia', size=12),
            yanchor='top',
            y=0.95,
            xanchor='right',
            x=1.2,
            title='Operational Costs'
        ),
        margin=dict(l=50, r=150, t=50, b=50),  # Add margins for better layout
        showlegend=True,
        paper_bgcolor='#f0f0f0'  # Light grey background
    )

    # Construct paths for HTML saving
    version_dir = os.path.join(results_folder, f'v{version}_DynamicOperationalCost')
    html_file = os.path.join(version_dir, f"Operational_Cost_Breakdown_Pie_Chart({version}).html")
    
    # Ensure the directory exists
    os.makedirs(version_dir, exist_ok=True)
    
    # Save the pie chart as HTML
    pie_chart.write_html(html_file)
    logging.info(f"Operational cost pie chart (dynamic) saved to {html_file}")

def generate_operational_cost_pie_chart_static(results_folder, version, operational_costs, selected_f):
    """
    Generate and save a static pie chart showing operational cost breakdown using Matplotlib.
    
    Args:
        results_folder (str): Path to the folder where results will be saved
        version (str): Version identifier
        operational_costs (dict): Dictionary containing operational cost data
        selected_f (dict): Dictionary of selected F parameters (on/off)
    """
    # Define labels and sizes for the operational cost breakdown
    operational_labels = [
        'Feedstock Cost',
        'Labor Cost',
        'Utility Cost',
        'Maintenance Cost',
        'Insurance Cost'
    ]
    operational_sizes = [
        operational_costs['average_feedstock_cost'],
        operational_costs['average_labor_cost'],
        operational_costs['average_utility_cost'],
        operational_costs['average_maintenance_cost'],
        operational_costs['average_insurance_cost']
    ]

    # Selected fonts
    chosen_title_font = 'Georgia'
    chosen_label_font = 'Georgia'
    chosen_numbers_font = 'Georgia'

    # Filter labels and sizes based on the 'on' or 'off' status in selected_f
    filtered_labels = []
    filtered_sizes = []
    
    for i, (label, size) in enumerate(zip(operational_labels, operational_sizes)):
        if selected_f.get(f'F{i+1}') == 'on' and not np.isnan(size) and size > 0:
            filtered_labels.append(label)
            filtered_sizes.append(size)
    
    # Check if we have valid data to plot
    if not filtered_labels or not filtered_sizes or sum(filtered_sizes) == 0:
        logging.warning(f"No valid operational cost data to plot for version {version}")
        # Create a directory for the plot even if we don't generate one
        static_plot = os.path.join(results_folder, f'{version}_PieStaticPlots')
        os.makedirs(static_plot, exist_ok=True)
        return
    
    # Generate the pie chart
    fig, ax = plt.subplots(figsize=(8, 8), dpi=300)

    def autopct_filter(pct):
        """Show percentage only if >= 3%."""
        return f'{pct:.1f}%' if pct >= 3 else ''

    # Ensure all values are positive and non-NaN
    filtered_sizes = [max(0, size) for size in filtered_sizes]
    
    # Add a small epsilon to prevent division by zero
    if sum(filtered_sizes) == 0:
        logging.warning(f"Sum of filtered sizes is zero for version {version}")
        return
        
    wedges, texts, autotexts = ax.pie(
        filtered_sizes,
        labels=None,  # Labels will be added with arrows
        autopct=autopct_filter,
        startangle=45,
        explode=[0.02] * len(filtered_labels),  # Slight explosion
        wedgeprops={'linewidth': 0.5, 'edgecolor': 'grey'},
        radius=0.7  # Smaller pie radius
    )

    # Set title with chosen font
    ax.set_title('Operational Cost Breakdown', fontsize=14, fontname=chosen_title_font, pad=25)

    # Annotate labels with arrows pointing outward, using chosen fonts
    for i, (wedge, label) in enumerate(zip(wedges, filtered_labels)):
        angle = (wedge.theta2 - wedge.theta1) / 2 + wedge.theta1
        x, y = np.cos(np.deg2rad(angle)), np.sin(np.deg2rad(angle))

        ax.annotate(
            f'{label}\n${filtered_sizes[i]:,.0f}',  # Dollar sign, comma formatting, no decimals
            xy=(x * 0.7, y * 0.7),
            xytext=(x * 1.2, y * 1.2),
            arrowprops=dict(facecolor='black', arrowstyle='->', lw=0.7),
            fontsize=10, ha='center', fontname=chosen_label_font  # Set font for labels
        )

    # Set font for the numbers in the pie chart (autotexts)
    for autotext in autotexts:
        autotext.set_fontname(chosen_numbers_font)
        autotext.set_fontsize(10)

    # Set background color and adjust layout
    ax.set_facecolor('#f7f7f7')
    plt.tight_layout()

    # Save the chart as PNG
    static_plot = os.path.join(results_folder, f'{version}_PieStaticPlots')
    os.makedirs(static_plot, exist_ok=True)

    png_path = os.path.join(static_plot, f"Operational_Cost_Breakdown_Pie_Chart({version}).png")
    plt.savefig(png_path, bbox_inches='tight', dpi=300)
    plt.close()
    
    logging.info(f"Operational cost pie chart (static) saved to {png_path}")
