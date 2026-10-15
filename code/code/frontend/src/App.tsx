import { useEffect, useState } from "react";
import "./App.css";

interface IndicatorDetail {
    id: string;
    name: string;
    value: number | null;
    unit: string | null;
    year: number | null;
    source: string | null;
    mapping_type: string | null;
    quality: string | null;
    }

interface ScenarioInfo {
    name: string;
    description: string;
    affected_indicators: Record<string, {mode:string, value:number }>;
    }

interface AppliedAction {
    indicator_id: string;
    indicator_name: string;
    mode: string;
    value: number;
    before: number | null;
    after: number | null;
    }

interface SimulationResponse {
    scenario_name:string;
    baseline_bz_index:number;
    scenario_bz_index:number;
    delta_bz:number;
    delta_layers:Record<string, number>;
    delta_power9:Record<string, number>;
    applied_actions: AppliedAction[];
    }

// Oblika podatkov, ki jih pricakujemo iz /api/pilots/{pilot}/baseline
interface BaselineResponse {
  pilot_name: string;
  data_version: string;
  bz_index: number;
  layer_scores: Record<string, number>;
  layer_names: Record<string, string>;
  power9_scores: Record<string, number>;
  data_coverage: Record<string, number>;
  warnings: string[];
  indicators: IndicatorDetail[];
  indicator_names: Record<string, string>;
}

function qualityChipClass(quality: string | null): string {
    if (quality === 'needs_review') return 'chip chip-warn';
    if (quality === 'official') return 'chip chip-good';
    return 'chip';
    }


function mappingTypeChipClass(mappingType: string | null): string {
    if (mappingType === 'exact') return 'chip chip-good';
    return 'chip';
    }

function deltaClass(delta: number): string {
    if (delta > 0) return 'delta-positive'
    if (delta < 0) return 'delta-negative';
    return 'delta-neutral';
    }

const PILOTS = [
    { code: 'svidnik', label: 'Svidník (SK)'},
    { code: 'beltinci', label: 'Beltinci (SI)'},
    { code: 'montegrotto', label: 'Montegrotto (IT)'},
    ];

