<script lang="ts">
  import { goto } from "$app/navigation";
  import { ArrowLeft, Globe, Lock, Save, Trash2 } from "@lucide/svelte";

  import { describeError } from "#shared/api/index.ts";
  import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
    AlertDialogTrigger,
    Button,
    Card,
    CardContent,
    CardHeader,
    createEditor,
    Edra,
    Input,
    Loading,
    Switch,
  } from "#shared/ui/index.ts";
  import { notify } from "#shared/ui/toast/index.ts";

  import { useDeleteNote, useNote, useSaveNote } from "../api/notes.ts";

  let { id }: { id: number } = $props();

  const note = useNote(() => id);
  const save = useSaveNote(() => id);
  const del = useDeleteNote();

  let hydrated = false;
  let title = $state("");
  let published = $state(false);

  const editor = createEditor();

  // content só vira um doc Tiptap de verdade depois do primeiro save; antes disso é "{}"
  // (NoteRead.content default do backend) — setContent nisso quebraria o editor.
  $effect(() => {
    if (hydrated || !editor || !note.data) return;
    if (note.data.content && typeof note.data.content.type === "string") {
      editor.commands.setContent(note.data.content, { emitUpdate: false });
    }
    title = note.data.title;
    published = note.data.published ?? false;
    hydrated = true;
  });

  function saveNow() {
    if (!editor) return;
    save.mutate(
      { title, content: editor.getJSON() as Record<string, unknown>, published },
      {
        onSuccess: () => notify("Artigo salvo"),
        onError: (error) => notify(describeError(error), true),
      },
    );
  }

  function deleteNow() {
    del.mutate(id, {
      onSuccess: () => {
        notify("Artigo excluído");
        goto("/notepad");
      },
      onError: (error) => notify(describeError(error), true),
    });
  }
</script>

<div class="flex flex-col gap-4">
  <div class="flex items-center justify-between">
    <Button href="/notepad" variant="ghost" size="sm" class="w-fit">
      <ArrowLeft data-icon="inline-start" />
      Meus artigos
    </Button>
    <div class="flex items-center gap-2">
      <AlertDialog>
        <AlertDialogTrigger>
          {#snippet child({ props })}
            <Button {...props} variant="ghost" size="sm" disabled={!note.data || del.isPending}>
              <Trash2 data-icon="inline-start" />
              Excluir
            </Button>
          {/snippet}
        </AlertDialogTrigger>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Excluir "{title}"?</AlertDialogTitle>
            <AlertDialogDescription>Essa ação não pode ser desfeita.</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Voltar</AlertDialogCancel>
            <AlertDialogAction variant="destructive" onclick={deleteNow}>Excluir artigo</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
      <Button onclick={saveNow} disabled={!note.data || save.isPending}>
        <Save data-icon="inline-start" />
        {save.isPending ? "Salvando…" : "Salvar"}
      </Button>
    </div>
  </div>

  <Card>
    <CardHeader>
      {#if !note.data}
        <Loading label="Carregando artigo" />
      {:else}
        <div class="flex flex-wrap items-center justify-between gap-3">
          <Input
            bind:value={title}
            placeholder="Título do artigo"
            class="h-auto border-none px-0 text-lg font-semibold shadow-none focus-visible:ring-0"
          />
          <div class="bg-muted/50 flex items-center gap-2 rounded-md border px-3 py-1.5">
            {#if published}
              <Globe class="text-muted-foreground size-4" />
            {:else}
              <Lock class="text-muted-foreground size-4" />
            {/if}
            <span class="text-sm font-medium whitespace-nowrap">
              {published ? "Publicado na wiki" : "Rascunho"}
            </span>
            <Switch bind:checked={published} />
          </div>
        </div>
      {/if}
    </CardHeader>
    <CardContent>
      {#if note.data}
        <div class="min-h-[60vh] rounded-lg border px-8 py-6">
          <Edra {editor}>
            <Edra.Toolbar />
            <Edra.BubbleMenu />
            <Edra.Content />
            <Edra.DragHandle />
          </Edra>
        </div>
      {/if}
    </CardContent>
  </Card>
</div>
