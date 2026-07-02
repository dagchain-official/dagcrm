import { Settings2 } from "lucide-react";
import TabHub from "../components/TabHub";

export default function ConfigHub() {
  return <TabHub title="Configuration" icon={Settings2} tabs={[
    { k: "businesses", l: "Businesses", resource: "businesses" },
    { k: "products", l: "Products", resource: "products" },
    { k: "metrics", l: "KPI Definitions", resource: "metric-definitions" },
    { k: "sources", l: "Lead Sources", resource: "lead-sources" },
  ]} />;
}
