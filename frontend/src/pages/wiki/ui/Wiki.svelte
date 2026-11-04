<script lang="ts">
  import { generateHTML } from "@tiptap/core";

  import { Card, CardContent, CardHeader, CardTitle, getDefaultExtensions, Loading } from "#shared/ui/index.ts";
  import "#shared/ui/edra/shadcn/editor.css";

  import { useWikiEntries } from "../api/wiki.ts";

  const entries = useWikiEntries();
  const extensions = getDefaultExtensions({ undoRedo: false });

  function toHtml(content: Record<string, unknown>): string | null {
    if (!content || typeof content.type !== "string") return null;
    return generateHTML(content as Parameters<typeof generateHTML>[0], extensions);
  }

  function formatUpdatedAt(iso: string): string {
    return new Date(iso).toLocaleString("pt-BR");
  }
</script>

<div class="flex flex-col gap-4">
  <h1 class="text-xl font-semibold">Wiki</h1>

  {#if entries.isLoading}
    <Loading label="Carregando wiki" />
  {:else if (entries.data?.length ?? 0) === 0}
    <p class="text-muted-foreground py-8 text-center text-sm">
      Ninguém publicou nada na wiki ainda.
    </p>
  {:else}
    {#each entries.data ?? [] as entry (entry.id)}
      {@const html = toHtml(entry.content)}
      <Card>
        <CardHeader>
          <CardTitle>{entry.title}</CardTitle>
          <p class="text-muted-foreground text-xs">
            Por {entry.author_name}
            {#if entry.updated_at}
              · Atualizado em {formatUpdatedAt(entry.updated_at)}
            {/if}
          </p>
        </CardHeader>
        <CardContent>
          {#if html}
            <div class="tiptap">{@html html}</div>
          {:else}
            <p class="text-muted-foreground text-sm">Nota vazia.</p>
          {/if}
        </CardContent>
      </Card>
    {/each}
  {/if}
</div>
