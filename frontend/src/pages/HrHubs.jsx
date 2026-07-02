import { Briefcase, Clock, Wallet, Award, Wand2 } from "lucide-react";
import TabHub from "../components/TabHub";
import IncentiveBoard from "./IncentiveBoard";
import FormulaBuilder from "./FormulaBuilder";
import FormulaBoard from "./FormulaBoard";

export function PeopleHub() {
  return <TabHub title="People" icon={Briefcase} tabs={[
    { k: "employees", l: "Employees", resource: "employees" },
    { k: "departments", l: "Departments", resource: "departments" },
    { k: "levels", l: "Hierarchy Levels", resource: "hierarchy-levels" },
  ]} />;
}

export function AttendanceHub() {
  return <TabHub title="Attendance & Leave" icon={Clock} tabs={[
    { k: "attendance", l: "Attendance", resource: "attendance" },
    { k: "activity", l: "Activity Tracking", resource: "employee-activities" },
    { k: "leaves", l: "Leaves", resource: "leaves" },
    { k: "leave-types", l: "Leave Types", resource: "leave-types" },
  ]} />;
}

export function CostHub() {
  return <TabHub title="Cost & CTC" icon={Wallet} tabs={[
    { k: "categories", l: "Cost Categories", resource: "cost-categories" },
    { k: "costs", l: "Employee Costs", resource: "employee-costs" },
  ]} />;
}

export function PayrollHub() {
  return <TabHub title="Payroll & Incentives" icon={Award} tabs={[
    { k: "payroll", l: "Payroll", resource: "payrolls" },
    { k: "incentives", l: "Incentives", resource: "incentives" },
    { k: "board", l: "Incentive Board", element: <IncentiveBoard /> },
    { k: "slabs", l: "Incentive Slabs", resource: "incentive-slabs" },
    { k: "activity", l: "Activity Incentives", resource: "activity-incentives" },
    { k: "rules", l: "Incentive Rules", resource: "incentive-rules" },
  ]} />;
}

export function RulesHub() {
  return <TabHub title="Rules & Config" icon={Wand2} tabs={[
    { k: "formula", l: "Formula Builder", element: <FormulaBuilder /> },
    { k: "payouts", l: "Formula Payouts", element: <FormulaBoard /> },
    { k: "multipliers", l: "Target Multipliers", resource: "target-multipliers" },
    { k: "weights", l: "Performance Weights", resource: "performance-weights" },
  ]} />;
}
