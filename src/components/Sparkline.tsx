import React from "react";
import { LineChart, Line, YAxis, ResponsiveContainer } from "recharts";

interface SparklineProps {
  data: { time: string; latency: number }[];
}

export const Sparkline: React.FC<SparklineProps> = ({ data }) => {
  return (
    <div className="w-24 h-6 opacity-80 flex items-center shrink-0">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <YAxis domain={["dataMin", "dataMax"]} hide />
          <Line
            type="monotone"
            dataKey="latency"
            stroke="#0A5C91"
            strokeWidth={2}
            dot={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};
