import {
  Activity,
  BadgeIndianRupee,
  Banknote,
  BarChart3,
  BriefcaseBusiness,
  ClipboardCheck,
  FileBarChart,
  HardHat,
  LayoutDashboard,
  MapPinned,
  ReceiptText,
  UsersRound,
} from "lucide-react";

export const navItems = [
  { title: "Dashboard", href: "/", icon: LayoutDashboard },
  { title: "Workers", href: "/workers", icon: UsersRound },
  { title: "Sites", href: "/sites", icon: MapPinned },
  { title: "Attendance", href: "/attendance", icon: ClipboardCheck },
  { title: "Payroll", href: "/payroll", icon: Banknote },
  { title: "Expenses", href: "/expenses", icon: ReceiptText },
  { title: "Reports", href: "/reports", icon: FileBarChart },
];

export const dashboardMetrics = [
  { label: "Active workers", value: "1,284", delta: "+8.4%", icon: HardHat, tone: "mint" },
  { label: "Present today", value: "1,091", delta: "84.9%", icon: ClipboardCheck, tone: "amber" },
  { label: "Payroll pending", value: "₹18.7L", delta: "-12%", icon: BadgeIndianRupee, tone: "clay" },
  { label: "Open sites", value: "42", delta: "+3", icon: BriefcaseBusiness, tone: "ink" },
];

export const labourFlow = [
  { label: "Attendance captured", value: 86 },
  { label: "Supervisor review", value: 64 },
  { label: "Payroll draft", value: 42 },
  { label: "Finance payout", value: 29 },
];

export const activityFeed = [
  "Mahadev Infra uploaded attendance for Metro Yard",
  "Payroll draft generated for June 2026",
  "Advance payment logged for 18 workers",
  "North Pier expenses moved to approval",
];

export const workers = [
  { code: "WRK-1042", name: "Ravi Kumar", trade: "Mason", site: "Metro Yard", wage: "₹850", status: "Active" },
  { code: "WRK-1043", name: "Sanjay Patel", trade: "Bar Bender", site: "North Pier", wage: "₹920", status: "Active" },
  { code: "WRK-1044", name: "Meena Devi", trade: "Painter", site: "Lakeview Towers", wage: "₹780", status: "On Leave" },
  { code: "WRK-1045", name: "Iqbal Khan", trade: "Electrician", site: "Depot Block C", wage: "₹1,050", status: "Active" },
];

export const sites = [
  { code: "SIT-021", name: "Metro Yard", city: "Pune", manager: "Asha Nair", workers: 312, status: "Active" },
  { code: "SIT-022", name: "North Pier", city: "Mumbai", manager: "Vikram Rao", workers: 188, status: "Active" },
  { code: "SIT-023", name: "Lakeview Towers", city: "Nashik", manager: "Ritika Shah", workers: 94, status: "Delayed" },
  { code: "SIT-024", name: "Depot Block C", city: "Thane", manager: "Farhan Ali", workers: 141, status: "Active" },
];

export const attendanceRows = [
  { date: "14 Jun", site: "Metro Yard", present: 286, absent: 18, halfDay: 8, ot: "126h", status: "Draft" },
  { date: "14 Jun", site: "North Pier", present: 171, absent: 11, halfDay: 6, ot: "72h", status: "Review" },
  { date: "13 Jun", site: "Lakeview Towers", present: 82, absent: 9, halfDay: 3, ot: "28h", status: "Approved" },
  { date: "13 Jun", site: "Depot Block C", present: 133, absent: 5, halfDay: 3, ot: "44h", status: "Approved" },
];

export const payrollRows = [
  { period: "June 2026", workers: 1184, gross: "₹72.4L", advance: "₹8.2L", paid: "₹45.5L", pending: "₹18.7L" },
  { period: "May 2026", workers: 1161, gross: "₹68.8L", advance: "₹7.9L", paid: "₹60.9L", pending: "₹0" },
  { period: "April 2026", workers: 1128, gross: "₹65.2L", advance: "₹6.6L", paid: "₹58.6L", pending: "₹0" },
];

export const expenseRows = [
  { site: "Metro Yard", category: "Tools", amount: "₹1.8L", owner: "Asha Nair", status: "Approved" },
  { site: "North Pier", category: "Material", amount: "₹4.2L", owner: "Vikram Rao", status: "Review" },
  { site: "Lakeview Towers", category: "Transport", amount: "₹86K", owner: "Ritika Shah", status: "Draft" },
  { site: "Depot Block C", category: "Safety", amount: "₹1.1L", owner: "Farhan Ali", status: "Paid" },
];

export const reportCards = [
  { title: "Worker-wise Payroll", metric: "1,184 rows", icon: UsersRound, accent: "clay" },
  { title: "Site-wise Expense", metric: "42 sites", icon: ReceiptText, accent: "amber" },
  { title: "Attendance Summary", metric: "29 days", icon: Activity, accent: "mint" },
  { title: "Monthly Payroll", metric: "₹72.4L gross", icon: BarChart3, accent: "ink" },
];
