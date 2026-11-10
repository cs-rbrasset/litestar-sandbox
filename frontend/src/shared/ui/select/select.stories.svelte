<script module lang="ts">
  import { defineMeta } from "@storybook/addon-svelte-csf";
  import Root from "./select.svelte";
  import Content from "./select-content.svelte";
  import Item from "./select-item.svelte";
  import Trigger from "./select-trigger.svelte";
  import Value from "./select-value.svelte";

  // Mesmo formato da lista de ativos em Trades.svelte: `label` curto no trigger, nome completo no item.
  const INSTRUMENTS = [
    { id: 1, cetip_code: "CDB123", name: "CDB Banco Alfa 110% CDI" },
    { id: 2, cetip_code: "LCA456", name: "LCA Banco Beta 95% CDI" },
    { id: 3, cetip_code: "DEB789", name: "Debênture Gama IPCA+6%" },
  ];

  const { Story } = defineMeta({
    title: "UI/Select",
    component: Root,
    tags: ["autodocs"],
    argTypes: {
      disabled: { control: "boolean" },
    },
    args: { disabled: false },
  });
</script>

<!-- Lado da boleta, como no formulário de Trades.svelte. -->
<Story name="Playground">
  {#snippet template(args)}
    <Root type="single" value="BUY" disabled={args.disabled}>
      <Trigger class="w-48" aria-label="Lado">
        <Value placeholder="Selecione o lado" />
      </Trigger>
      <Content>
        <Item value="BUY">Compra</Item>
        <Item value="SELL">Venda</Item>
      </Content>
    </Root>
  {/snippet}
</Story>

<!-- Sem valor inicial: o placeholder aparece até escolher. `label` controla o texto do trigger. -->
<Story name="Com placeholder">
  {#snippet template(args)}
    <Root type="single" disabled={args.disabled}>
      <Trigger class="w-64" aria-label="Ativo">
        <Value placeholder="Cadastre um ativo primeiro" />
      </Trigger>
      <Content>
        {#each INSTRUMENTS as i (i.id)}
          <Item value={String(i.id)} label={i.cetip_code}>{i.cetip_code} · {i.name}</Item>
        {/each}
      </Content>
    </Root>
  {/snippet}
</Story>

<!-- `SelectTrigger size="sm"`: a única outra altura que o trigger tem. -->
<Story name="Compacto">
  {#snippet template(args)}
    <Root type="single" value="BUY" disabled={args.disabled}>
      <Trigger class="w-40" size="sm" aria-label="Lado">
        <Value placeholder="Selecione o lado" />
      </Trigger>
      <Content>
        <Item value="BUY">Compra</Item>
        <Item value="SELL">Venda</Item>
      </Content>
    </Root>
  {/snippet}
</Story>
