import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { YearlyProjection } from "../../types";

interface Props {
  data: YearlyProjection[];
}

function fmtK(v: number): string {
  return `$${(v / 1000).toFixed(0)}k`;
}

export default function EquityBuildupChart({ data }: Props) {
  const chartData = data.map((row) => ({
    year: row.year,
    equity: Math.round(row.equity),
    loan_balance: Math.round(row.loan_balance),
  }));

  return (
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart
        data={chartData}
        margin={{ top: 4, right: 8, left: 0, bottom: 0 }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
        <XAxis dataKey="year" tick={{ fontSize: 11 }} />
        <YAxis tickFormatter={fmtK} tick={{ fontSize: 11 }} width={44} />
        <Tooltip
          formatter={(value) => [`$${Number(value).toLocaleString()}`, ""]}
          labelFormatter={(label) => `Year ${label}`}
        />
        <Area
          type="monotone"
          dataKey="loan_balance"
          stackId="1"
          fill="#fde68a"
          stroke="#f59e0b"
          name="Loan Balance"
        />
        <Area
          type="monotone"
          dataKey="equity"
          stackId="1"
          fill="#bbf7d0"
          stroke="#22c55e"
          name="Equity"
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
