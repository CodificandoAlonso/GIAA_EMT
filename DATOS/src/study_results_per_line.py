import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from ast import literal_eval
import os

# Configuration
plt.style.use('seaborn-v0_8-whitegrid')
TIMESLOTS = [5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23]


def load_and_prepare_data(filepath):

    dataframe = pd.read_csv(filepath)

    # Convert outlier columns from string representation to actual lists
    for t in TIMESLOTS:
        col = f"outliers_{t}"
        if col in dataframe.columns:
            dataframe[col] = dataframe[col].apply(lambda x: literal_eval(x) if isinstance(x, str) else x)
    return dataframe


def count_outliers(outlier_list):
    """Count number of outliers in a list"""
    if isinstance(outlier_list, list):
        return len(outlier_list)
    return 0


def calc_normality_pct_by_timeslot(dataframe):
    """Calculate % True/False for IsNormal per timeslot"""
    results = []
    for t in TIMESLOTS:
        col = f"IsNormal_{t}"
        if col in dataframe.columns:
            total = dataframe[col].notna().sum()
            true_count = ((dataframe[col] == True) | (dataframe[col] == "True")).sum()
            false_count = ((dataframe[col] == False) | (dataframe[col] == "False") | (dataframe[col] == "NO DATA")).sum()
            results.append({
                'Timeslot': t,
                'True_pct': (true_count / total * 100) if total > 0 else 0,
                'False_pct': (false_count / total * 100) if total > 0 else 0,
                'Total': total
            })
    return pd.DataFrame(results)


def calc_avg_outliers_by_timeslot(dataframe):
    """Calculate average number of outliers per timeslot"""
    results = []
    for t in TIMESLOTS:
        col = f"outliers_{t}"
        if col in dataframe.columns:
            outlier_counts = dataframe[col].apply(count_outliers)
            results.append({
                'Timeslot': t,
                'Avg_outliers': outlier_counts.mean(),
                'Std_outliers': outlier_counts.std(),
                'Total_outliers': outlier_counts.sum()
            })
    return pd.DataFrame(results)


def calc_normality_pct_by_stop(dataframe):
    """Calculate % True/False for IsNormal per stop"""
    results = []
    stops = dataframe['Stop'].unique()

    for stop in stops:
        stop_data = dataframe[dataframe['Stop'] == stop]
        true_count = 0
        false_count = 0
        total = 0

        for t in TIMESLOTS:
            col = f"IsNormal_{t}"
            if col in stop_data.columns:
                total += stop_data[col].notna().sum()
                true_count += ((stop_data[col] == True) | (stop_data[col] == "True")).sum()
                false_count += ((stop_data[col] == False)| (stop_data[col] == "False") | (stop_data[col] == "NO DATA")).sum()

        results.append({
            'Stop': stop,
            'True_pct': (true_count / total * 100) if total > 0 else 0,
            'False_pct': (false_count / total * 100) if total > 0 else 0,
            'Total_checks': total
        })

    return pd.DataFrame(results)


def calc_avg_outliers_by_stop(dataframe):
    """Calculate average number of outliers per stop"""
    results = []
    stops = dataframe['Stop'].unique()

    for stop in stops:
        stop_data = dataframe[dataframe['Stop'] == stop]
        total_outliers = 0
        count = 0

        for t in TIMESLOTS:
            col = f"outliers_{t}"
            if col in stop_data.columns:
                outlier_counts = stop_data[col].apply(count_outliers)
                total_outliers += outlier_counts.sum()
                count += len(outlier_counts)

        results.append({
            'Stop': stop,
            'Avg_outliers': total_outliers / count if count > 0 else 0,
            'Total_outliers': total_outliers
        })

    return pd.DataFrame(results)



