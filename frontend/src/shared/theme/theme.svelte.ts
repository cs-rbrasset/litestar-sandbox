type Theme = "light" | "dark";

const STORAGE_KEY = "theme";

function applyTheme(value: Theme) {
  document.documentElement.classList.toggle("dark", value === "dark");
}

function readInitialTheme(): Theme {
  if (typeof document === "undefined") return "dark";
  return document.documentElement.classList.contains("dark") ? "dark" : "light";
}

let current = $state<Theme>(readInitialTheme());

export const theme = {
  get current() {
    return current;
  },
  toggle() {
    current = current === "dark" ? "light" : "dark";
    localStorage.setItem(STORAGE_KEY, current);
    applyTheme(current);
  },
};
