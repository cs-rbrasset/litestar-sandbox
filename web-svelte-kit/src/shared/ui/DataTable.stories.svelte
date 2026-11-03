<script module lang="ts">
  import { defineMeta } from "@storybook/addon-svelte-csf";
  import { createColumnHelper } from "@tanstack/svelte-table";
  import DataTable, { features } from "./DataTable.svelte";

  const { Story } = defineMeta({
    title: "UI/DataTable",
    component: DataTable,
    tags: ["autodocs"],
  });

  type Row = { id: number; ativo: string; quantidade: number; preco: string };

  const helper = createColumnHelper<typeof features, Row>();
  const columns = [
    helper.accessor("ativo", { header: "Ativo" }),
    helper.accessor("quantidade", { header: "Qtd." }),
    helper.accessor("preco", { header: "Preço" }),
  ];

  const data: Row[] = [
    { id: 1, ativo: "CDB123", quantidade: 100, preco: "101,25" },
    { id: 2, ativo: "LCA456", quantidade: 50, preco: "998,00" },
  ];
</script>

<!-- numericColumnIds alinha cabeçalho e célula à direita — é o único "feature" que o
  DataTable expõe além da renderização padrão do tanstack table (mesmo uso de Trades.svelte).
  Story não carrega os generics do DataTable (TData); `as any` só pra calar o typecheck. -->
<Story
  name="Playground"
  args={{ columns, data, numericColumnIds: ["quantidade", "preco"] } as any}
/>
