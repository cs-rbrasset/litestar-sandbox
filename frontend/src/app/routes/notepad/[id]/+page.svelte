<script lang="ts">
  import { page } from "$app/state";

  import { NotepadEditor } from "#pages/notepad/index.ts";
</script>

{#key page.params.id}
  <NotepadEditor id={Number(page.params.id)} />
{/key}
