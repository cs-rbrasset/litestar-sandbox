/** Erro da API no formato do Litestar: {status_code, detail, extra}. */
export class ApiError extends Error {
  readonly status: number;
  readonly fields: string[];

  constructor(status: number, detail: string, fields: string[]) {
    super(detail);
    this.status = status;
    this.fields = fields;
  }
}

type SdkResult<T> = { data?: T; error?: unknown; response?: Response };

type LitestarError = {
  detail?: string;
  extra?: Array<{ key?: string; message?: string }> | Record<string, unknown> | null;
};

/** Desembrulha a resposta do SDK gerado: devolve os dados ou lança ApiError. */
export async function unwrap<T>(call: Promise<SdkResult<T>>): Promise<T> {
  const { data, error, response } = await call;
  if (error === undefined && response?.ok) {
    return data as T;
  }
  const body = (error ?? {}) as LitestarError;
  const fields = Array.isArray(body.extra)
    ? body.extra.map((e) => [e.key, e.message].filter(Boolean).join(": "))
    : [];
  throw new ApiError(response?.status ?? 0, body.detail ?? "Erro inesperado", fields);
}

export function describeError(error: unknown): string {
  if (error instanceof ApiError) {
    const head = `${error.status} · ${error.message}`;
    return error.fields.length ? `${head}\n${error.fields.join("\n")}` : head;
  }
  return error instanceof Error ? error.message : String(error);
}

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
