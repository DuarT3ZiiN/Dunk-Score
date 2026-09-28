import { useCallback, useEffect, useMemo, useState } from "react";
import { fetchGames, predictGame } from "./api.js";

// Escala típica de cada diferença, para comparar fatores de unidades diferentes.
const FACTOR_SCALE = {
  points_diff: 5,
  rebounds_diff: 3,
  assists_diff: 3,
  turnovers_diff: 2,
  form_diff: 0.3,
  fg_pct_diff: 0.03,
  rest_diff: 1.5,
};

// Em turnovers, valor positivo (mandante erra mais) favorece o visitante.
const LOWER_IS_BETTER = new Set(["turnovers_diff"]);

const pct = (value) => `${(value * 100).toFixed(1)}%`;

const signed = (value, digits = 1) => `${value > 0 ? "+" : ""}${value.toFixed(digits)}`;

const formatFactorValue = ({ feature, value }) => {
  if (feature === "form_diff") return `${signed(value * 100, 0)} p.p.`;
  if (feature === "fg_pct_diff") return `${signed(value * 100)} p.p.`;
  if (feature === "rest_diff") return `${signed(value, 0)} dia(s)`;
  return signed(value);
};

const confidenceLabel = (value) => {
  if (value >= 0.5) return "Alta";
  if (value >= 0.25) return "Média";
  return "Baixa";
};

const todayISO = () => {
  const now = new Date();
  return new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString().slice(0, 10);
};

const teamName = (team) => team.name || team.abbreviation || team.external_id;

function topFactors(game, count = 3) {
  const factors = game.prediction?.factors ?? [];
  return [...factors]
    .filter((f) => f.value !== 0)
    .sort((a, b) => Math.abs(b.value) / (FACTOR_SCALE[b.feature] ?? 1) - Math.abs(a.value) / (FACTOR_SCALE[a.feature] ?? 1))
    .slice(0, count)
    .map((f) => {
      const favorsHome = LOWER_IS_BETTER.has(f.feature) ? f.value < 0 : f.value > 0;
      const team = favorsHome ? game.home_team : game.away_team;
      return {
        key: f.feature,
        text: `${f.label} ${formatFactorValue(f)}`,
        favors: team.abbreviation || teamName(team),
      };
    });
}

function gameStatus(game) {
  const date = new Date(game.game_date).toLocaleDateString("pt-BR", { timeZone: "UTC" });
  return game.status ? `${date} • ${game.status}` : date;
}

function Score({ game }) {
  if (game.home_score == null || game.away_score == null) return null;
  return (
    <p className="mt-1 text-sm text-zinc-400">
      Placar final: {game.away_score} x {game.home_score}
    </p>
  );
}

function PredictButton({ game, busy, onPredict, className = "" }) {
  return (
    <button
      type="button"
      onClick={() => onPredict(game.game_id)}
      disabled={busy}
      className={`rounded-full border border-zinc-700 px-4 py-2 text-sm text-zinc-200 transition hover:border-zinc-500 hover:bg-zinc-800 disabled:cursor-wait disabled:opacity-50 ${className}`}
    >
      {busy ? "Calculando..." : game.prediction ? "Recalcular" : "Gerar previsão"}
    </button>
  );
}

