import streamlit as st
import pandas as pd
import math
import matplotlib.pyplot as plt
from jsonbin import load_key, save_key
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth

# Logo/Name setzen für Tab in Google, so dass nicht "local" steht
st.set_page_config(
    page_title="Covid-19 Datenbank"
)

# -------- load secrets for jsonbin.io --------
jsonbin_secrets = st.secrets["jsonbin"]
api_key = jsonbin_secrets["api_key"]
bin_id = jsonbin_secrets["bin_id"]

# -------- user login --------
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
)

fullname, authentication_status, username = authenticator.login('Login', 'main')

if authentication_status == True:
    # login successful
    authenticator.logout('Logout', 'main')  # show logout button
elif authentication_status == False:
    st.error('Username/password is incorrect')
    st.stop()
elif authentication_status == None:
    st.warning('Please enter your username and password')
    st.stop()

## Helper Functions
def binomial_probability(k, n, p):
    """
    Berechnet die Wahrscheinlichkeit einer bestimmten Anzahl von Erfolgen in einer bestimmten Anzahl von Versuchen gemäß der Binomialverteilung.
    
    Parameter:
    k (int): Anzahl der Erfolge
    n (int): Anzahl der Versuche
    p (float): Erfolgswahrscheinlichkeit
    
    Rückgabewert:
    float: Wahrscheinlichkeit
    
    """
    # Berechne den Binomialkoeffizienten
    coefficient = math.comb(n, k)
    
    # Berechne die Wahrscheinlichkeit
    probability = coefficient * (p ** k) * ((1 - p) ** (n - k))
    
    return probability


### App
# Kolone erstellen, um den Titel links zu setzen und nicht in der Mitte
col1, col2, col3 = st.columns([1, 2, 1])
# Markdown-Zeichenkette mit HTML-Stilen anzeigen
st.markdown("<h1 style='color: green; font-weight: bold;'>Die Covid-19 Datenbank für die Dokumentierung von diagnostischen PCR Untersuchungen ZHAW</h1>", unsafe_allow_html=True)
st.subheader('Die Covid-19 Datenbank unterstützt Labor und Covid Testcenter während der Pandemie, hier können alle Untersuchungsdaten von positiven und negativen Tests digital gesammelt werden.')
# Bild in der 3. Kolone setzen
col3.image('https://thumbs.dreamstime.com/b/biohazard-der-rote-poster-des-dreiecks-covid-warnt-biohazardvorsichtzeichen-kein-eintrag-pr%C3%A4vention-sicherheitszeichen-eps-vektor-177789902.jpg')
# Caption erstellen
st.caption("Erstellt von der BMLD Studentin: Michèle Pfister")

# load data from jsonbin.io
data = load_key(api_key, bin_id, username)

if data is None:
    data = []  # Empty list if no data is


# Create DataFrame
df = pd.DataFrame(data)

### App
# Streamlit Sidebar-Eingabefelder erstellen
with st.sidebar:
    st.title("COVID-19-Testergebnisse")
    case_number = st.number_input("Fallnummer", min_value=0, step=1)
    name = st.text_input("Name")
    age = st.number_input("Alter", min_value=0, max_value=120, step=1)
    gender = st.selectbox("Geschlecht", ["Männlich", "Weiblich", "Divers"])
    test_result = st.selectbox("Testergebnis", ["Negativ", "Positiv"])
    test_date = st.text_input("Testdatum")
    save_button = st.button("Speichern")
    search_term = st.text_input("Patienten suchen")
    search_button = st.button("Suchen")

# Überprüfen und Anpassen der Spalten im DataFrame
required_columns = ["Fallnummer", "Name", "Alter", "Geschlecht", "Testergebnis", "Testdatum"]
existing_columns = list(df.columns)

for column in required_columns:
    if column not in existing_columns:
        df[column] = ""

# Filtern der Daten basierend auf dem Suchbegriff
if search_button:
    search_result = df[df["Name"].str.contains(search_term, case=False)]
else:
    search_result = pd.DataFrame()

# Daten speichern, wenn "Speichern"-Button geklickt wird
if save_button:
    new_entry = {
        "Fallnummer": case_number,
        "Name": name,
        "Alter": age,
        "Geschlecht": gender,
        "Testergebnis": test_result,
        "Testdatum": test_date
    }
    df = df.append(new_entry, ignore_index=True)
    # Daten in jsonbin.io speichern
    save_key(api_key, bin_id, username, df.to_dict(orient="records"))


# Binomialverteilung berechnen
total_tests = len(df)
if "Testergebnis" in df.columns:
    positive_tests = len(df[df["Testergebnis"] == "Positiv"])
else:
    positive_tests = 0
probability_positive = binomial_probability(positive_tests, total_tests, 0.2)

# Ergebnistabelle anzeigen, nur wenn Daten vorhanden sind
if not df.empty:
    st.header("Testergebnisse")
    st.dataframe(df)
else:
    st.info("Es liegen keine Daten vor.")

# Suchergebnis anzeigen
if not search_result.empty:
    st.header("Suchergebnis")
    st.dataframe(search_result)
elif search_button:
    st.info("Es wurden keine Ergebnisse gefunden.")

# Statistik anzeigen
st.header("Statistik")
st.subheader("Binomialverteilung der Testergebnisse")
st.write(f"Anzahl der Tests insgesamt: {total_tests}")
st.write(f"Anzahl der positiven Tests: {positive_tests}")
st.write(f"Wahrscheinlichkeit eines positiven Tests: {probability_positive:.2%}")


# Plot erstellen
st.header("Plot der Testergebnisse")
fig, ax = plt.subplots(figsize=(8, 6))
df["Testergebnis"].value_counts().plot(kind="bar", ax=ax)
ax.set_xlabel("Testergebnis")
ax.set_ylabel("Anzahl")
ax.set_title("Verteilung der Testergebnisse")
st.pyplot(fig)

# Daten löschen
with st.expander("Daten löschen"):
    delete_option = st.radio("Löschoption auswählen", ["Alle Daten löschen", "Daten einer Person löschen", "Daten an einem Datum löschen"])

    if delete_option == "Alle Daten löschen":
        confirm_delete = st.button("Bestätigen")

        if confirm_delete:
            df = pd.DataFrame(columns=required_columns)
            # Daten in jsonbin.io speichern
            save_key(api_key, bin_id, username, df.to_dict(orient="records"))
            st.success("Alle Daten wurden gelöscht.")

    elif delete_option == "Daten einer Person löschen":
        person_name = st.text_input("Name der Person")
        confirm_delete = st.button("Bestätigen")

        if confirm_delete:
            df = df[df["Name"] != person_name]
            # Daten in jsonbin.io speichern
            save_key(api_key, bin_id, username, df.to_dict(orient="records"))
            st.success(f"Daten von {person_name} wurden gelöscht.")

    elif delete_option == "Daten an einem Datum löschen":
        date = st.text_input("Datum (YYYY-MM-DD)")
        confirm_delete = st.button("Bestätigen")

        if confirm_delete:
            df = df[df["Testdatum"] != date]
            # Daten in jsonbin.io speichern
            save_key(api_key, bin_id, username, df.to_dict(orient="records"))
            st.success(f"Daten vom {date} wurden gelöscht.")


