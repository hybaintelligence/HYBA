import React, { useEffect, useRef, useState } from "react";
import * as d3 from "d3";

interface DataPoint {
  time: Date;
  coherence: number;
  resonance: number;
}

interface CoherenceScatterPlotProps {
  coherence: number;
  resonance: number;
  className?: string;
}

export const CoherenceScatterPlot: React.FC<CoherenceScatterPlotProps> = ({ coherence, resonance, className }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [data, setData] = useState<DataPoint[]>([]);

  // Periodically add data
  useEffect(() => {
    setData(prev => {
      const nuData = [...prev, { time: new Date(), coherence, resonance }];
      return nuData.slice(-50); // Keep last 50 points
    });
  }, [coherence, resonance]);

  // D3 Render Effect
  useEffect(() => {
    if (!containerRef.current || data.length === 0) return;

    const width = containerRef.current.clientWidth;
    const height = 240;
    const margin = { top: 20, right: 30, bottom: 40, left: 50 };

    // Clear previous SVG
    d3.select(containerRef.current).select("svg").remove();

    const svg = d3.select(containerRef.current)
      .append("svg")
      .attr("width", width)
      .attr("height", height)
      .append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);

    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    // Scales
    const xScale = d3.scaleTime()
      .domain(d3.extent(data, (d: DataPoint) => d.time) as [Date, Date])
      .range([0, innerWidth]);

    const yScale = d3.scaleLinear()
      .domain([0, 1]) // Both coherence and resonance are generally between 0 and 1
      .range([innerHeight, 0]);

    // Axes
    const xAxis = d3.axisBottom(xScale).ticks(5);
    const yAxis = d3.axisLeft(yScale).ticks(5);

    svg.append("g")
      .attr("transform", `translate(0,${innerHeight})`)
      .call(xAxis)
      .attr("class", "text-[10px] font-mono text-[#64748B]");

    svg.append("g")
      .call(yAxis)
      .attr("class", "text-[10px] font-mono text-[#64748B]");

    // X Axis Label
    svg.append("text")
      .attr("x", innerWidth / 2)
      .attr("y", innerHeight + 30)
      .style("text-anchor", "middle")
      .attr("class", "text-[10px] font-mono fill-[#64748B]")
      .text("Time");

    // Y Axis Label
    svg.append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", -40)
      .attr("x", -innerHeight / 2)
      .style("text-anchor", "middle")
      .attr("class", "text-[10px] font-mono fill-[#64748B]")
      .text("Value Band");

    // Plot Coherence points (Blue)
    svg.append("g")
      .selectAll("dot")
      .data(data)
      .enter()
      .append("circle")
      .attr("cx", (d: any) => xScale(d.time))
      .attr("cy", (d: any) => yScale(d.coherence))
      .attr("r", 4)
      .style("fill", "#0A5C91")
      .style("opacity", 0.7);

    // Plot Resonance points (Orange)
    svg.append("g")
      .selectAll("dot")
      .data(data)
      .enter()
      .append("circle")
      .attr("cx", (d: any) => xScale(d.time))
      .attr("cy", (d: any) => yScale(d.resonance))
      .attr("r", 4)
      .style("fill", "#e36c0a")
      .style("opacity", 0.7);

  }, [data]);

  return (
    <div className={`bg-white border border-[#E2E4E9] rounded-xl p-5 shadow-sm ${className || ''}`}>
      <div className="flex items-center justify-between mb-4">
        <h4 className="text-xs font-mono text-[#1A1A1E] font-bold uppercase tracking-wider">
          Coherence vs Φ-Resonance Banding
        </h4>
        <div className="flex space-x-3 text-[10px] font-mono font-bold uppercase">
           <div className="flex items-center space-x-1">
              <span className="w-2 h-2 rounded-full bg-[#0A5C91]"></span>
              <span className="text-[#64748B]">Coherence</span>
           </div>
           <div className="flex items-center space-x-1">
              <span className="w-2 h-2 rounded-full bg-[#e36c0a]"></span>
              <span className="text-[#64748B]">Resonance</span>
           </div>
        </div>
      </div>
      <div ref={containerRef} className="w-full h-[240px]" />
    </div>
  );
};
