import pandas as pd
import numpy as np
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import requests

st.title("Formule 1")
multi = '''Formule 1 (F1) is de hoogste klassen in de autosport formule racen, officieel bekend als FIA One World Championship. De Formule 1 racen worden al gehouden sinds 1950, en is inmiddels uitgegroeid tot éen van de populairste motorsportevenementen ter wereld. De Formule 1 races worden ook wel Grands Prix genoemd, elk jaar worden er een reeks aan Grand Prix wedstrijden gehouden, die mee tellen aan de wereldkampioenschap Formule 1 van dat jaar. Dat race jaar word ook wel een seizoen genoemd. 


De Grands Prix worden over verschillende circuits verspreid over de hele wereld, elk circuit is anders dan de vorige, zo worden er straten races gehouden in Monaco en Singapore, en races op gespecialiseerde circuits zoals in Zandvoort. Hierdoor is elke race weer anders. 
'''
st.markdown(multi)

st.header("Dataset informatie")

multi = '''De data set die we in deze blogpost gebruiken, komt van de **OpenF1 API**, een publieke bron voor Formule 1 data. Deze API geeft toegang tot een breed scala aan gegevens die tijdens F1-races worden verzameld en die we kunnen gebruiken voor analyses en visualisaties.


In deze blogpost wordt de beschikbare Formule 1-data van 2023 verkend om inzicht te geven in de prestaties van coureurs tijdens races. We zullen verschillende aspecten van de race analyseren, zoals:
-   Ronde tijden per coureur.
    - Ronde nummer: Het rondnummer waarin een specifieke tijd is gereden.
    - Ronde tijd: De tijd die een coureur nodig had om een ronde te voltooien.
-	Het vergelijken van verschillende coureurs om te zien wie het beste presteert.
-	Inzicht in hoe bepaalde coureurs beter presteren op specifieke circuits.
-   De snelste ronde bekijken die de coureur op het gekozen circuit heeft afgelegd.
'''
st.markdown(multi)