def plot_normality_by_timeslot(dataframe_kpi, title_suffix=""):
    """Bar plot of normality % by timeslot"""
    fig, ax = plt.subplots(figsize=(14, 6))

    x = np.arange(len(dataframe_kpi))
    width = 0.35

    bars1 = ax.bar(x - width/2, dataframe_kpi['True_pct'], width, label='Normal (True)', color='#2ecc71')
    bars2 = ax.bar(x + width/2, dataframe_kpi['False_pct'], width, label='No Normal (False)', color='#e74c3c')

    ax.set_xlabel('Franja Horaria', fontsize=12)
    ax.set_ylabel('Porcentaje (%)', fontsize=12)
    ax.set_title(f'Porcentaje de Normalidad por Franja Horaria {title_suffix}', fontsize=14)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{t}:00" for t in dataframe_kpi['Timeslot']], rotation=45)
    ax.legend()
    ax.set_ylim(0, 100)

    # Add value labels on bars
    for bar in bars1:
        height = bar.get_height()
        ax.annotate(f'{height:.1f}%', xy=(bar.get_x() + bar.get_width()/2, height),
                    xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=8)

    plt.tight_layout()
    return fig


def plot_avg_outliers_by_timeslot(dataframe_kpi, title_suffix=""):
    """Bar plot of average outliers by timeslot"""
    fig, ax = plt.subplots(figsize=(14, 6))

    colors = plt.cm.YlOrRd(dataframe_kpi['Avg_outliers'] / dataframe_kpi['Avg_outliers'].max())

    bars = ax.bar(dataframe_kpi['Timeslot'].astype(str), dataframe_kpi['Avg_outliers'], color=colors, edgecolor='black')

    if 'Std_outliers' in dataframe_kpi.columns:
        ax.errorbar(dataframe_kpi['Timeslot'].astype(str), dataframe_kpi['Avg_outliers'],
                    yerr=dataframe_kpi['Std_outliers'], fmt='none', color='black', capsize=3)

    ax.set_xlabel('Franja Horaria', fontsize=12)
    ax.set_ylabel('Nº Medio de Outliers', fontsize=12)
    ax.set_title(f'Número Medio de Outliers por Franja Horaria {title_suffix}', fontsize=14)
    ax.set_xticklabels([f"{t}:00" for t in dataframe_kpi['Timeslot']], rotation=45)

    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'{height:.2f}', xy=(bar.get_x() + bar.get_width()/2, height),
                    xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=9)

    plt.tight_layout()
    return fig


def plot_normality_by_stop(dataframe_kpi, title_suffix=""):
    """Horizontal bar plot of normality % by stop"""
    fig, ax = plt.subplots(figsize=(10, max(8, len(dataframe_kpi) * 0.4)))

    dataframe_sorted = dataframe_kpi.sort_values('True_pct', ascending=True)

    y = np.arange(len(dataframe_sorted))
    height = 0.35

    bars1 = ax.barh(y - height/2, dataframe_sorted['True_pct'], height, label='Normal (True)', color='#2ecc71')
    bars2 = ax.barh(y + height/2, dataframe_sorted['False_pct'], height, label='No Normal (False)', color='#e74c3c')

    ax.set_ylabel('Parada', fontsize=12)
    ax.set_xlabel('Porcentaje (%)', fontsize=12)
    ax.set_title(f'Porcentaje de Normalidad por Parada {title_suffix}', fontsize=14)
    ax.set_yticks(y)
    ax.set_yticklabels(dataframe_sorted['Stop'])
    ax.legend(loc='lower right')
    ax.set_xlim(0, 100)

    plt.tight_layout()
    return fig


def plot_avg_outliers_by_stop(dataframe_kpi, title_suffix=""):
    """Horizontal bar plot of average outliers by stop"""
    fig, ax = plt.subplots(figsize=(10, max(8, len(dataframe_kpi) * 0.4)))

    dataframe_sorted = dataframe_kpi.sort_values('Avg_outliers', ascending=True)

    colors = plt.cm.YlOrRd(dataframe_sorted['Avg_outliers'] / dataframe_sorted['Avg_outliers'].max())

    bars = ax.barh(dataframe_sorted['Stop'].astype(str), dataframe_sorted['Avg_outliers'], color=colors, edgecolor='black')

    ax.set_ylabel('Parada', fontsize=12)
    ax.set_xlabel('Nº Medio de Outliers', fontsize=12)
    ax.set_title(f'Número Medio de Outliers por Parada {title_suffix}', fontsize=14)

    plt.tight_layout()
    return fig


