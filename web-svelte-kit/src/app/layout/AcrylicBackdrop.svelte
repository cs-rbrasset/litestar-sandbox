<script lang="ts">
  import { wallpaper } from "#shared/lib/wallpaper.svelte.ts";
</script>

<!-- plano de fundo fixo atrás de tudo: dá cor pro blur do vidro fosco (card/popover/
     sidebar translúcidos em app.css) ler como acrílico. Imagem escolhida pelo usuário
     em WallpaperPicker, persistida em #shared/lib/wallpaper.svelte.ts. -->
<div class="pointer-events-none fixed inset-0 -z-10 bg-background">
  {#if wallpaper.selected}
    <img
      src={wallpaper.selected.src}
      alt=""
      class="size-full object-cover opacity-70 dark:opacity-50"
    />
  {/if}
</div>
