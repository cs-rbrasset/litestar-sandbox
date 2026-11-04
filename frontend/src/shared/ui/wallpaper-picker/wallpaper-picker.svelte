<script lang="ts">
	import Check from "@lucide/svelte/icons/check";

	import { cn } from "#shared/lib/utils.js";
	import { wallpaper, WALLPAPERS } from "#shared/lib/wallpaper.svelte.js";

	let { showLabels = false, class: className }: { showLabels?: boolean; class?: string } = $props();
</script>

<div class={cn("grid grid-cols-2 gap-2", className)}>
	{#each WALLPAPERS as option (option.id)}
		<button type="button" onclick={() => wallpaper.set(option.id)} title={option.label} class="group flex flex-col gap-1.5 text-left">
			<span
				class={cn(
					"ring-foreground/10 relative block aspect-video overflow-hidden rounded-lg ring-1 transition group-hover:ring-brand-500/60",
					wallpaper.selectedId === option.id && "ring-2 ring-brand-500 group-hover:ring-brand-500",
				)}
			>
				<img src={option.src} alt="" class="size-full object-cover" />
				{#if wallpaper.selectedId === option.id}
					<span class="bg-brand-500 absolute top-1.5 right-1.5 flex size-5 items-center justify-center rounded-full text-white shadow-sm">
						<Check class="size-3" />
					</span>
				{/if}
			</span>
			{#if showLabels}
				<span class="text-muted-foreground px-0.5 text-xs">{option.label}</span>
			{/if}
		</button>
	{/each}
	<button
		type="button"
		onclick={() => wallpaper.set(null)}
		class={cn(
			"bg-muted text-muted-foreground ring-foreground/10 col-span-2 flex aspect-[4/1] items-center justify-center gap-1.5 rounded-lg text-xs ring-1 transition hover:ring-brand-500/60",
			wallpaper.selectedId === null && "ring-2 ring-brand-500 hover:ring-brand-500",
		)}
	>
		{#if wallpaper.selectedId === null}<Check class="size-3.5" />{/if}
		Nenhum
	</button>
</div>
