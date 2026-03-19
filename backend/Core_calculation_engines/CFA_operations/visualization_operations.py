import os
import logging
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from .utility import remove_existing_file

def create_operational_cost_pie_chart(operational_labels, operational_sizes, selected_f, static_plot, version):
    # Example list of fonts to choose from
    available_fonts = ['Arial', 'Verdana', 'Helvetica', 'Times New Roman', 'Courier New', 'Georgia']

    # Selected fonts
    chosen_title_font = 'Georgia'
    chosen_label_font = 'Georgia'
    chosen_numbers_font = 'Georgia'

    # Filter labels and sizes based on the 'on' or 'off' status in selected_f
    filtered_labels = [
        label for i, label in enumerate(operational_labels) if selected_f.get(f'F{i+1}') == 'on'
    ]
    filtered_sizes = [
        size for i, size in enumerate(operational_sizes) if selected_f.get(f'F{i+1}') == 'on'
    ]

    # Generate the pie chart
    fig, ax = plt.subplots(figsize=(8, 8), dpi=300)

    def autopct_filter(pct):
        """Show percentage only if >= 3%."""
        return f'{pct:.1f}%' if pct >= 3 else ''

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
    os.makedirs(static_plot, exist_ok=True)
    png_path = os.path.join(static_plot, f"Operational_Cost_Breakdown_Pie_Chart({version}).png")
    plt.savefig(png_path, bbox_inches='tight', dpi=300)
    plt.close()

def create_operational_revenue_pie_chart(revenue_labels, revenue_sizes, selected_rf, static_plot, version):
    # Selected fonts
    chosen_title_font = 'Georgia'
    chosen_label_font = 'Georgia'
    chosen_numbers_font = 'Georgia'

    # Filter revenue labels and sizes based on the 'on' or 'off' status in selected_rf
    filtered_rev_labels = [
        label for i, label in enumerate(revenue_labels) if selected_rf.get(f'RF{i+1}') == 'on'
    ]
    filtered_rev_sizes = [
        size for i, size in enumerate(revenue_sizes) if selected_rf.get(f'RF{i+1}') == 'on'
    ]

    # Generate the pie chart for revenue (only if there are non-zero values)
    if any(filtered_rev_sizes):
        fig, ax = plt.subplots(figsize=(8, 8), dpi=300)

        def autopct_filter(pct):
            """Show percentage only if >= 3%."""
            return f'{pct:.1f}%' if pct >= 3 else ''

        wedges, texts, autotexts = ax.pie(
            filtered_rev_sizes,
            labels=None,  # Labels will be added with arrows
            autopct=autopct_filter,
            startangle=45,
            explode=[0.02] * len(filtered_rev_labels),  # Slight explosion
            wedgeprops={'linewidth': 0.5, 'edgecolor': 'grey'},
            radius=0.7  # Smaller pie radius
        )

        # Set title with chosen font
        ax.set_title('Operational Revenue Breakdown', fontsize=14, fontname=chosen_title_font, pad=25)

        # Annotate labels with arrows pointing outward, using chosen fonts
        for i, (wedge, label) in enumerate(zip(wedges, filtered_rev_labels)):
            angle = (wedge.theta2 - wedge.theta1) / 2 + wedge.theta1
            x, y = np.cos(np.deg2rad(angle)), np.sin(np.deg2rad(angle))

            ax.annotate(
                f'{label}\n${filtered_rev_sizes[i]:,.0f}',  # Dollar sign, comma formatting, no decimals
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
        png_path = os.path.join(static_plot, f"Operational_Revenue_Breakdown_Pie_Chart({version}).png")
        plt.savefig(png_path, bbox_inches='tight', dpi=300)
        plt.close()

def create_economic_summary(config_received, TOC, total_revenue, total_operating_expenses, 
                           total_depreciation, total_state_taxes, total_federal_taxes, 
                           total_after_tax_cash_flow, total_discounted_cash_flow, 
                           average_selling_price_operational, cumulative_npv, 
                           operational_years, results_folder, version):
    average_annual_revenue = total_revenue / operational_years
    average_annual_operating_expenses = total_operating_expenses / operational_years
    average_annual_depreciation = total_depreciation / operational_years
    average_annual_state_taxes = total_state_taxes / operational_years
    average_annual_federal_taxes = total_federal_taxes / operational_years
    average_annual_discounted_cash_flow = total_discounted_cash_flow / operational_years
    average_annual_after_tax_cash_flow = total_after_tax_cash_flow / operational_years

    economic_summary = pd.DataFrame({
        'Metric': [
            'Internal Rate of Return',
            'Average Selling Price (Project Life Cycle)',
            'Total Overnight Cost (TOC)',
            'Average Annual Revenue',
            'Average Annual Operating Expenses',
            'Average Annual Depreciation',
            'Average Annual State Taxes',
            'Average Annual Federal Taxes',
            'Average Annual After-Tax Cash Flow',
            'Cumulative NPV',
            'Calculation Mode'
        ],
        'Value': [
            f"{config_received.iRRAmount30:.2%}",
            f"${average_selling_price_operational:,.2f}",
            f"${TOC:,.0f}",
            f"${average_annual_revenue:,.0f}",
            f"${average_annual_operating_expenses:,.0f}",
            f"${average_annual_depreciation:,.0f}",
            f"${average_annual_state_taxes:,.0f}",
            f"${average_annual_federal_taxes:,.0f}",
            f"${average_annual_after_tax_cash_flow:,.0f}",
            f"${cumulative_npv:,.0f}",
            f"{os.sys.argv[5] if len(os.sys.argv) > 5 else 'default'}"
        ]
    })

    economic_summary_file = os.path.join(results_folder, f"Economic_Summary({version}).csv")
    remove_existing_file(economic_summary_file)  # Remove if the file already exists
    economic_summary.to_csv(economic_summary_file, index=False)