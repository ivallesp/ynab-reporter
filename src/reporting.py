import calendar
import locale
from datetime import datetime

import matplotlib.pyplot as plt
import pandas as pd

from src.wrangling import calculate_daily_balances, get_ynab_dataset

MONTHS = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]


def calculate_financial_snapshot(year, month):
    eom_day = calendar.monthrange(year, month)[1]
    eom_date = datetime(year, month, eom_day)
    # Load data and calculate daily balances
    df_ynab = get_ynab_dataset()
    df = calculate_daily_balances(df=df_ynab)
    # Get the end of month balances
    df = df[lambda d: d.date == eom_date]
    # Aggregate at account level
    df = df.groupby(["account_name"]).amount.sum()
    # Sort accounts by decreasing balabce
    df = df.sort_values(ascending=False).reset_index()
    # Remove accounts with 0€
    df = df[lambda d: d.amount != 0]
    # Add total
    total = {"account_name": ["Total"], "amount": [df.amount.sum()]}
    df_total = pd.DataFrame(total)
    df = pd.concat([df, df_total], axis=0)
    # Add fancy column names
    df.columns = ["Account", "Amount"]
    # Transpose
    df = df.set_index("Account").transpose()
    return df


def generate_evolution_plot():
    df_ynab = get_ynab_dataset()
    df = calculate_daily_balances(df=df_ynab)
    # Aggregate at account level
    df = df.groupby(["date", "account_name"]).amount.sum().reset_index()
    # Pivot the account dimension
    df = pd.pivot_table(df, index="date", columns="account_name", aggfunc="sum")
    # Drop the accounts that have always had 0 balance
    for col in df.columns:
        if df[col].max() == 0:
            df = df.drop(col, axis=1)
    # Calculate the histories for every account
    histories = list(zip(*df.values.clip(0, None).tolist()))
    fig = plt.figure(figsize=(10, 2.5))
    ax = plt.gca()
    ax.stackplot(df.index.tolist(), *histories, labels=df["amount"].columns)
    ax.legend(loc="upper left")
    fig.tight_layout()
    return fig, ax


def generate_latex_report(year, month):
    with open("assets/template.tex", "r") as f:
        template = f.read()
    df_financial_snapshot = calculate_financial_snapshot(year=year, month=month)

    locale.setlocale(locale.LC_ALL, "en_us.utf-8")
    float_format = lambda x: locale.format("%.2f", x, grouping=True)
    financial_report = df_financial_snapshot.to_latex(
        index=False, float_format=float_format
    )

    title = f"Financial report – {MONTHS[month-1]} {year}"
    template = template.format(financial_snapshot=financial_report, title=title)

    # + monthly inflows and outflows, with initial and final balance and savings
    # + biggest transactions

    # Change colors
    # Add grid
    # Set xlim
    fig, ax = generate_evolution_plot()
    fig.savefig("assets/evolution.eps")

    with open("assets/report.tex", "w") as f:
        f.write(template)
