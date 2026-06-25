import { useEffect, useState } from "react";

import "./App.css";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:5001";

function App() {
  const [ville, setVille] = useState("");
  const [dateSelectionnee, setDateSelectionnee] = useState("");
  const [chargement, setChargement] = useState("idle");
  const [erreur, setErreur] = useState("");
  const [resultat, setResultat] = useState(null);

  useEffect(() => {
    const dateRecente = resultat?.mesures_station?.mesure_plus_recente?.date ?? "";
    setDateSelectionnee(dateRecente);
  }, [resultat]);

  const formulaire = async (e) => {
    e.preventDefault();
    setChargement("loading");
    setErreur("");

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

  const mesureChoisie =
    resultat?.mesures_station?.mesures_par_date?.[dateSelectionnee] ?? null;

  const geleesParAnnee = Object.entries(
    resultat?.mesures_station?.gelees_par_annee ?? {},
  );

  const stationsProches = [...(resultat?.tableau_distances ?? [])]
    .sort((a, b) => a.distance_km - b.distance_km)
    .slice(0, 6);

  return (
    <main className="page">
      <section className="hero">
        <div className="hero-copy">
          <p className="eyebrow">Projet Meteo France</p>
          <h1>Retrouver la station meteo la plus proche d&apos;une ville</h1>
          <p className="hero-text">
            Entre une ville, on interroge le backend Flask, on cherche la
            meilleure station et on affiche les mesures utiles directement sur
            la page.
          </p>
        </div>

        <form className="search-card" onSubmit={formulaire}>
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
            {chargement === "loading" ? "Recherche en cours..." : "Lancer la recherche"}
          </button>

          {erreur ? <p className="error-message">{erreur}</p> : null}
        </form>
      </section>

      {chargement === "idle" && (
        <section className="empty-state">
          <p>La recherche n&apos;a pas encore ete lancee.</p>
          <h2>Le tableau de bord apparaitra ici</h2>
          <p>
            Tu verras le recap de la ville, la station choisie, les gelees par
            annee et le detail des temperatures pour une date precise.
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
                  <strong>Periode dispo :</strong>{" "}
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
                  <strong>
                    {resultat.mesures_station.mesure_plus_recente?.TN ?? "-"} C
                  </strong>
                </div>
                <div>
                  <span>Max</span>
                  <strong>
                    {resultat.mesures_station.mesure_plus_recente?.TX ?? "-"} C
                  </strong>
                </div>
                <div>
                  <span>Moyenne</span>
                  <strong>
                    {resultat.mesures_station.mesure_plus_recente?.TM ?? "-"} C
                  </strong>
                </div>
              </div>
            </article>

            <article className="panel stat-panel">
              <p className="panel-kicker">Recherche</p>
              <h3>{resultat.recherche_autres_datasets ? "Elargie" : "Locale"}</h3>
              <p>
                {resultat.recherche_autres_datasets
                  ? "La meilleure station a ete cherchee hors departement."
                  : "Une station du departement est suffisament proche."}
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
                  Compte des jours ou la temperature minimale est inferieure ou
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
                  <p className="panel-kicker">Recherche par date</p>
                  <h2>Temperature du jour choisi</h2>
                </div>
              </div>

              <label className="field field-date">
                <span>Date</span>
                <input
                  type="date"
                  min={resultat.mesures_station.premiere_date || undefined}
                  max={resultat.mesures_station.derniere_date || undefined}
                  value={dateSelectionnee}
                  onChange={(e) => setDateSelectionnee(e.target.value)}
                />
              </label>

              {mesureChoisie ? (
                <div className="selected-day">
                  <h3>{dateSelectionnee}</h3>
                  <div className="weather-inline">
                    <div>
                      <span>Min</span>
                      <strong>{mesureChoisie.TN ?? "-"} C</strong>
                    </div>
                    <div>
                      <span>Max</span>
                      <strong>{mesureChoisie.TX ?? "-"} C</strong>
                    </div>
                    <div>
                      <span>Moyenne</span>
                      <strong>{mesureChoisie.TM ?? "-"} C</strong>
                    </div>
                  </div>
                </div>
              ) : (
                <p className="panel-note">
                  Aucune mesure disponible pour cette date.
                </p>
              )}
            </article>
          </div>

          <div className="content-grid">
            <article className="panel">
              <div className="panel-head">
                <div>
                  <p className="panel-kicker">Stations voisines</p>
                  <h2>Les plus proches</h2>
                </div>
              </div>

              <div className="station-list">
                {stationsProches.map((station) => (
                  <div className="station-row" key={`${station.fichier}-${station.num_poste}`}>
                    <div>
                      <strong>{station.nom_station}</strong>
                      <p>{station.num_poste}</p>
                    </div>
                    <span>{station.distance_km} km</span>
                  </div>
                ))}
              </div>
            </article>

            <article className="panel">
              <div className="panel-head">
                <div>
                  <p className="panel-kicker">Dernieres mesures</p>
                  <h2>Historique recent</h2>
                </div>
              </div>

              <div className="history-list">
                {resultat.mesures_station.historique_recent.map((mesure) => (
                  <div className="history-row" key={mesure.date}>
                    <span>{mesure.date}</span>
                    <strong>TN {mesure.TN ?? "-"} C</strong>
                    <strong>TX {mesure.TX ?? "-"} C</strong>
                    <strong>TM {mesure.TM ?? "-"} C</strong>
                  </div>
                ))}
              </div>
            </article>
          </div>
        </section>
      )}
    </main>
  );
}

export default App;
