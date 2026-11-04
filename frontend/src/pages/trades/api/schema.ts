import { z } from "zod";

export const tradeCreateSchema = z.object({
  instrument_id: z.coerce.number().int("Selecione um ativo").positive("Selecione um ativo"),
  fund_cnpj: z
    .string()
    .trim()
    .regex(/^\d{14}$/, "CNPJ deve ter 14 dígitos, sem pontuação"),
  trade_date: z.string().min(1, "Informe a data"),
  side: z.enum(["BUY", "SELL"]),
  quantity: z.coerce.number().int("Quantidade deve ser inteira").positive("Quantidade deve ser maior que zero"),
  unit_price: z
    .string()
    .trim()
    .regex(/^\d+(\.\d{1,8})?$/, "Preço inválido"),
});

export type TradeCreateInput = z.infer<typeof tradeCreateSchema>;
