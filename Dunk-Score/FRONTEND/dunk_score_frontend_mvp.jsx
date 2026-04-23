export default function DunkScoreFrontendMVP() {
  const games = [
    {
      id: "001",
      away: "Lakers",
      home: "Celtics",
      homeWinProb: 0.64,
      awayWinProb: 0.36,
      projectedTotal: 228.5,
      confidence: 0.74,
      status: "Hoje • 20:30",
      factors: ["ORTG +4.2", "Descanso +1 dia", "Mando de quadra"],
    },
    {
      id: "002",
      away: "Nuggets",
      home: "Suns",
      homeWinProb: 0.48,
      awayWinProb: 0.52,
      projectedTotal: 221.0,
      confidence: 0.58,
      status: "Hoje • 22:00",
      factors: ["Pace menor", "Forma recente equilibrada", "Lesão questionável"],
    },
    {
      id: "003",
      away: "Heat",
      home: "Bucks",
      homeWinProb: 0.69,
      awayWinProb: 0.31,
      projectedTotal: 216.5,
      confidence: 0.81,
      status: "Amanhã • 21:00",
      factors: ["DRTG superior", "Rebote +6%", "Últimos 10 jogos: 8-2"],
    },
  ];

  const topGame = games[0];

  const pct = (value: number) => `${(value * 100).toFixed(1)}%`;

  const confidenceLabel = (value: number) => {
    if (value >= 0.75) return "Alta";
    if (value >= 0.6) return "Média";
    return "Baixa";
  };

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      <div className="mx-auto max-w-7xl px-6 py-8">
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
              <p className="text-xs uppercase tracking-wide text-zinc-500">Jogos monitorados</p>
              <p className="mt-2 text-2xl font-semibold">{games.length}</p>
            </div>
            <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-4">
              <p className="text-xs uppercase tracking-wide text-zinc-500">Modelo ativo</p>
              <p className="mt-2 text-2xl font-semibold">v0.2</p>
            </div>
          </div>
        </header>

        <section className="mb-8 grid gap-6 lg:grid-cols-[1.35fr_0.65fr]">
          <div className="rounded-3xl border border-zinc-800 bg-gradient-to-br from-zinc-900 to-zinc-950 p-6 shadow-2xl shadow-black/30">
            <div className="mb-4 flex items-start justify-between gap-4">
              <div>
                <p className="text-sm text-zinc-400">Jogo em destaque</p>
                <h2 className="mt-1 text-3xl font-semibold">
                  {topGame.away} <span className="text-zinc-500">vs</span> {topGame.home}
                </h2>
                <p className="mt-2 text-sm text-zinc-400">{topGame.status}</p>
              </div>
              <div className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-sm text-emerald-300">
                Confiança {confidenceLabel(topGame.confidence)}
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-3">
              <div className="rounded-2xl bg-zinc-900/70 p-4">
                <p className="text-xs uppercase text-zinc-500">Prob. mandante</p>
                <p className="mt-2 text-3xl font-bold">{pct(topGame.homeWinProb)}</p>
              </div>
              <div className="rounded-2xl bg-zinc-900/70 p-4">
                <p className="text-xs uppercase text-zinc-500">Prob. visitante</p>
                <p className="mt-2 text-3xl font-bold">{pct(topGame.awayWinProb)}</p>
              </div>
              <div className="rounded-2xl bg-zinc-900/70 p-4">
                <p className="text-xs uppercase text-zinc-500">Total projetado</p>
                <p className="mt-2 text-3xl font-bold">{topGame.projectedTotal}</p>
              </div>
            </div>

            <div className="mt-6">
              <div className="mb-2 flex justify-between text-sm text-zinc-400">
                <span>Força da previsão</span>
                <span>{pct(topGame.confidence)}</span>
              </div>
              <div className="h-3 overflow-hidden rounded-full bg-zinc-800">
                <div
                  className="h-full rounded-full bg-white"
                  style={{ width: `${topGame.confidence * 100}%` }}
                />
              </div>
            </div>
          </div>

          <aside className="rounded-3xl border border-zinc-800 bg-zinc-900 p-6">
            <p className="text-sm text-zinc-400">Principais fatores</p>
            <div className="mt-4 space-y-3">
              {topGame.factors.map((factor) => (
                <div key={factor} className="rounded-2xl border border-zinc-800 bg-zinc-950 p-4 text-sm">
                  {factor}
                </div>
              ))}
            </div>
          </aside>
        </section>

        <section>
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-2xl font-semibold">Jogos do dia</h3>
            <div className="rounded-full border border-zinc-800 px-3 py-1 text-sm text-zinc-400">
              Atualização automática
            </div>
          </div>

          <div className="grid gap-4 xl:grid-cols-3">
            {games.map((game) => (
              <article
                key={game.id}
                className="rounded-3xl border border-zinc-800 bg-zinc-900 p-5 transition hover:border-zinc-700 hover:bg-zinc-900/80"
              >
                <div className="mb-4 flex items-start justify-between gap-4">
                  <div>
                    <p className="text-sm text-zinc-400">{game.status}</p>
                    <h4 className="mt-1 text-xl font-semibold">
                      {game.away} <span className="text-zinc-500">vs</span> {game.home}
                    </h4>
                  </div>
                  <span className="rounded-full border border-zinc-700 px-2.5 py-1 text-xs text-zinc-300">
                    {confidenceLabel(game.confidence)}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="rounded-2xl bg-zinc-950 p-3">
                    <p className="text-xs uppercase text-zinc-500">Mandante</p>
                    <p className="mt-1 text-2xl font-bold">{pct(game.homeWinProb)}</p>
                  </div>
                  <div className="rounded-2xl bg-zinc-950 p-3">
                    <p className="text-xs uppercase text-zinc-500">Visitante</p>
                    <p className="mt-1 text-2xl font-bold">{pct(game.awayWinProb)}</p>
                  </div>
                </div>

                <div className="mt-4 rounded-2xl bg-zinc-950 p-3">
                  <p className="text-xs uppercase text-zinc-500">Total projetado</p>
                  <p className="mt-1 text-2xl font-bold">{game.projectedTotal}</p>
                </div>

                <div className="mt-4">
                  <div className="mb-2 flex justify-between text-xs text-zinc-500">
                    <span>Confiança</span>
                    <span>{pct(game.confidence)}</span>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-zinc-800">
                    <div className="h-full rounded-full bg-white" style={{ width: `${game.confidence * 100}%` }} />
                  </div>
                </div>

                <div className="mt-4 flex flex-wrap gap-2">
                  {game.factors.map((factor) => (
                    <span key={factor} className="rounded-full border border-zinc-800 px-2.5 py-1 text-xs text-zinc-300">
                      {factor}
                    </span>
                  ))}
                </div>
              </article>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
