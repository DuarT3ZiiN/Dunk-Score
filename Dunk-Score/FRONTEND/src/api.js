// Em produção, defina VITE_API_BASE com a URL do backend; em dev o Vite faz proxy de /api.
const BASE = import.meta.env.VITE_API_BASE ?? "/api";

async function request(path, options) {
  const resp = await fetch(`${BASE}${path}`, options);
  if (!resp.ok) {
    const body = await resp.json().catch(() => ({}));
    throw new Error(body.detail || `Erro ${resp.status}`);
  }
  return resp.json();
}

export const fetchGames = (date) => request(`/games?date=${date}`);

export const predictGame = (gameId) =>
  request(`/games/${encodeURIComponent(gameId)}/predict`, { method: "POST" });
