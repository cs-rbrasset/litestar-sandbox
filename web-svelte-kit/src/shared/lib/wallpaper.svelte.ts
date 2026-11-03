const STORAGE_KEY = "wallpaper";

export type WallpaperId = (typeof WALLPAPERS)[number]["id"];

export const WALLPAPERS = [
  { id: "aurora", label: "Aurora", src: "/wallpapers/aurora.svg" },
  { id: "sunset", label: "Entardecer", src: "/wallpapers/sunset.svg" },
  { id: "forest", label: "Floresta", src: "/wallpapers/forest.svg" },
  { id: "mono", label: "Neutro", src: "/wallpapers/mono.svg" },
] as const;

function readStored(): WallpaperId | null {
  if (typeof localStorage === "undefined") return null;
  const value = localStorage.getItem(STORAGE_KEY);
  return WALLPAPERS.some((w) => w.id === value) ? (value as WallpaperId) : null;
}

let selectedId = $state<WallpaperId | null>(readStored());

export const wallpaper = {
  get selected() {
    return WALLPAPERS.find((w) => w.id === selectedId) ?? null;
  },
  get selectedId() {
    return selectedId;
  },
  set(id: WallpaperId | null) {
    selectedId = id;
    if (id) {
      localStorage.setItem(STORAGE_KEY, id);
    } else {
      localStorage.removeItem(STORAGE_KEY);
    }
  },
};
