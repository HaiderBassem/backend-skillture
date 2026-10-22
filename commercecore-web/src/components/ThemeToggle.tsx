import { Moon, Sun } from "lucide-react";
import { useState } from "react";
import { IconButton } from "./ui/Button";

type Theme = "light" | "dark";

function currentTheme(): Theme {
  const saved = document.documentElement.dataset.theme;
  if (saved === "light" || saved === "dark") return saved;
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>(currentTheme);
  const next: Theme = theme === "dark" ? "light" : "dark";

  function toggle() {
    document.documentElement.dataset.theme = next;
    try {
      localStorage.setItem("cc.theme", next);
    } catch {
      // not persisted; still applies for this visit
    }
    setTheme(next);
  }

  return (
    <IconButton label={`Switch to ${next} theme`} onClick={toggle}>
      {theme === "dark" ? <Sun className="size-5" aria-hidden /> : <Moon className="size-5" aria-hidden />}
    </IconButton>
  );
}
