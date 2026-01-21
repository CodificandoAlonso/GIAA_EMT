import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt


def project_occupation_in_daytime(data_to_project, highlight_trip_id=None):
    data_to_project = data_to_project.copy()
    data_to_project["EventTime"] = pd.to_datetime(
        data_to_project["EventTime"],
        format="%H:%M:%S.%f"
    )

    data_to_project = data_to_project.sort_values("EventTime")

    plt.figure(figsize=(16, 6))

    # Plotear línea completa conectada
    plt.plot(data_to_project["EventTime"], data_to_project["Occupation"],
             marker='o', color='steelblue', alpha=0.7)

    if highlight_trip_id:
        # Superponer puntos del TripId destacado en otro color
        highlight_data = data_to_project[data_to_project["TripId"] == highlight_trip_id]
        plt.scatter(highlight_data["EventTime"], highlight_data["Occupation"],
                    color='red', s=100, zorder=5, label=f'Trip: {highlight_trip_id}')
        plt.legend()

    ax = plt.gca()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))

    ax.set_xlim([
        pd.to_datetime("00:00:00", format="%H:%M:%S"),
        pd.to_datetime("23:59:59", format="%H:%M:%S")
    ])

    plt.xlabel('Hora del día')
    plt.ylabel('Occupation')
    plt.title('Evolución de Occupation durante el día')
    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()


def histogram(data_hist, variable):
    plt.hist(data_hist[variable], bins= 15)
    plt.xlabel(variable)
    plt.ylabel('Count')
    plt.title(f"Histograma de {variable}")
    plt.xticks(rotation=29)
    plt.grid(True, alpha=0.3)
    plt.show()