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
