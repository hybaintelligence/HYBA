import React, { useEffect, useRef, useState, useMemo } from "react";
import * as d3 from "d3";
import { motion, AnimatePresence } from "motion/react";
import { Layers, MousePointer2 } from "lucide-react";

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
  const svgRef = useRef<SVGSVGElement>(null);
  const [data, setData] = useState<DataPoint[]>([]);
  const [dimensions, setDimensions] = useState({ width: 0, height: 240 });
  const [zoomTransform, setZoomTransform] = useState<d3.ZoomTransform>(d3.zoomIdentity);
  const [hoveredPoint, setHoveredPoint] = useState<{ point: DataPoint; type: 'coherence' | 'resonance'; x: number; y: number } | null>(null);
  const [viewMode, setViewMode] = useState<'scatter' | 'heatmap'>('scatter');

  const margin = { top: 20, right: 30, bottom: 40, left: 50 };

  // Update dimensions on resize
  useEffect(() => {
    if (!containerRef.current) return;
    const observer = new ResizeObserver((entries) => {
      if (entries[0]) {
        setDimensions({
          width: entries[0].contentRect.width,
          height: 240
        });
      }
    });
    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, []);

  // Periodically add data
  useEffect(() => {
    setData(prev => {
      const nuData = [...prev, { time: new Date(), coherence, resonance }];
      return nuData.slice(-100); // More points for heatmap
    });
  }, [coherence, resonance]);

  const innerWidth = Math.max(0, dimensions.width - margin.left - margin.right);
  const innerHeight = Math.max(0, dimensions.height - margin.top - margin.bottom);

  // Scales calculated with memoization
  const scales = useMemo(() => {
    if (data.length === 0 || innerWidth <= 0) return null;

    const xScale = d3.scaleTime()
      .domain(d3.extent(data, (d: DataPoint) => d.time) as [Date, Date])
      .range([0, innerWidth]);

    const yScale = d3.scaleLinear()
      .domain([0, 1])
      .range([innerHeight, 0]);

    return { xScale, yScale };
  }, [data, innerWidth, innerHeight]);

  // Zoom setup
  useEffect(() => {
    if (!svgRef.current) return;
    const svg = d3.select(svgRef.current);
    
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.5, 10])
      .on("zoom", (event) => {
        setZoomTransform(event.transform);
      });

    svg.call(zoom);
  }, [dimensions]);

  const renderedXScale = useMemo(() => {
    if (!scales) return null;
    return zoomTransform.rescaleX(scales.xScale);
  }, [scales, zoomTransform]);

  const renderedYScale = useMemo(() => {
    if (!scales) return null;
    return zoomTransform.rescaleY(scales.yScale);
  }, [scales, zoomTransform]);

  // Heatmap Contours Calculation
  const contours = useMemo(() => {
    if (viewMode !== 'heatmap' || !scales || data.length < 5) return null;

    const density = d3.contourDensity<DataPoint>()
      .x(d => scales.xScale(d.time))
      .y(d => scales.yScale(d.coherence))
      .size([innerWidth, innerHeight])
      .bandwidth(20)
      .thresholds(10);

    return density(data);
  }, [data, scales, viewMode, innerWidth, innerHeight]);

  return (
    <div className={`bg-white border border-[#E2E4E9] rounded-xl p-5 shadow-sm relative ${className || ''}`}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <h4 className="text-xs font-mono text-[#1A1A1E] font-bold uppercase tracking-wider">
            Coherence vs Φ-Resonance Banding
          </h4>
          <div className="flex border border-[#E2E4E9] rounded-md overflow-hidden">
            <button
              onClick={() => setViewMode('scatter')}
              className={`px-2 py-1 text-[9px] font-mono flex items-center gap-1 transition-colors ${viewMode === 'scatter' ? 'bg-black text-white' : 'bg-white text-gray-500 hover:bg-gray-50'}`}
            >
              <MousePointer2 className="w-2.5 h-2.5" />
              SCATTER
            </button>
            <button
              onClick={() => setViewMode('heatmap')}
              className={`px-2 py-1 text-[9px] font-mono flex items-center gap-1 transition-colors ${viewMode === 'heatmap' ? 'bg-black text-white' : 'bg-white text-gray-500 hover:bg-gray-50'}`}
            >
              <Layers className="w-2.5 h-2.5" />
              HEATMAP
            </button>
          </div>
        </div>
        
        <div className="flex items-center gap-4 text-[10px] font-mono">
           <div className="flex items-center gap-2">
             <span className="w-2 h-2 rounded-full bg-[#0A5C91]" />
             <span className="text-[#64748B]">Coherence</span>
           </div>
           <div className="flex items-center gap-2">
             <span className="w-2 h-2 rounded-full bg-[#e36c0a]" />
             <span className="text-[#64748B]">Resonance</span>
           </div>
        </div>
      </div>

      <div ref={containerRef} className="w-full h-[240px] cursor-move overflow-hidden">
        <svg ref={svgRef} width={dimensions.width} height={dimensions.height}>
          <defs>
            <clipPath id="chart-area-main-v2">
              <rect x={margin.left} y={margin.top} width={innerWidth} height={innerHeight} />
            </clipPath>
          </defs>

          <g transform={`translate(${margin.left},${margin.top})`}>
            {renderedXScale && (
              <g 
                transform={`translate(0,${innerHeight})`}
                ref={el => { if (el) d3.select(el).call(d3.axisBottom(renderedXScale).ticks(5)); }}
                className="text-[10px] font-mono text-[#64748B] opacity-50"
              />
            )}
            {renderedYScale && (
              <g 
                ref={el => { if (el) d3.select(el).call(d3.axisLeft(renderedYScale).ticks(5)); }}
                className="text-[10px] font-mono text-[#64748B] opacity-50"
              />
            )}

            {/* Labels */}
            <text x={innerWidth / 2} y={innerHeight + 30} textAnchor="middle" className="text-[10px] font-mono fill-[#64748B]">Time</text>
            <text transform="rotate(-90)" y={-40} x={-innerHeight / 2} textAnchor="middle" className="text-[10px] font-mono fill-[#64748B]">Value Band</text>

            <motion.g 
              clipPath="url(#chart-area-main-v2)"
              drag
              dragConstraints={{ left: 0, right: 0, top: 0, bottom: 0 }}
              dragElastic={0.05}
            >
              {/* Heatmap Layer */}
              {viewMode === 'heatmap' && contours && (
                <g className="heatmap-contours">
                  {contours.map((contour, i) => (
                    <path
                      key={i}
                      d={d3.geoPath()(contour) || ""}
                      fill="#0A5C91"
                      fillOpacity={0.1}
                      stroke="#0A5C91"
                      strokeOpacity={0.2}
                      strokeWidth={0.5}
                      transform={zoomTransform.toString()}
                    />
                  ))}
                </g>
              )}

              {/* Points Layer */}
              {renderedXScale && renderedYScale && data.map((d, i) => (
                <React.Fragment key={d.time.getTime() + i}>
                  <motion.circle
                    layout
                    initial={false}
                    animate={{
                      cx: renderedXScale(d.time),
                      cy: renderedYScale(d.coherence),
                      opacity: viewMode === 'heatmap' ? 0.3 : 0.7
                    }}
                    transition={{ type: "spring", stiffness: 300, damping: 30 }}
                    r={viewMode === 'heatmap' ? 2 : 4}
                    fill="#0A5C91"
                    onMouseEnter={(e) => setHoveredPoint({ point: d, type: 'coherence', x: e.clientX, y: e.clientY })}
                    onMouseLeave={() => setHoveredPoint(null)}
                    style={{ cursor: 'pointer' }}
                  />
                  <motion.circle
                    layout
                    initial={false}
                    animate={{
                      cx: renderedXScale(d.time),
                      cy: renderedYScale(d.resonance),
                      opacity: viewMode === 'heatmap' ? 0.3 : 0.7
                    }}
                    transition={{ type: "spring", stiffness: 300, damping: 30 }}
                    r={viewMode === 'heatmap' ? 2 : 4}
                    fill="#e36c0a"
                    onMouseEnter={(e) => setHoveredPoint({ point: d, type: 'resonance', x: e.clientX, y: e.clientY })}
                    onMouseLeave={() => setHoveredPoint(null)}
                    style={{ cursor: 'pointer' }}
                  />
                </React.Fragment>
              ))}
            </motion.g>
          </g>
        </svg>
      </div>

      <AnimatePresence>
        {hoveredPoint && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 10 }}
            className="fixed z-50 pointer-events-none bg-oxford/90 backdrop-blur-sm border border-[#E2E4E9]/20 p-3 rounded-lg shadow-xl text-white font-mono text-[10px]"
            style={{ 
              left: hoveredPoint.x + 15, 
              top: hoveredPoint.y - 40 
            }}
          >
            <div className="flex flex-col gap-1">
              <div className="flex justify-between gap-4">
                <span className="text-gray-400 capitalize">{hoveredPoint.type}</span>
                <span className="font-bold">{(hoveredPoint.type === 'coherence' ? hoveredPoint.point.coherence : hoveredPoint.point.resonance).toFixed(4)}</span>
              </div>
              <div className="flex justify-between gap-4">
                <span className="text-gray-400">Timestamp</span>
                <span>{hoveredPoint.point.time.toLocaleTimeString()}</span>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="mt-2 text-[8px] font-mono text-[#64748B] text-center italic">
        Scroll to zoom • Drag plot to pan • Switch modes for density insights
      </div>
    </div>
  );
};
