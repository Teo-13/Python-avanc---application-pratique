import { useState } from "react";

import "./App.css";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:5001";

const formatTemperature = (value) => {
  if (value === null || value === undefined) {
    return "Non disponible";
  }

  return `${new Intl.NumberFormat("fr-FR", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  }).format(value)} °C`;
};

const MONTHS = [
  { value: "01", label: "Janvier" },
  { value: "02", label: "Fevrier" },
  { value: "03", label: "Mars" },
  { value: "04", label: "Avril" },
  { value: "05", label: "Mai" },
  { value: "06", label: "Juin" },
  { value: "07", label: "Juillet" },
  { value: "08", label: "Aout" },
  { value: "09", label: "Septembre" },
  { value: "10", label: "Octobre" },
  { value: "11", label: "Novembre" },
  { value: "12", label: "Decembre" },
];

const DAYS = Array.from({ length: 31 }, (_, index) => {
  const day = String(index + 1).padStart(2, "0");
  return { value: day, label: String(index + 1) };
});

function creerCleJourMois(jour, mois) {
  if (!jour || !mois) {
    return "";
  }

  return `${mois}-${jour}`;
}

function App() {
  const [ville, setVille] = useState("");
  const [jourSelectionne, setJourSelectionne] = useState("");
  const [moisSelectionne, setMoisSelectionne] = useState("");
  const [jourMoisEnvoye, setJourMoisEnvoye] = useState("");
  const [chargement, setChargement] = useState("idle");
  const [erreur, setErreur] = useState("");
  const [erreurDate, setErreurDate] = useState("");
  const [resultat, setResultat] = useState(null);

  const formulaireVille = async (e) => {
    e.preventDefault();
    setChargement("loading");
    setErreur("");
    setErreurDate("");
    setJourMoisEnvoye("");

    try {
      const res = await fetch(`${API_BASE_URL}/api/meteo/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ ville }),
      });

      const responseText = await res.text();
      let payload = null;

      try {
        payload = responseText ? JSON.parse(responseText) : null;
      } catch {
        throw new Error(
          "Le backend n'a pas renvoye du JSON. Verifie que Flask tourne bien sur http://127.0.0.1:5001.",
        );
      }

      if (!res.ok) {
        throw new Error(payload?.error || "Erreur serveur.");
      }

      setResultat(payload);
      setChargement("success");
    } catch (error) {
      setResultat(null);
      setChargement("error");
      setErreur(error.message || "Impossible de recuperer les donnees.");
    }
  };

  const formulaireDate = (e) => {
    e.preventDefault();
    setErreurDate("");

    if (!jourSelectionne || !moisSelectionne) {
      setErreurDate("Choisis un jour et un mois avant d'envoyer.");
      return;
    }

    setJourMoisEnvoye(creerCleJourMois(jourSelectionne, moisSelectionne));
  };

  const geleesParAnnee = Object.entries(
    resultat?.mesures_station?.gelees_par_annee ?? {},
  );

  const rechercheJour = (() => {
    if (!resultat || !jourMoisEnvoye) {
      return {
        cleJour: "",
        mesures: [],
        nombreGelees: 0,
      };
    }

    const cleJour = jourMoisEnvoye;
    const mesures = (resultat.mesures_station.historique_complet ?? []).filter(
      (mesure) => mesure.date.slice(5) === cleJour,
    );
    const nombreGelees = mesures.filter(
      (mesure) => mesure.TN !== null && mesure.TN <= 0,
    ).length;

    return {
      cleJour,
      mesures,
      nombreGelees,
    };
  })();

  return (
    <main className="page">
      <section className="hero">
        <div className="hero-copy">
          <p className="eyebrow">Projet Meteo France</p>
          <h1>Retrouver la station meteo la plus proche d&apos;une ville</h1>
          <p className="hero-text">
            Recherche une ville, recupere les donnees de la station la plus
            proche puis filtre toutes les mesures d&apos;un meme jour sur toutes
            les annees.
          </p>
        </div>

        <form className="search-card" onSubmit={formulaireVille}>
          <label className="field">
            <span>Ville</span>
            <input
              type="text"
              value={ville}
              onChange={(e) => setVille(e.target.value)}
              placeholder="Exemple : Orleans"
              required
            />
          </label>

          <button type="submit" disabled={chargement === "loading"}>
            {chargement === "loading" ? "Recherche en cours..." : "Envoyer ville"}
          </button>

          {erreur ? <p className="error-message">{erreur}</p> : null}
        </form>
      </section>

      {chargement === "idle" && (
        <section className="empty-state">
          <p>La recherche n&apos;a pas encore ete lancee.</p>
          <h2>Le tableau de bord apparaitra ici</h2>
          <p>
            Le recap ville/station, les gelees par annee et la recherche par
            jour/mois seront affiches apres l&apos;envoi de la ville.
          </p>
        </section>
      )}

      {chargement === "success" && resultat && (
        <section className="dashboard">
          <div className="summary-grid">
            <article className="panel accent-panel">
              <p className="panel-kicker">Recap</p>
              <h2>{resultat.ville}</h2>
              <div className="meta-list">
                <p>
                  <strong>Departement :</strong> {resultat.departement}
                </p>
                <p>
                  <strong>Station :</strong>{" "}
                  {resultat.station_plus_proche.nom_station}
                </p>
                <p>
                  <strong>Distance :</strong>{" "}
                  {resultat.station_plus_proche.distance_km} km
                </p>
                <p>
                  <strong>Periode :</strong>{" "}
                  {resultat.mesures_station.premiere_date} au{" "}
                  {resultat.mesures_station.derniere_date}
                </p>
              </div>
            </article>

            <article className="panel stat-panel">
              <p className="panel-kicker">Mesure recente</p>
              <h3>{resultat.mesures_station.mesure_plus_recente?.date || "-"}</h3>
              <div className="weather-inline">
                <div>
                  <span>Min</span>
                  <strong>{formatTemperature(resultat.mesures_station.mesure_plus_recente?.TN)}</strong>
                </div>
                <div>
                  <span>Max</span>
                  <strong>{formatTemperature(resultat.mesures_station.mesure_plus_recente?.TX)}</strong>
                </div>
                <div>
                  <span>Moyenne</span>
                  <strong>{formatTemperature(resultat.mesures_station.mesure_plus_recente?.TM)}</strong>
                </div>
              </div>
            </article>

            <article className="panel stat-panel">
              <p className="panel-kicker">Recherche station</p>
              <h3>{resultat.recherche_autres_datasets ? "Elargie" : "Locale"}</h3>
              <p>
                {resultat.recherche_autres_datasets
                  ? "La station retenue a ete trouvee hors departement."
                  : "Une station du departement a ete utilisee."}
              </p>
            </article>
          </div>

          <div className="content-grid">
            <article className="panel">
              <div className="panel-head">
                <div>
                  <p className="panel-kicker">Nombre de gelees</p>
                  <h2>Gel par annee</h2>
                </div>
                <p className="panel-note">
                  Nombre de jours ou la temperature minimale est inferieure ou
                  egale a 0 C.
                </p>
              </div>

              <div className="years-grid">
                {geleesParAnnee.map(([annee, valeur]) => (
                  <div className="year-card" key={annee}>
                    <span>{annee}</span>
                    <strong>{valeur}</strong>
                    <small>jours de gelee</small>
                  </div>
                ))}
              </div>
            </article>

            <article className="panel">
              <div className="panel-head">
                <div>
                  <p className="panel-kicker">Jour sans annee</p>
                  <h2>Toutes les mesures d&apos;un meme jour</h2>
                </div>
                <p className="panel-note">
                  Choisis une date, puis l&apos;application prend seulement le jour
                  et le mois. L&apos;annee est ignoree.
                </p>
              </div>

              <form className="date-form" onSubmit={formulaireDate}>
                <div className="date-grid">
                  <label className="field field-date">
                    <span>Jour</span>
                    <select
                      value={jourSelectionne}
                      onChange={(e) => setJourSelectionne(e.target.value)}
                    >
                      <option value="">Jour</option>
                      {DAYS.map((day) => (
                        <option key={day.value} value={day.value}>
                          {day.label}
                        </option>
                      ))}
                    </select>
                  </label>

                  <label className="field field-date">
                    <span>Mois</span>
                    <select
                      value={moisSelectionne}
                      onChange={(e) => setMoisSelectionne(e.target.value)}
                    >
                      <option value="">Mois</option>
                      {MONTHS.map((month) => (
                        <option key={month.value} value={month.value}>
                          {month.label}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>

                <button type="submit">Envoyer date</button>
              </form>

              {erreurDate ? <p className="error-message">{erreurDate}</p> : null}

              {jourMoisEnvoye ? (
                <div className="selected-day">
                  <div className="selected-day-header">
                    <div>
                      <h3>{rechercheJour.cleJour}</h3>
                      <p>
                        Toutes les mesures du jour selectionne, toutes annees
                        confondues.
                      </p>
                    </div>
                    <div className="day-highlight">
                      <span>Nombre de gelees</span>
                      <strong>{rechercheJour.nombreGelees}</strong>
                    </div>
                  </div>

                  {rechercheJour.mesures.length > 0 ? (
                    <div className="day-results">
                      {rechercheJour.mesures.map((mesure) => (
                        <div className="history-row" key={mesure.date}>
                          <span>{mesure.date}</span>
                          <strong>TN {formatTemperature(mesure.TN)}</strong>
                          <strong>TX {formatTemperature(mesure.TX)}</strong>
                          <strong>TM {formatTemperature(mesure.TM)}</strong>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="panel-note">
                      Aucune mesure disponible pour ce jour/mois.
                    </p>
                  )}
                </div>
              ) : null}
            </article>
          </div>
        </section>
      )}
    </main>
  );
}

export default App;
