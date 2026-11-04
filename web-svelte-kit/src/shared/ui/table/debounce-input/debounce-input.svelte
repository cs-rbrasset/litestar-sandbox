<script lang="ts">
	import SearchIcon from "@lucide/svelte/icons/search";
	import XIcon from "@lucide/svelte/icons/x";
	import { Debounced, watch } from "runed";

	import { InputGroup, InputGroupAddon, InputGroupButton, InputGroupInput } from "#shared/ui/index.ts";

	type Props = {
		value?: string;
		onChange?: (value: string) => void;
		class?: string;
		placeholder?: string;
		debounce?: number;
	};

	let {
		value = $bindable(""),
		onChange,
		class: className,
		placeholder = "Search...",
		debounce = 0
	}: Props = $props();

	let inputValue = $state(value);
	const debouncedValue = new Debounced(
		() => inputValue,
		() => debounce
	);

	watch(
		() => value,
		(nextValue) => {
			if (nextValue === inputValue) return;

			inputValue = nextValue;
			debouncedValue.setImmediately(nextValue);
		},
		{ lazy: true }
	);

	watch(
		() => debouncedValue.current,
		(nextValue) => {
			if (nextValue === value) return;

			value = nextValue;
			onChange?.(nextValue);
		},
		{ lazy: true }
	);

	function clearValue() {
		inputValue = "";
	}
</script>

<InputGroup class={className}>
	<InputGroupAddon align="inline-start">
		<SearchIcon aria-hidden="true" />
	</InputGroupAddon>

	<InputGroupInput bind:value={inputValue} {placeholder} />

	{#if inputValue}
		<InputGroupAddon align="inline-end">
			<InputGroupButton aria-label="Clear search" onclick={clearValue}>
				<XIcon aria-hidden="true" />
			</InputGroupButton>
		</InputGroupAddon>
	{/if}
</InputGroup>