def plot_heatmap_normality(dataframe, title_suffix=""):
    """Heatmap of normality by stop and timeslot"""
    stops = dataframe['Stop'].unique()

    # Create matrix
    matrix = []
    for stop in stops:
        stop_data = dataframe[dataframe['Stop'] == stop]
        row = []
        for t in TIMESLOTS:
            col = f"IsNormal_{t}"
            if col in stop_data.columns:
                true_rate = ((stop_data[col] == True) | (stop_data[col] == "True")).mean() * 100
                row.append(true_rate)
            else:
                row.append(np.nan)
        matrix.append(row)

    matrix_dataframe = pd.DataFrame(matrix, index=stops, columns=[f"{t}:00" for t in TIMESLOTS])

    fig, ax = plt.subplots(figsize=(16, max(8, len(stops) * 0.5)))
    sns.heatmap(matrix_dataframe, annot=True, fmt='.0f', cmap='RdYlGn', vmin=0, vmax=100,
                ax=ax, cbar_kws={'label': '% Normal'})
    ax.set_title(f'Heatmap de Normalidad por Parada y Franja Horaria {title_suffix}', fontsize=14)
    ax.set_xlabel('Franja Horaria', fontsize=12)
    ax.set_ylabel('Parada', fontsize=12)

    plt.tight_layout()
    return fig


def plot_heatmap_outliers(dataframe, title_suffix=""):
    """Heatmap of outliers by stop and timeslot"""
    stops = dataframe['Stop'].unique()

    matrix = []
    for stop in stops:
        stop_data = dataframe[dataframe['Stop'] == stop]
        row = []
        for t in TIMESLOTS:
            col = f"outliers_{t}"
            if col in stop_data.columns:
                avg_outliers = stop_data[col].apply(count_outliers).mean()
                row.append(avg_outliers)
            else:
                row.append(np.nan)
        matrix.append(row)

    matrix_dataframe = pd.DataFrame(matrix, index=stops, columns=[f"{t}:00" for t in TIMESLOTS])

    fig, ax = plt.subplots(figsize=(16, max(8, len(stops) * 0.5)))
    sns.heatmap(matrix_dataframe, annot=True, fmt='.1f', cmap='YlOrRd', ax=ax,
                cbar_kws={'label': 'Avg Outliers'})
    ax.set_title(f'Heatmap de Outliers Medios por Parada y Franja Horaria {title_suffix}', fontsize=14)
    ax.set_xlabel('Franja Horaria', fontsize=12)
    ax.set_ylabel('Parada', fontsize=12)

    plt.tight_layout()
    return fig


# =============================================================================
# MAIN ANALYSIS FUNCTION
# =============================================================================