function App() {
  const [baseline, setBaseline] = useState<BaselineResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [scenarios, setScenarios] = useState<Record<string, ScenarioInfo>>({});
  const [selectedScenario, setSelectedScenario] = useState<string>('');
  const [simulationResult, setSimulationResult] = useState<SimulationResponse | null>(null);
  const [simulationError, setSimulationError] = useState<string | null>(null);
  const [showWarnings, setShowWarnings] = useState(false)
  const [selectedPilot, setSelectedPilot] = useState<string>('svidnik');
  const [availablePilots, setAvailablePilots] = useState<string[]>([]);

    useEffect(() => {
    fetch(`http://127.0.0.1:8000/api/pilots/${selectedPilot}/baseline`)
      .then((response) => {
        if (!response.ok) {
          throw new Error("Napaka pri klicu API-ja: " + response.status);
        }
        return response.json();
      })
      .then((data: BaselineResponse) => {
        setBaseline(data);
        setError(null);
      })
      .catch((err) => setError(err.message));
  }, [selectedPilot]);

    useEffect(() => {
    fetch("http://127.0.0.1:8000/api/scenarios")
      .then((response) => response.json())
      .then((data: Record<string, ScenarioInfo>) => {
        setScenarios(data);
        const firstKey = Object.keys(data)[0];
        if (firstKey) setSelectedScenario(firstKey);
      });
  }, []);

    useEffect(() => {
        fetch("http://127.0.0.1:8000/api/pilots")
            .then((response) => response.json())
            .then((data: { pilots: string[] }) => setAvailablePilots(data.pilots));
            }, []);


    function changePilot(code: string) {
        setSelectedPilot(code);
        setSimulationResult(null);
        setSimulationError(null);
        }


function runSimulation() {
    setSimulationError(null);
    fetch('http://127.0.0.1:8000/api/simulations', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({pilot: selectedPilot, scenario_id:selectedScenario }),
    })
        .then((response) => {
            if (!response.ok) {
                throw new Error('Napaka pri simulaciji: ' + response.status);
            }
            return response.json();
        })
        .then((data: SimulationResponse) => setSimulationResult(data))
        .catch((err) => setSimulationError(err.message));
}

  if (error) {
    return <div className="App"><p>Napaka: {error}</p></div>;
  }

  if (!baseline) {
    return <div className="App"><p>Nalagam podatke...</p></div>;
  }

  return (
      <div className='App'>
    <header className='App-header'>
      <div className='header-info'>
        <h1>{baseline.pilot_name}</h1>
        <p>Verzija podatkov: {baseline.data_version}</p>
        <h2>BZ indeks: {baseline.bz_index}</h2>
      </div>

      <div className='pilot-picker'>
        <span className='pilot-picker-label'>Pilotno območje</span>
        <select
            className='scenario-select'
            value={selectedPilot}
            onChange={(e) => changePilot(e.target.value)}
        >
            {PILOTS.map((p) => (
                <option key={p.code} value={p.code} disabled={!availablePilots.includes(p.code)}>
                    {p.label}{availablePilots.includes(p.code) ? '' : ' - ni podatkov'}
                </option>
            ))}
        </select>
      </div>
    </header>
    <section className="card">
      <h3>Ocene po slojih (Layer scores)</h3>
      <table>
        <thead>
          <tr>
            <th>Sloj</th>
            <th>Ocena</th>
            <th>Pokritost podatkov</th>
          </tr>
        </thead>
        <tbody>
          {Object.entries(baseline.layer_scores).map(([layerId, score]) => (
            <tr key={layerId}>
              <td>{baseline.layer_names[layerId] ?? layerId}</td>
              <td>{score}</td>
              <td>
                <div className="coverage-bar">
                  <div
                    className="coverage-bar-fill"
                    style={{ width: `${Math.round((baseline.data_coverage[layerId] ?? 0) * 100)}%` }}
                  />
                </div>
                <span className="coverage-label">
                  {baseline.data_coverage[layerId] !== undefined
                    ? Math.round(baseline.data_coverage[layerId] * 100) + "%"
                    : "-"}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>

    <section className="card">
      <h3>Power 9 ocene</h3>
      <div className="power9-grid">
        {Object.entries(baseline.power9_scores).map(([dimId, score]) => (
          <div className="power9-tile" key={dimId}>
            <span className="power9-id">{dimId}</span>
            <span className="power9-score">{score}</span>
          </div>
        ))}
      </div>
    </section>

    <section className='card'>
      <h3>Vhodni indikatorji (izpolnjeni)</h3>
      <div className='table-scroll'>
      <table>
        <thead>
            <tr>
                <th>Indikator</th>
                <th>Vrednost</th>
                <th>Leto</th>
                <th>Tip mapiranja</th>
                <th>Kakovost</th>
            </tr>
        </thead>
      <tbody>
        {baseline.indicators
            .filter((ind) => ind.value != null)
            .map((ind) => (
                <tr key={ind.id}>
                    <td>{ind.name}</td>
                    <td>{ind.value}</td>
                    <td>{ind.year}</td>
                    <td><span className={mappingTypeChipClass(ind.mapping_type)}>{ind.mapping_type}</span></td>
                    <td><span className={qualityChipClass(ind.quality)}>{ind.quality}</span></td>
                </tr>
            ))}
        </tbody>
      </table>
     </div>
    </section>

  <section className='card card-stack'>
    <h2>Scenario Builder</h2>
    <select
        className='scenario-select'
        value={selectedScenario}
        onChange={(e) => setSelectedScenario (e.target.value)}
        >
            {Object.entries(scenarios).map(([id, s]) => (
                <option key={id} value={id}>
                    {s.name}
                </option>
                ))}
            </select>

            {selectedScenario && scenarios[selectedScenario] && (
                <div className='scenario-details'>
                    <p>{scenarios[selectedScenario].description}</p>
                    <p className='scenario-subtitle'>Spremeni indikatorje:</p>
                    <ul className='scenario-indicator-list'>
                        {Object.entries(scenarios[selectedScenario].affected_indicators).map(
                            ([indID, effect]) => (
                                <li key={indID}>
                                    <span className='chip'>{baseline.indicator_names[indID] ?? indID}</span> {effect.mode} {effect.value}
                                </li>
                            )
                        )}
                    </ul>
                </div>
                    )}
    <div className='button-row'>
        <button className='btn-primary' onClick={runSimulation}>Zaženi simulacijo</button>
        {baseline.warnings.length > 0 && (
            <button className='btn-secondary' onClick={() => setShowWarnings(!showWarnings)}>
                {showWarnings ? 'Skrij': 'Prikaži'} opozorila ({baseline.warnings.length})
            </button>
        )}
    </div>

    {showWarnings && (
        <ul className='warning-list warning-box'>
        {baseline.warnings.map((warning, i) => (
            <li key={i}>{warning}</li>
            ))}
        </ul>
    )}

    {simulationError && <p>Napaka: {simulationError}</p>}
  </section>


{simulationResult && (
  <section className="card card-stack">
    <h3>Rezultat: {simulationResult.scenario_name}</h3>

    <div className="result-stats">
      <div className="result-stat">
        <span className="result-stat-label">Baseline BZ indeks</span>
        <span className="result-stat-value">{simulationResult.baseline_bz_index}</span>
      </div>
      <div className="result-stat">
        <span className="result-stat-label">BZ indeks po scenariju</span>
        <span className="result-stat-value">{simulationResult.scenario_bz_index}</span>
      </div>
      <div className="result-stat">
        <span className="result-stat-label">Sprememba (delta)</span>
        <span className={`result-stat-value ${deltaClass(simulationResult.delta_bz)}`}>
          {simulationResult.delta_bz > 0 ? "+" : ""}{simulationResult.delta_bz}
        </span>
      </div>
    </div>

    <div>
      <h4 className="result-subtitle">Sprememba po slojih</h4>
      <ul className="delta-list">
        {Object.entries(simulationResult.delta_layers).map(([layerId, delta]) => (
          <li key={layerId}>
            <span className="chip">{baseline.layer_names[layerId] ?? layerId}</span>
            <span className={deltaClass(delta)}>{delta > 0 ? "+" : ""}{delta}</span>
          </li>
        ))}
      </ul>
    </div>

    <div>
      <h4 className="result-subtitle">Sprememba po Power9 dimenzijah</h4>
      <ul className="delta-list">
        {Object.entries(simulationResult.delta_power9).map(([dimId, delta]) => (
          <li key={dimId}>
            <span className="chip">{dimId}</span>
            <span className={deltaClass(delta)}>{delta > 0 ? "+" : ""}{delta}</span>
          </li>
        ))}
      </ul>
    </div>

    <div>
      <h4 className="result-subtitle">Izvedeni ukrepi (applied actions)</h4>
      <ul className="scenario-indicator-list">
        {simulationResult.applied_actions.map((action) => (
          <li key={action.indicator_id}>
            <span className="chip">{action.indicator_name}</span> {action.mode} {action.value}
          </li>
        ))}
      </ul>
    </div>

    <p className="disclaimer">
      <em>
        Opozorilo: gre za simuliran učinek na podlagi predpostavk modela, ne za dokazano vzročno posledico.
      </em>
    </p>
  </section>
)}
    </div>
  );
}

export default App;