with st.sidebar:    # Zorgt ervoor dat deze code in een sidebar komt te staan
    @st.cache_data # Zorgt ervoor dat de functie in dit geval maar 1 keer wordt uitgevoerd
    def get_data(): # Haalt alle data op
        # Data wordt opgehaald met de API door deze "https://api.openf1.org/v1/" url in een request.get() te zetten
        # Aan deze url voeg je alleen nog de database die je wilt opvragen toe (zoals: sessions of drivers)
        # Je kan nog specifieker zijn door hier achter nog een ? te zetten en een colom naam met een specificatie. (Bv: year=2023 of session_name=Race)

        response_sessions = requests.get("https://api.openf1.org/v1/sessions?session_name=Race&year=2023")
        print(response_sessions.status_code)
        df_locatie = pd.json_normalize(response_sessions.json())

        response_drivers = requests.get("https://api.openf1.org/v1/drivers")
        print(response_drivers.status_code)
        df_driver = pd.json_normalize(response_drivers.json())

        df_all_laps = pd.DataFrame()
        for session_key in list(df_locatie['session_key']):
            inputString2 = "https://api.openf1.org/v1/laps?session_key={}".format(session_key)
            response2 = requests.get(inputString2)
            print(response2.status_code)
            df_laps = pd.json_normalize(response2.json())
            df_all_laps = pd.concat([df_all_laps, df_laps])

        # Verwijdert de formatie lap, want deze is niet ingevuld en zet de rondes 1 omlaag, zodat de formatie lap niet meer op ronde 1 staat
        formation_lap = df_all_laps[df_all_laps["lap_number"] == 1].index
        df_all_laps.drop(formation_lap, inplace=True)
        df_all_laps["lap_number"] = df_all_laps["lap_number"] - 1
        return df_all_laps, df_locatie, df_driver

    df_laps, df_locatie, df_driver = get_data() # Haal de data op

    # Het verkrijgen van de session_key van de ingevulde racelocatie
    locatie = st.selectbox(
        "Van welke race zou je de data willen bekijken?",
        (df_locatie["location"]), key="1"
    )
    sessionKey = df_locatie.loc[(df_locatie["location"]==locatie), "session_key"].values[0]

    # Het verkrijgen van het coureurs nummer van de ingevulde coureur
    coureur = st.selectbox(
        "Van welke coureur zou je de data willen bekijken?",
        (df_driver.loc[(df_driver["session_key"]==sessionKey), "broadcast_name"].unique()), key="2"
    )
    driver = df_driver.loc[df_driver["broadcast_name"]==coureur, "driver_number"].values[0]

    # Filter de laps voor de geselecteerde race en coureur
    df_filtered_driver = df_laps[(df_laps["session_key"] == sessionKey) & (df_laps["driver_number"] == driver)]

    # Slider voor het aantal laps
    lap_range = st.slider(
        "Selecteer het aantal rondes om weer te geven",
        min_value=int(df_filtered_driver["lap_number"].min()), 
        max_value=int(df_filtered_driver['lap_number'].max()),
        value=(int(df_filtered_driver["lap_number"].min()), int(df_filtered_driver['lap_number'].max()))
    )

    # Filter de dataframe op basis van de geselecteerde laps
    df_filtered_driver_laps = df_filtered_driver[
        (df_filtered_driver["lap_number"] >= lap_range[0]) & (df_filtered_driver["lap_number"] <= lap_range[1])
    ]

    # Checkbox voor inzoomen
    zoomin = st.checkbox("Inzoomen op de grafiek")

    # Minimum lap tijd bepalen
    min_lap_duration = df_filtered_driver_laps['lap_duration'].min()

    # Grafiek logica
    if zoomin:
        # Stel een symmetrisch bereik rondom de minimumwaarde in, bijvoorbeeld ±4 seconden
        zoom_range = 4  # Dit kan je aanpassen als je een ander bereik wilt
        y_min = min_lap_duration - zoom_range
        y_max = min_lap_duration + zoom_range

        # Plot met ingezoomde y-limieten rond de minimum lap tijd
        fig = px.line(df_filtered_driver_laps, x="lap_number", y="lap_duration", 
                    title="Ingezoomde Ronde tijden")
        fig.update_layout(yaxis_range=[y_min, y_max], yaxis_title="Ronde tijd (s)", xaxis_title="Ronde")
    else:
        # Normale plot zonder zoom
        fig = px.line(df_filtered_driver_laps, x="lap_number", y="lap_duration", 
                    title="Originele Ronde tijden")
        fig.update_layout(yaxis_title="Ronde tijd (s)", xaxis_title="Ronde")


    agree = st.checkbox("Wil je de data vergelijken met een tweede coureur?")
    if agree:
        # Het verkrijgen van het coureurs nummer van de 2e ingevulde coureur
        coureur2 = st.selectbox(
            "Van welke coureur zou je de data willen bekijken?",
            (df_driver.loc[(df_driver["session_key"]==sessionKey), "broadcast_name"].unique()), key="3"
        )
        driver2 = df_driver.loc[df_driver["broadcast_name"]==coureur2, "driver_number"].values[0]

        # Voeg de nieuwe lijn toe
        fig.add_trace(go.Scatter(x=df_laps.loc[(df_laps["session_key"]==sessionKey) & (df_laps["driver_number"]==driver2), "lap_number"], y=df_laps.loc[(df_laps["session_key"]==sessionKey) & (df_laps["driver_number"]==driver2), "lap_duration"], mode="lines", line=go.scatter.Line(color="red"), showlegend=True, name=coureur2))

        # Bereken de snelste ronde
        snelste_ronde = df_filtered_driver_laps.loc[df_filtered_driver_laps["lap_duration"].idxmin(), "lap_number"]
        st.markdown(f"**Coureur**: {coureur} | **Locatie**: {locatie} | **Snelste Ronde** : {int(snelste_ronde)}")

        # Filter de laps voor de geselecteerde race en coureur
        df_filtered_driver2 = df_laps[(df_laps["session_key"] == sessionKey) & (df_laps["driver_number"] == driver2)]

        # Filter de dataframe op basis van de geselecteerde laps
        df_filtered_driver_laps2 = df_filtered_driver2[(df_filtered_driver2["lap_number"] >= lap_range[0]) & (df_filtered_driver2["lap_number"] <= lap_range[1])]

        snelste_ronde2 = df_filtered_driver_laps2.loc[df_filtered_driver_laps2["lap_duration"].idxmin(), "lap_number"]
        st.markdown(f"**Coureur**: {coureur2} | **Locatie**: {locatie} | **Snelste Ronde** : {int(snelste_ronde2)}")
        
    else:
        # Bereken de snelste ronde voor als er maar 1 coureur is geselecteerd
        snelste_ronde = df_filtered_driver_laps.loc[df_filtered_driver_laps["lap_duration"].idxmin(), "lap_number"]
        st.markdown(f"**Coureur**: {coureur} | **Locatie**: {locatie} | **Snelste Ronde** : {int(snelste_ronde)}")

# Grafiek tonen
st.plotly_chart(fig, use_container_width=True)


st.subheader("Uitleg pieken")
multi = '''In de grafieken zijn verschillende pieken te zien, deze pieken betekenen dat de coureur bijvoorbeeld een pitstop heeft moeten maken tijdens de Grand Prix, het zou ook kunnen betekenen dat er een safetycar in gezet is. Deze pieken laten zien dat de ronde tijden van de coureur hoger zijn door omstandigheden tijdens het racen, door bijvoorbeeld een incident.''' 

st.markdown(multi)

st.subheader("Inzichten rondetijden")
multi = '''De analyse van de rondetijden van verschillende coureurs tijdens de races op de circuits laat duidelijk zien dat de prestaties kunnen verschillen op verschillende circuits. Uit de data blijkt dat, hoewel de meeste coureurs een stabiel tempo weten aan te houden, er duidelijke pieken en dalen in rondetijden zijn te zien die mogelijk het gevolg zijn van incidenten op de baan, pitstops of Safety Car-situaties.


Het vergelijken van de snelste rondes tussen coureurs geeft inzichten in hoe verschillende strategieën hebben bijgedragen aan hun eindresultaat. Sommige coureurs weten bijvoorbeeld hun snelste rondes te rijden in het begin  van de race, terwijl anderen in de latere ronden versnellen.


Door deze data-analyse kunnen we inzichten verkrijgen hoe verschillende coureurs hun race aanpakken, dit soort data kunnen de race strategieën van de teams verbeteren voor toekomstige races.'''
st.markdown(multi)