function FeaturedGame({ game, busy, onPredict }) {
  const prediction = game.prediction;
  const factors = topFactors(game, 4);

  return (
    <section className="mb-8 grid gap-6 lg:grid-cols-[1.35fr_0.65fr]">
      <div className="rounded-3xl border border-zinc-800 bg-gradient-to-br from-zinc-900 to-zinc-950 p-6 shadow-2xl shadow-black/30">
        <div className="mb-4 flex items-start justify-between gap-4">
          <div>
            <p className="text-sm text-zinc-400">Jogo em destaque</p>
            <h2 className="mt-1 text-3xl font-semibold">
              {teamName(game.away_team)} <span className="text-zinc-500">@</span> {teamName(game.home_team)}
            </h2>
            <p className="mt-2 text-sm text-zinc-400">{gameStatus(game)}</p>
            <Score game={game} />
          </div>
          {prediction ? (
            <div className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-sm text-emerald-300">
              Confiança {confidenceLabel(prediction.confidence_score)}
            </div>
          ) : (
            <PredictButton game={game} busy={busy} onPredict={onPredict} />
          )}
        </div>

        {prediction ? (
          <>
            <div className="grid gap-4 md:grid-cols-3">
              <Stat label={`Prob. ${game.home_team.abbreviation ?? "mandante"} (casa)`} value={pct(prediction.home_win_prob)} large />
              <Stat label={`Prob. ${game.away_team.abbreviation ?? "visitante"} (fora)`} value={pct(prediction.away_win_prob)} large />
              <Stat label="Total projetado" value={prediction.projected_total?.toFixed(1) ?? "—"} large />
            </div>

            <div className="mt-6">
              <div className="mb-2 flex justify-between text-sm text-zinc-400">
                <span>Força da previsão</span>
                <span>{pct(prediction.confidence_score)}</span>
              </div>
              <div className="h-3 overflow-hidden rounded-full bg-zinc-800">
                <div className="h-full rounded-full bg-white" style={{ width: `${prediction.confidence_score * 100}%` }} />
              </div>
            </div>
          </>
        ) : (
          <p className="text-sm text-zinc-400">Este jogo ainda não tem previsão.</p>
        )}
      </div>

      <aside className="rounded-3xl border border-zinc-800 bg-zinc-900 p-6">
        <p className="text-sm text-zinc-400">Principais fatores</p>
        <div className="mt-4 space-y-3">
          {factors.length === 0 && <p className="text-sm text-zinc-500">Gere a previsão para ver os fatores.</p>}
          {factors.map((factor) => (
            <div key={factor.key} className="flex items-center justify-between gap-3 rounded-2xl border border-zinc-800 bg-zinc-950 p-4 text-sm">
              <span>{factor.text}</span>
              <span className="text-xs text-zinc-500">favorece {factor.favors}</span>
            </div>
          ))}
        </div>
      </aside>
    </section>
  );
}

function Stat({ label, value, large = false }) {
  return (
    <div className={`rounded-2xl ${large ? "bg-zinc-900/70 p-4" : "bg-zinc-950 p-3"}`}>
      <p className="text-xs uppercase text-zinc-500">{label}</p>
      <p className={`mt-1 font-bold ${large ? "text-3xl" : "text-2xl"}`}>{value}</p>
    </div>
  );
}

function GameCard({ game, busy, onPredict }) {
  const prediction = game.prediction;

  return (
    <article className="flex flex-col rounded-3xl border border-zinc-800 bg-zinc-900 p-5 transition hover:border-zinc-700 hover:bg-zinc-900/80">
      <div className="mb-4 flex items-start justify-between gap-4">
        <div>
          <p className="text-sm text-zinc-400">{gameStatus(game)}</p>
          <h4 className="mt-1 text-xl font-semibold">
            {teamName(game.away_team)} <span className="text-zinc-500">@</span> {teamName(game.home_team)}
          </h4>
          <Score game={game} />
        </div>
        {prediction && (
          <span className="rounded-full border border-zinc-700 px-2.5 py-1 text-xs text-zinc-300">
            {confidenceLabel(prediction.confidence_score)}
          </span>
        )}
      </div>

      {prediction ? (
        <>
          <div className="grid grid-cols-2 gap-3">
            <Stat label={`${game.home_team.abbreviation ?? "Mandante"} (casa)`} value={pct(prediction.home_win_prob)} />
            <Stat label={`${game.away_team.abbreviation ?? "Visitante"} (fora)`} value={pct(prediction.away_win_prob)} />
          </div>

          <div className="mt-4">
            <Stat label="Total projetado" value={prediction.projected_total?.toFixed(1) ?? "—"} />
          </div>

          <div className="mt-4">
            <div className="mb-2 flex justify-between text-xs text-zinc-500">
              <span>Confiança</span>
              <span>{pct(prediction.confidence_score)}</span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-zinc-800">
              <div className="h-full rounded-full bg-white" style={{ width: `${prediction.confidence_score * 100}%` }} />
            </div>
          </div>

          <div className="mt-4 flex flex-wrap gap-2">
            {topFactors(game).map((factor) => (
              <span key={factor.key} className="rounded-full border border-zinc-800 px-2.5 py-1 text-xs text-zinc-300">
                {factor.text}
              </span>
            ))}
          </div>
        </>
      ) : (
        <div className="mt-auto pt-2">
          <PredictButton game={game} busy={busy} onPredict={onPredict} className="w-full" />
        </div>
      )}
    </article>
  );
}

