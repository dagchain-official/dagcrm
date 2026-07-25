import { GraduationCap } from "lucide-react";
import TabHub from "../components/TabHub";

// Training & Learning — the catalogue, each employee's plan, and assessments.
export default function TrainingHub() {
  return <TabHub title="Training & Learning" icon={GraduationCap} tabs={[
    { k: "modules", l: "Modules", resource: "training-modules" },
    { k: "assignments", l: "Assignments", resource: "training-assignments" },
    { k: "assessments", l: "Assessments", resource: "assessments" },
  ]} />;
}
