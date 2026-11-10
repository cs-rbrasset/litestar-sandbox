import type { StorybookConfig } from '@storybook/sveltekit';

const config: StorybookConfig = {
  "stories": [
    "../src/**/*.mdx",
    "../src/**/*.stories.@(js|ts|svelte)"
  ],
  "addons": [
    "@storybook/addon-svelte-csf",
    // @storybook/addon-a11y: desligado. Com ele ativo (testado em 10.6.5 e 10.6.7, mesmo
    // comportamento), o processo do Storybook trava em loop (~1 núcleo a 100%, sem nunca
    // terminar) assim que QUALQUER story é aberta, mesmo uma sem nenhuma edição nossa — não é
    // conteúdo de story, é o addon em si com esse stack (Svelte 5 + @storybook/sveltekit nesse
    // Windows). Religar exige investigar a fundo (bisect de versão/plataforma) antes.
    "@storybook/addon-docs"
  ],
  // docgen:false — o docgen do @storybook/sveltekit usa o compilador TypeScript pra resolver
  // a árvore de imports de cada componente (bits-ui etc.) e extrair a tabela de props. Nesta
  // máquina isso trava: cada stat/exists do resolvedor de módulos passa pelo antivírus
  // corporativo (Sophos, visível no profile do V8 injetado no processo node), e a varredura
  // nunca termina em tempo viável (minutos presa em ntdll.dll/SophosED.dll). Sem docgen o
  // Storybook sobe normal; perdemos só a tabela de props automática nos Docs.
  "framework": { "name": "@storybook/sveltekit", "options": { "docgen": false } },
  // Cada story importa um conjunto diferente de sub-módulos de bits-ui/@lucide/svelte;
  // sem isso o Vite descobre deps novas aos poucos e força re-otimização (reload) a cada
  // story nova. Pré-listar aqui faz o Vite bundlar tudo de uma vez no boot.
  async viteFinal(viteConfig) {
    viteConfig.optimizeDeps ??= {};
    viteConfig.optimizeDeps.include = [
      ...(viteConfig.optimizeDeps.include ?? []),
      "bits-ui",
      "@lucide/svelte",
      "paneforge",
      "vaul-svelte",
      "svelte-number-format",
      "tailwind-variants",
      "clsx",
      "tailwind-merge",
    ];
    return viteConfig;
  },
};
export default config;