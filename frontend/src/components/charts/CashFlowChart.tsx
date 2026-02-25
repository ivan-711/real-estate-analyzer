import {
  Bar,
  CartesianGrid,
  Cell,
  ComposedChart,
  Line,
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

export default function CashFlowChart({ data }: Props) {
  const chartData = data.map((row) => ({
    year: row.year,
    annual_net_cash_flow: Math.round(row.annual_net_cash_flow),
    cumulative_cash_flow: Math.round(row.cumulative_cash_flow),
  }));

  return (
    <ResponsiveContainer width="100%" height={220}>
      <ComposedChart
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
        <Bar
          dataKey="annual_net_cash_flow"
          name="Annual Cash Flow"
          radius={[2, 2, 0, 0]}
        >
          {chartData.map((entry, i) => (
            <Cell
              key={i}
              fill={entry.annual_net_cash_flow >= 0 ? "#22c55e" : "#ef4444"}
            />
          ))}
        </Bar>
        <Line
          type="monotone"
          dataKey="cumulative_cash_flow"
          stroke="#3b82f6"
          strokeWidth={2}
          dot={false}
          name="Cumulative Cash Flow"
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
