<script lang="ts">
	import SlidersHorizontalIcon from "@lucide/svelte/icons/sliders-horizontal";

	import {
		Button,
		DropdownMenu,
		DropdownMenuCheckboxItem,
		DropdownMenuContent,
		DropdownMenuLabel,
		DropdownMenuSeparator,
		DropdownMenuTrigger,
	} from "#shared/ui/index.ts";
	import { cn } from "#shared/lib/utils.js";

	type DataTableViewColumn = {
		id: string;
		columnDef?: { header?: unknown };
		getCanHide?: () => boolean;
		getIsVisible?: () => boolean;
		toggleVisibility?: (visible?: boolean) => void;
	};

	type DataTableViewTable = {
		getAllLeafColumns: () => DataTableViewColumn[];
	};

	let {
		table,
		label = "View",
		class: className
	}: {
		table: DataTableViewTable;
		label?: string;
		class?: string;
	} = $props();

	let hideableColumns = $derived(
		table
			.getAllLeafColumns()
			.filter(
				(column) =>
					(column.getCanHide?.() ?? false) &&
					column.getIsVisible !== undefined &&
					column.toggleVisibility !== undefined
			)
	);

	function getColumnLabel(column: DataTableViewColumn) {
		const header = column.columnDef?.header;

		if (typeof header === "string") return header;

		return column.id
			.replace(/([a-z0-9])([A-Z])/g, "$1 $2")
			.replace(/[-_]+/g, " ")
			.replace(/^\w/, (character) => character.toUpperCase());
	}
</script>

<DropdownMenu>
	<DropdownMenuTrigger>
		{#snippet child({ props })}
			<Button
				{...props}
				variant="outline"
				size="sm"
				class={cn("ml-auto", className)}
				disabled={hideableColumns.length === 0}
				aria-label={`${label}: choose visible columns`}
			>
				<SlidersHorizontalIcon />
				{label}
			</Button>
		{/snippet}
	</DropdownMenuTrigger>

	<DropdownMenuContent align="end" class="w-44">
		<DropdownMenuLabel>Toggle columns</DropdownMenuLabel>
		<DropdownMenuSeparator />

		{#each hideableColumns as column (column.id)}
			<DropdownMenuCheckboxItem
				checked={column.getIsVisible?.() ?? true}
				onCheckedChange={(checked) =>
					column.toggleVisibility?.(checked)}
				closeOnSelect={false}
				class="capitalize"
			>
				{getColumnLabel(column)}
			</DropdownMenuCheckboxItem>
		{/each}
	</DropdownMenuContent>
</DropdownMenu>
