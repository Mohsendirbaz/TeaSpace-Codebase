import matplotlib.pyplot as plt

# Plot the annual cash flow over time with customization options
def plot_cash_flow(annual_cash_flow, filepath, title="Annual Cash Flow Over Time", xlabel="Year", ylabel="Cash Flow", legend_label="Annual Cash Flow", color="blue"):
    plt.figure(figsize=(10, 5))
    plt.plot(annual_cash_flow, label=legend_label, color=color)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.legend()
    plt.grid(True)
    plt.savefig(filepath)
    plt.close()

# Plot the annual revenue over time with customization options
def plot_revenue(annual_revenue, filepath, title="Annual Revenue Over Time", xlabel="Year", ylabel="Revenue", legend_label="Annual Revenue", color="green"):
    plt.figure(figsize=(10, 5))
    plt.plot(annual_revenue, label=legend_label, color=color)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.legend()
    plt.grid(True)
    plt.savefig(filepath)
    plt.close()

# Plot the annual operating expenses over time with customization options
def plot_operating_expenses(operating_expenses, filepath, title="Annual Operating Expenses Over Time", xlabel="Year", ylabel="Expenses", legend_label="Operating Expenses", color="red"):
    plt.figure(figsize=(10, 5))
    plt.plot(operating_expenses, label=legend_label, color=color)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.legend()
    plt.grid(True)
    plt.savefig(filepath)
    plt.close()

# Plot Loan Repayment
def plot_loan_repayment(loan_repayment_terms, filepath, title="Loan Repayment Over Time", xlabel="Period", ylabel="Repayment Amount", legend_label="Loan Repayment", color="purple"):
    plt.figure(figsize=(10, 5))
    plt.plot(loan_repayment_terms, label=legend_label, color=color)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.legend()
    plt.grid(True)
    plt.savefig(filepath)
    plt.close()
