import { type ClassValue, clsx } from "clsx";
import type { Snippet } from "svelte";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// os componentes do shadcn-svelte (via bits-ui) usam isso pra tirar "child"/"children" do tipo
// de props quando o wrapper já renderiza o próprio filho por conta própria
export type WithoutChild<T> = T extends { child?: Snippet<[infer _]> } ? Omit<T, "child"> : T;
export type WithoutChildren<T> = T extends { children?: Snippet } ? Omit<T, "children"> : T;
export type WithoutChildrenOrChild<T> = WithoutChildren<WithoutChild<T>>;
export type WithElementRef<T, E extends HTMLElement = HTMLElement> = T & { ref?: E | null };