def analyze_normality_results(filepath, output_dir="./"):
    """
    Main function to analyze normality results and generate all visualizations.
    Parameters:
    -----------
    filepath : str
        Path to the CSV file with normality results
    output_dir : str
        Directory to save the generated plots
    """

    # Load data
    dataframe = load_and_prepare_data(filepath)


    # Separate ALL vs individual days
    dataframe_all = dataframe[dataframe['day'] == 'ALL']
    dataframe_individual = dataframe[dataframe['day'] != 'ALL']



    #ALL
    norm_timeslot_all = calc_normality_pct_by_timeslot(dataframe_all)
    outliers_timeslot_all = calc_avg_outliers_by_timeslot(dataframe_all)
    norm_stop_all = calc_normality_pct_by_stop(dataframe_all)
    outliers_stop_all = calc_avg_outliers_by_stop(dataframe_all)


    # Generate plots for ALL
    fig1 = plot_normality_by_timeslot(norm_timeslot_all, "(ALL)")
    fig1.savefig(f"{output_dir}/normality_timeslot_ALL.png", dpi=150)

    fig2 = plot_avg_outliers_by_timeslot(outliers_timeslot_all, "(ALL)")
    fig2.savefig(f"{output_dir}/outliers_timeslot_ALL.png", dpi=150)

    fig3 = plot_normality_by_stop(norm_stop_all, "(ALL)")
    fig3.savefig(f"{output_dir}/normality_stop_ALL.png", dpi=150)

    fig4 = plot_heatmap_normality(dataframe_all, "(ALL)")
    fig4.savefig(f"{output_dir}/heatmap_normality_ALL.png", dpi=150)

    fig5 = plot_heatmap_outliers(dataframe_all, "(ALL)")
    fig5.savefig(f"{output_dir}/heatmap_outliers_ALL.png", dpi=150)

    fig6 = plot_avg_outliers_by_stop(outliers_stop_all, "(ALL)")
    fig6.savefig(f"{output_dir}/outliers_stop_ALL.png", dpi=150)

    #SEPARATE DAYS
    norm_timeslot_ind = calc_normality_pct_by_timeslot(dataframe_individual)
    outliers_timeslot_ind = calc_avg_outliers_by_timeslot(dataframe_individual)
    norm_stop_ind = calc_normality_pct_by_stop(dataframe_individual)
    outliers_stop_ind = calc_avg_outliers_by_stop(dataframe_individual)


    # Generate plots for individual
    fig7 = plot_normality_by_timeslot(norm_timeslot_ind, "(L,M,X,J,V)")
    fig7.savefig(f"{output_dir}/normality_timeslot_individual.png", dpi=150)

    fig8 = plot_avg_outliers_by_timeslot(outliers_timeslot_ind, "(L,M,X,J,V)")
    fig8.savefig(f"{output_dir}/outliers_timeslot_individual.png", dpi=150)

    fig9 = plot_normality_by_stop(norm_stop_ind, "(L,M,X,J,V)")
    fig9.savefig(f"{output_dir}/normality_stop_individual.png", dpi=150)

    fig10 = plot_avg_outliers_by_stop(outliers_stop_ind, "(L,M,X,J,V)")
    fig10.savefig(f"{output_dir}/outliers_stop_individual.png", dpi=150)

    fig11 = plot_heatmap_normality(dataframe_individual, "(L,M,X,J,V)")
    fig11.savefig(f"{output_dir}/heatmap_normality_individual.png", dpi=150)

    fig12 = plot_heatmap_outliers(dataframe_individual, "(L,M,X,J,V)")
    fig12.savefig(f"{output_dir}/heatmap_outliers_individual.png", dpi=150)

    # Comparative plot: ALL vs Individual
    fig13, axes = plt.subplots(1, 2, figsize=(16, 6))


    # Normality comparison
    x = np.arange(len(TIMESLOTS))
    width = 0.35
    axes[0].bar(x - width/2, norm_timeslot_all['True_pct'], width, label='ALL', color='#3498db')
    axes[0].bar(x + width/2, norm_timeslot_ind['True_pct'], width, label='Individual', color='#e67e22')
    axes[0].set_xlabel('Franja Horaria')
    axes[0].set_ylabel('% Normal (True)')
    axes[0].set_title('Comparación % Normalidad: ALL vs Individual')
    axes[0].set_xticks(x)
    axes[0].set_xticklabels([f"{t}:00" for t in TIMESLOTS], rotation=45)
    axes[0].legend()
    axes[0].set_ylim(0, 100)

    # Outliers comparison
    axes[1].bar(x - width/2, outliers_timeslot_all['Avg_outliers'], width, label='ALL', color='#3498db')
    axes[1].bar(x + width/2, outliers_timeslot_ind['Avg_outliers'], width, label='Individual', color='#e67e22')
    axes[1].set_xlabel('Franja Horaria')
    axes[1].set_ylabel('Nº Medio Outliers')
    axes[1].set_title('Comparación Outliers: ALL vs Individual')
    axes[1].set_xticks(x)
    axes[1].set_xticklabels([f"{t}:00" for t in TIMESLOTS], rotation=45)
    axes[1].legend()

    plt.tight_layout()
    fig13.savefig(f"{output_dir}/comparison_ALL_vs_individual.png", dpi=150)

    plt.close('all')



    return {
        'norm_timeslot_all': norm_timeslot_all,
        'outliers_timeslot_all': outliers_timeslot_all,
        'norm_stop_all': norm_stop_all,
        'norm_timeslot_ind': norm_timeslot_ind,
        'outliers_timeslot_ind': outliers_timeslot_ind,
        'norm_stop_ind': norm_stop_ind,
        'outliers_stop_ind': outliers_stop_ind
    }







