import { TrendingUp, Landmark, Scale } from "lucide-react";
import TabHub from "../components/TabHub";
import PnL from "./PnL";
import AumBoard from "./AumBoard";
import ContributionBoard from "./ContributionBoard";

export function FinanceHub() {
  return <TabHub title="Finance" icon={TrendingUp} tabs={[
    { k: "pnl", l: "P&L Statement", element: <PnL /> },
    { k: "expenses", l: "Expenses", resource: "expenses" },
    { k: "commissions", l: "Commissions", resource: "commissions" },
  ]} />;
}

export function AumHub() {
  return <TabHub title="AUM" icon={Landmark} tabs={[
    { k: "board", l: "AUM Board", element: <AumBoard /> },
    { k: "entries", l: "AUM Entries", resource: "aum-entries" },
  ]} />;
}

export function ContributionHub() {
  return <TabHub title="Business Contribution" icon={Scale} tabs={[
    { k: "board", l: "Contribution Board", element: <ContributionBoard /> },
    { k: "entries", l: "Contribution Entries", resource: "contribution-entries" },
    { k: "formula", l: "Contribution Formula", resource: "contribution-weights" },
  ]} />;
}
