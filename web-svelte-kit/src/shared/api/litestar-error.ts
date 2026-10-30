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
