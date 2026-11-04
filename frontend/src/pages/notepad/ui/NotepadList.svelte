<script lang="ts">
  import { goto } from "$app/navigation";
  import { Plus } from "@lucide/svelte";

  import { Badge, Button, Card, CardContent, CardHeader, CardTitle, Loading } from "#shared/ui/index.ts";

  import { useCreateNote, useMyNotes } from "../api/notes.ts";

  const notes = useMyNotes();
  const create = useCreateNote();

  function newArticle() {
    create.mutate("Sem título", {
      onSuccess: (note) => goto(`/notepad/${note.id}`),
    });
  }

  function formatUpdatedAt(iso: string): string {
    return new Date(iso).toLocaleString("pt-BR");
  }
</script>

<div class="flex flex-col gap-4">
  <div class="flex items-center justify-between">
    <h1 class="text-xl font-semibold">Meus artigos</h1>
    <Button onclick={newArticle} disabled={create.isPending}>
      <Plus data-icon="inline-start" />
      Novo artigo
    </Button>
  </div>

  {#if notes.isLoading}
    <Loading label="Carregando artigos" />
  {:else if (notes.data?.length ?? 0) === 0}
    <p class="text-muted-foreground py-8 text-center text-sm">
      Você ainda não criou nenhum artigo.
    </p>
  {:else}
    <div class="flex flex-col gap-2">
      {#each notes.data ?? [] as note (note.id)}
        <a href={`/notepad/${note.id}`} class="block">
          <Card class="transition-colors hover:bg-accent/50">
            <CardHeader>
              <CardTitle class="flex items-center gap-2 text-base">
                {note.title}
                {#if note.published}
                  <Badge>Publicado</Badge>
                {:else}
                  <Badge variant="outline">Rascunho</Badge>
                {/if}
              </CardTitle>
            </CardHeader>
            {#if note.updated_at}
              <CardContent class="text-muted-foreground text-xs">
                Atualizado em {formatUpdatedAt(note.updated_at)}
              </CardContent>
            {/if}
          </Card>
        </a>
      {/each}
    </div>
  {/if}
</div>