export default function App() {
  const [date, setDate] = useState(todayISO);
  const [games, setGames] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [busyIds, setBusyIds] = useState(() => new Set());

  const load = useCallback(async (day) => {
    setLoading(true);
    setError(null);
    try {
      setGames(await fetchGames(day));
    } catch (err) {
      setGames([]);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load(date);
  }, [date, load]);

  const setBusy = (gameId, busy) =>
    setBusyIds((prev) => {
      const next = new Set(prev);
      busy ? next.add(gameId) : next.delete(gameId);
      return next;
    });

  const handlePredict = useCallback(async (gameId) => {
    setBusy(gameId, true);
    try {
      const updated = await predictGame(gameId);
      setGames((prev) => prev.map((g) => (g.game_id === gameId ? updated : g)));
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(gameId, false);
    }
  }, []);

  const handlePredictAll = () => games.filter((g) => !g.prediction).forEach((g) => handlePredict(g.game_id));

  const featured = useMemo(() => {
    const predicted = games.filter((g) => g.prediction);
    if (predicted.length === 0) return games[0];
    return predicted.reduce((best, g) => (g.prediction.confidence_score > best.prediction.confidence_score ? g : best));
  }, [games]);

  const modelVersion = games.find((g) => g.prediction)?.prediction.model_version;
  const missing = games.filter((g) => !g.prediction).length;

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6">
        <header className="mb-8 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.2em] text-zinc-400">NBA Predictive Platform</p>
            <h1 className="text-4xl font-bold tracking-tight">Dunk-Score</h1>
            <p className="mt-2 max-w-2xl text-sm text-zinc-400">
              Probabilidades pré-jogo, total projetado, confiança do modelo e fatores que mais influenciam cada confronto.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-3 md:w-[360px]">
            <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-4">
              <p className="text-xs uppercase tracking-wide text-zinc-500">Jogos no dia</p>
              <p className="mt-2 text-2xl font-semibold">{loading ? "…" : games.length}</p>
            </div>
            <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-4">
              <p className="text-xs uppercase tracking-wide text-zinc-500">Modelo ativo</p>
              <p className="mt-2 truncate text-sm font-semibold" title={modelVersion}>
                {modelVersion ?? "—"}
              </p>
            </div>
          </div>
        </header>

        {error && (
          <div className="mb-6 rounded-2xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-300">{error}</div>
        )}

        {!loading && featured && <FeaturedGame game={featured} busy={busyIds.has(featured.game_id)} onPredict={handlePredict} />}

        <section>
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
            <h3 className="text-2xl font-semibold">Jogos do dia</h3>
            <div className="flex flex-wrap items-center gap-3">
              {missing > 0 && (
                <button
                  type="button"
                  onClick={handlePredictAll}
                  className="rounded-full border border-zinc-700 px-3 py-1 text-sm text-zinc-200 transition hover:border-zinc-500 hover:bg-zinc-800"
                >
                  Gerar {missing} previs{missing === 1 ? "ão" : "ões"}
                </button>
              )}
              <input
                type="date"
                value={date}
                onChange={(e) => e.target.value && setDate(e.target.value)}
                className="rounded-full border border-zinc-800 bg-zinc-900 px-3 py-1 text-sm text-zinc-200 [color-scheme:dark]"
              />
            </div>
          </div>

          {loading && <p className="text-sm text-zinc-400">Carregando jogos...</p>}

          {!loading && !error && games.length === 0 && (
            <div className="rounded-3xl border border-dashed border-zinc-800 p-8 text-center text-sm text-zinc-400">
              Nenhum jogo encontrado para esta data. Escolha outra data ou rode a sincronização com o balldontlie.
            </div>
          )}

          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {games.map((game) => (
              <GameCard key={game.game_id} game={game} busy={busyIds.has(game.game_id)} onPredict={handlePredict} />
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
