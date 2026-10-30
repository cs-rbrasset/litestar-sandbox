import { TradesPanel } from "../../src/components/trades.tsx";
import { DEFAULT_FUND } from "../../src/constants.ts";

export default function BoletasPage() {
  return <TradesPanel defaultFund={DEFAULT_FUND} />;
}
