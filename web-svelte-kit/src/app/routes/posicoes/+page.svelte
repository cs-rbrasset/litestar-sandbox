<script lang="ts">
  import { DEFAULT_FUND } from "#shared/config/index.ts";
  import { Positions, PositionsHistoryChart, PositionsReport } from "#pages/positions/index.ts";
</script>

<div class="flex flex-col gap-6">
  <Positions defaultFund={DEFAULT_FUND} />
  <PositionsHistoryChart defaultFund={DEFAULT_FUND} />
  <PositionsReport defaultFund={DEFAULT_FUND} />
</div>
