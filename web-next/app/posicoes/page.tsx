import { PositionsPanel } from "../../src/components/positions.tsx";
import { PositionsReportPanel } from "../../src/components/positions-report.tsx";
import { DEFAULT_FUND } from "../../src/constants.ts";

export default function PosicoesPage() {
  return (
    <div className="flex flex-col gap-6">
      <PositionsPanel defaultFund={DEFAULT_FUND} />
      <PositionsReportPanel defaultFund={DEFAULT_FUND} />
    </div>
  );
}
