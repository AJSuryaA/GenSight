import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import os
from sklearn.metrics import confusion_matrix, roc_curve, auc

def save_figure_only(fig, filename):
    """
    Save the figure to the given filename and close the plot without showing it.
    """
    dir_path = os.path.dirname(filename)
    if dir_path and not os.path.exists(dir_path):
        os.makedirs(dir_path)
    fig.savefig(filename)
    plt.close(fig)
    print(f"Saved plot to {filename}")

def pairplot(data: pd.DataFrame, cols: list, filename):
    """Generate seaborn pairplot for specified columns and save to file."""
    fig = sns.pairplot(data[cols])
    fig.savefig(filename)
    plt.close(fig.fig)
    print(f"Saved pairplot to {filename}")

def barplot(data: pd.DataFrame, x_col: str, y_col: str, filename):
    """Generate barplot for specified x and y columns and save to file."""
    fig, ax = plt.subplots(figsize=(8,6))
    sns.barplot(x=data[x_col], y=data[y_col], ax=ax)
    save_figure_only(fig, filename)

def scatterplot(data: pd.DataFrame, x_col: str, y_col: str, filename):
    """Generate scatterplot for specified x and y columns and save to file."""
    fig, ax = plt.subplots(figsize=(8,6))
    sns.scatterplot(x=data[x_col], y=data[y_col], ax=ax)
    save_figure_only(fig, filename)

def histogram(data: pd.DataFrame, col: str, bins: int = 30, filename=None):
    """Generate histogram for a single column and save to file."""
    fig, ax = plt.subplots(figsize=(8,6))
    sns.histplot(data[col], bins=bins, kde=True, ax=ax)
    save_figure_only(fig, filename)

def boxplot(data: pd.DataFrame, x_col: str = None, y_col: str = None, filename=None):
    """Generate boxplot; can be for y_col grouped by x_col if provided, and save to file."""
    fig, ax = plt.subplots(figsize=(8,6))
    if x_col and y_col:
        sns.boxplot(x=data[x_col], y=data[y_col], ax=ax)
    elif y_col:
        sns.boxplot(y=data[y_col], ax=ax)
    else:
        print("boxplot requires at least y_col")
        plt.close(fig)
        return
    save_figure_only(fig, filename)

def heatmap(data: pd.DataFrame, annot: bool = True, filename=None):
    """Generate heatmap of correlations of numeric columns and save to file."""
    fig, ax = plt.subplots(figsize=(10,8))
    corr = data.corr()
    sns.heatmap(corr, annot=annot, cmap='coolwarm', fmt=".2f", ax=ax)
    save_figure_only(fig, filename)

def lineplot(data: pd.DataFrame, x_col: str, y_col: str, filename):
    """Generate lineplot for specified x and y columns and save to file."""
    fig, ax = plt.subplots(figsize=(8,6))
    sns.lineplot(x=data[x_col], y=data[y_col], ax=ax)
    save_figure_only(fig, filename)

def piechart(data: pd.DataFrame, col: str, filename):
    """Generate pie chart from a categorical column with max 10 levels and save to file."""
    s = data[col].astype(str)
    value_counts = s.value_counts()
    if len(value_counts) > 10:
        value_counts = value_counts[:10]
    fig, ax = plt.subplots(figsize=(6,6))
    value_counts.plot.pie(autopct='%1.1f%%', startangle=90, ax=ax)
    plt.title(col)
    ax.set_ylabel('')
    save_figure_only(fig, filename)

def plot_confusion_matrix(y_true, y_pred, labels=None, filename=None):
    """Plot confusion matrix heatmap and save to file."""
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    fig, ax = plt.subplots(figsize=(8,6))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", ax=ax)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title("Confusion Matrix")
    if filename:
        save_figure_only(fig, filename)
    else:
        plt.show()

def plot_roc_curve(y_true, y_score, filename=None):
    """Plot ROC curve and save to file."""
    fpr, tpr, _ = roc_curve(y_true, y_score)
    roc_auc = auc(fpr, tpr)
    fig, ax = plt.subplots(figsize=(8,6))
    ax.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (area = {roc_auc:.2f})')
    ax.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    ax.set_xlabel('False Positive Rate')
    ax.set_ylabel('True Positive Rate')
    ax.set_title('Receiver Operating Characteristic (ROC) Curve')
    ax.legend(loc="lower right")
    if filename:
        save_figure_only(fig, filename)
    else:
        plt.show()

import os

def plot_from_gpt_dict(df, viz_dict, target_col, y_true=None, y_pred=None, y_score=None):
    chart_functions = {
        'pair-plot': pairplot,
        'pairplot': pairplot,
        'bar': barplot,
        'scatter': scatterplot,
        'histogram': histogram,
        'boxplot': boxplot,
        'box': boxplot,
        'heatmap': heatmap,
        'line-chart': lineplot,
        'line': lineplot,
        'pie': piechart,
        # Add other supported charts here
    }

    if not os.path.exists("plots"):
        os.makedirs("plots")

    for key, spec in viz_dict.get('result', {}).items():
        chart_types = spec.get('chart', [])
        cols = spec.get('col', [])

        for chart_type in chart_types:
            ct = chart_type.lower()
            safe_cols = [str(c).replace(" ", "_") for c in cols]
            filename_cols_safe = "_".join(safe_cols) if safe_cols else "no_cols"
            filename = os.path.join("plots", f"{key}_{ct}_{filename_cols_safe}.png")

            # Handle special chart types first which require prediction data
            if ct == 'confusion matrix':
                if y_true is not None and y_pred is not None:
                    plot_confusion_matrix(y_true, y_pred, filename=filename)
                else:
                    print("Confusion matrix plot skipped: y_true/y_pred missing")
                continue  # skip to next chart_type

            if ct == 'roc curve':
                if y_true is not None and y_score is not None:
                    plot_roc_curve(y_true, y_score, filename=filename)
                else:
                    print("ROC curve plot skipped: y_true/y_score missing")
                continue  # skip to next chart_type

            # Handle regular chart types via chart_functions dict
            func = chart_functions.get(ct)
            if func is None:
                print(f"Chart type '{chart_type}' not implemented or pending.")
                continue

            try:
                if ct in ['pair-plot', 'pairplot']:
                    func(df, cols, filename=filename)

                elif ct == 'heatmap':
                    func(df, annot=True, filename=filename)

                elif ct in ['bar', 'scatter', 'line-chart', 'line']:
                    if len(cols) >= 2:
                        func(df, cols[0], cols[1], filename=filename)
                    else:
                        print(f"Not enough columns for {ct} in entry {key}: needs 2 but got {len(cols)}")

                elif ct in ['boxplot', 'box']:
                    if len(cols) == 1:
                        func(df, None, cols[0], filename=filename)
                    elif len(cols) >= 2:
                        func(df, cols[0], cols[1], filename=filename)
                    else:
                        print(f"Not enough columns for boxplot in entry {key}: got {len(cols)}")

                elif ct in ['histogram', 'pie']:
                    if len(cols) >= 1:
                        for col in cols:
                            filename_i = filename.replace(".png", f"_{str(col).replace(' ', '_')}.png")
                            func(df, col, filename=filename_i)
                    else:
                        print(f"{ct} requires at least one column, got {len(cols)} in entry {key}")

                else:
                    print(f"Unhandled chart type: {ct}")

            except Exception as e:
                print(f"Failed to generate chart '{chart_type}' for columns {cols} in entry {key}: {e}")

