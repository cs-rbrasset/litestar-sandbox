const quantity = new Intl.NumberFormat("pt-BR");
const price = new Intl.NumberFormat("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 8 });

export const format = {
  quantity: (value: number) => quantity.format(value),
  price: (value: string) => price.format(Number(value)),
  date: (iso: string) => iso.split("-").reverse().join("/"),
  cnpj: (digits: string) =>
    digits.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/, "$1.$2.$3/$4-$5"),
};

export const today = () => new Date().toLocaleDateString("sv-SE"); // AAAA-MM-DD no fuso local

/** Datas (AAAA-MM-DD) entre start e end, inclusive, amostradas pra no máximo maxPoints. */
export function datesBetween(start: string, end: string, maxPoints = 30): string[] {
  const startDate = new Date(`${start}T00:00:00`);
  const endDate = new Date(`${end}T00:00:00`);
  const totalDays = Math.round((endDate.getTime() - startDate.getTime()) / 86_400_000) + 1;
  if (totalDays <= 0) return [];
  const step = Math.max(1, Math.ceil(totalDays / maxPoints));
  const dates: string[] = [];
  for (let offset = 0; offset < totalDays; offset += step) {
    const d = new Date(startDate);
    d.setDate(d.getDate() + offset);
    dates.push(d.toLocaleDateString("sv-SE"));
  }
  if (dates[dates.length - 1] !== end) dates.push(end);
  return dates;
}
