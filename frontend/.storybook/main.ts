import type { StorybookConfig } from '@storybook/sveltekit';

const config: StorybookConfig = {
  "stories": [
    "../src/**/*.mdx",
    "../src/**/*.stories.@(js|ts|svelte)"
  ],
  "addons": [
    "@storybook/addon-svelte-csf",
    "@storybook/addon-a11y",
    "@storybook/addon-docs"
  ],
  "framework": "@storybook/sveltekit",
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