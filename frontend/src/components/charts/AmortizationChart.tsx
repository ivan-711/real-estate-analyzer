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

export default function AmortizationChart({ data }: Props) {
  const chartData = data.map((row) => ({
    year: row.year,
    interest_paid: Math.round(row.interest_paid),
    principal_paid: Math.round(row.principal_paid),
  }));

  return (
    <ResponsiveContainer width="100%" height={220}>
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
          dataKey="interest_paid"
          stackId="1"
          fill="#fed7aa"
          stroke="#f97316"
          name="Interest Paid"
        />
        <Area
          type="monotone"
          dataKey="principal_paid"
          stackId="1"
          fill="#99f6e4"
          stroke="#14b8a6"
          name="Principal Paid"
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
