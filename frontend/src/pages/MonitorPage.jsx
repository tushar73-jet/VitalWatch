import { useState, useEffect, useRef, useCallback } from 'react';
import { getAnalytics, getPatient, predict, explain } from '../lib/api';
import AlertBanner from '../components/AlertBanner';
import { 
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, 
    ReferenceLine, ResponsiveContainer 
} from 'recharts';
import { Play, Pause } from 'lucide-react';

export default function MonitorPage() {
    const [cases, setCases] = useState([]);
    const [selectedCase, setSelectedCase] = useState(null);
    const [patientData, setPatientData] = useState([]);
    
    const [currentIndex, setCurrentIndex] = useState(0);
    const [isPlaying, setIsPlaying] = useState(false);
    const [speed, setSpeed] = useState(1);
    
    const [currentVitals, setCurrentVitals] = useState({ MAP: 0, HR: 0, SpO2: 0 });
    const [riskScore, setRiskScore] = useState(0);
    const [alertLevel, setAlertLevel] = useState("low");
    
    const [chartData, setChartData] = useState([]);
    const [shapFeatures, setShapFeatures] = useState([]);
    
    const [loadingCases, setLoadingCases] = useState(true);
    const [errorCases, setErrorCases] = useState(null);
    const [loadingPatient, setLoadingPatient] = useState(false);
    
    const stepCountRef = useRef(0);

    const fetchCases = useCallback(async () => {
        setLoadingCases(true);
        setErrorCases(null);
        try {
            const data = await getAnalytics();
            if (data && data.per_case) {
                const caseIds = data.per_case.map(c => c.case_id);
                setCases(caseIds);
                if (caseIds.length > 0) {
                    loadCase(caseIds[0]);
                }
            }
        } catch (e) {
            setErrorCases('Could not load patient cases. Is the backend running?');
        } finally {
            setLoadingCases(false);
        }
    }, []);

    useEffect(() => {
        fetchCases();
    }, [fetchCases]);

    const loadCase = useCallback(async (cid) => {
        setSelectedCase(cid);
        setIsPlaying(false);
        setLoadingPatient(true);
        try {
            const data = await getPatient(cid);
            setPatientData(data);
            setCurrentIndex(0);
            setChartData([]);
            setShapFeatures([]);
            stepCountRef.current = 0;
            setRiskScore(0);
            setAlertLevel("low");
            setCurrentVitals({ MAP: 0, HR: 0, SpO2: 0 });
            
            if (data.length > 0) {
                processRow(data[0], 0);
            }
        } catch (e) {
            console.error("Failed to load patient:", e);
        } finally {
            setLoadingPatient(false);
        }
    }, []);

    const processRow = async (row, index) => {
        setCurrentVitals({
            MAP: row.MAP_current || 0,
            HR: row.HR_current || 0,
            SpO2: row.SpO2_current || 0
        });

        try {
            const predRes = await predict(row);
            setRiskScore(predRes.risk_score);
            setAlertLevel(predRes.alert_level);

            setChartData(prev => {
                const newPoint = {
                    time: index,
                    MAP: row.MAP_current || 0,
                    HR: row.HR_current || 0,
                    SpO2: row.SpO2_current || 0
                };
                const newData = [...prev, newPoint];
                return newData.length > 300 ? newData.slice(-300) : newData;
            });

            stepCountRef.current += 1;
            if (stepCountRef.current % 5 === 0 || stepCountRef.current === 1) {
                const explRes = await explain(row);
                if (explRes && explRes.top_features) {
                    setShapFeatures(explRes.top_features);
                }
            }
        } catch (e) {
            console.error("Prediction/Explanation API error:", e);
        }
    };

    useEffect(() => {
        let interval;
        if (isPlaying && patientData.length > 0) {
            interval = setInterval(() => {
                setCurrentIndex(prev => {
                    const nextIndex = prev + speed;
                    if (nextIndex >= patientData.length) {
                        setIsPlaying(false);
                        return prev;
                    }
                    return nextIndex;
                });
            }, 1000);
        }
        return () => clearInterval(interval);
    }, [isPlaying, speed, patientData.length]);

    useEffect(() => {
        if (patientData.length > 0 && currentIndex > 0 && isPlaying) {
            processRow(patientData[currentIndex], currentIndex);
        }
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [currentIndex, patientData, isPlaying]);

    const minutes = Math.floor(currentIndex / 60).toString().padStart(2, '0');
    const seconds = (currentIndex % 60).toString().padStart(2, '0');
    
    // Risk visual parameters
    const riskPercent = riskScore * 100;
    let riskColor = "text-white";
    let badgeColor = "bg-gray-800 text-white";
    let badgeText = "NORMAL";
    
    if (alertLevel === "high") {
        riskColor = "text-red-500";
        badgeColor = "bg-red-500 text-white";
        badgeText = "HIGH RISK (CRITICAL)";
    } else if (alertLevel === "medium") {
        riskColor = "text-amber-400";
        badgeColor = "bg-amber-500 text-black";
        badgeText = "MEDIUM RISK";
    } else {
        badgeColor = "bg-cyan-500 text-black";
        badgeText = "STABLE";
    }

function SkeletonBlock({ h = 'h-64' }) {
    return <div className={`${h} bg-gray-900 rounded-lg animate-pulse w-full`} />;
}

    return (
        <div className="bg-black min-h-screen pt-[68px] flex flex-col font-mono text-gray-200">
            {errorCases ? (
                <div className="flex-1 flex items-center justify-center p-8">
                    <div className="bg-red-950/40 border border-red-800/50 rounded-lg p-8 max-w-md w-full flex flex-col items-center text-center">
                        <div className="text-red-400 font-mono text-lg font-bold mb-2">⚠ System Offline</div>
                        <div className="text-gray-400 text-sm mb-6">{errorCases}</div>
                        <button
                            onClick={fetchCases}
                            className="bg-cyan-500 hover:bg-cyan-400 text-black px-6 py-2 rounded font-bold transition-colors"
                        >
                            Retry Connection
                        </button>
                    </div>
                </div>
            ) : (
                <>
            {/* Control bar */}
            <div className="bg-gray-950 border-b border-gray-800 px-6 py-3 flex items-center justify-between shadow-lg z-10 shrink-0">
                <div className="flex items-center gap-6">
                    <div className="flex items-center gap-2">
                        <span className="text-gray-500 text-sm">CASE:</span>
                        {loadingCases ? (
                            <div className="w-24 h-7 bg-gray-900 animate-pulse rounded" />
                        ) : (
                            <select 
                                className="bg-black text-cyan-400 border border-gray-800 px-3 py-1 font-mono text-sm rounded outline-none cursor-pointer"
                                value={selectedCase || ''}
                                onChange={(e) => loadCase(parseInt(e.target.value))}
                                disabled={loadingCases || loadingPatient}
                            >
                                {cases.map(c => <option key={c} value={c}>#{c}</option>)}
                            </select>
                        )}
                    </div>
                    
                    <div className="w-px h-6 bg-gray-800 hidden sm:block" />
                    
                    <div className="flex items-center gap-2">
                        <button 
                            onClick={() => setIsPlaying(!isPlaying)}
                            disabled={loadingCases || loadingPatient}
                            className={`p-2 rounded transition ${isPlaying ? 'bg-cyan-900 text-cyan-400 shadow-[0_0_10px_rgba(0,229,255,0.5)]' : 'bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-white'} disabled:opacity-50`}
                        >
                            {isPlaying ? <Pause size={18} /> : <Play size={18} />}
                        </button>
                        
                        <button
                            onClick={() => window.open(`/api/patient/${selectedCase}/export`, '_blank')}
                            disabled={loadingCases || loadingPatient || !selectedCase}
                            className="bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-white px-3 py-1.5 rounded text-xs font-bold transition disabled:opacity-50 border border-gray-700 ml-2"
                        >
                            Export CSV
                        </button>
                        
                        <div className="flex items-center bg-gray-900 rounded overflow-hidden border border-gray-800 ml-2">
                            {[1, 5, 10].map(s => (
                                <button
                                    key={s}
                                    onClick={() => setSpeed(s)}
                                    className={`px-3 py-1 text-xs transition border-r border-gray-800 last:border-0 ${speed === s ? 'bg-cyan-600 text-white font-bold' : 'text-gray-400 hover:bg-gray-800'}`}
                                >
                                    {s}x
                                </button>
                            ))}
                        </div>
                    </div>
                </div>
                
                <div className="flex items-center gap-3">
                    <span className="text-gray-500 text-xs sm:text-sm">TIME OFFSET</span>
                    <div className="bg-black px-3 py-1 border border-gray-800 rounded text-cyan-400 font-bold tracking-widest text-lg">
                        {minutes}:{seconds}
                    </div>
                </div>
            </div>

            <AlertBanner shown={alertLevel === "high"} />

            {/* Main grid */}
            <div className="flex-1 grid grid-cols-12 gap-0 overflow-y-auto sm:overflow-hidden">
                {/* Left panel */}
                <div className="col-span-12 lg:col-span-3 bg-gray-950 border-r border-gray-800 p-6 flex flex-col justify-between shrink-0">
                    <div>
                        {loadingPatient ? (
                            <>
                                <SkeletonBlock h="h-16 mb-6" />
                                <SkeletonBlock h="h-16 mb-6" />
                                <SkeletonBlock h="h-16 mb-6" />
                            </>
                        ) : (
                            <>
                                <div className="mb-6">
                                    <div className="text-gray-500 text-xs tracking-widest mb-1">MAP (mmHg)</div>
                                    <div className="text-5xl font-mono text-cyan-400 font-bold">
                                        {currentVitals.MAP ? currentVitals.MAP.toFixed(1) : "0.0"}
                                    </div>
                                </div>
                                <div className="mb-6">
                                    <div className="text-gray-500 text-xs tracking-widest mb-1">HR (bpm)</div>
                                    <div className="text-5xl font-mono text-white font-bold">
                                        {currentVitals.HR ? currentVitals.HR.toFixed(1) : "0.0"}
                                    </div>
                                </div>
                                <div className="mb-6">
                                    <div className="text-gray-500 text-xs tracking-widest mb-1">SpO2 (%)</div>
                                    <div className="text-5xl font-mono text-green-400 font-bold">
                                        {currentVitals.SpO2 ? currentVitals.SpO2.toFixed(1) : "0.0"}
                                    </div>
                                </div>
                            </>
                        )}
                    </div>

                    <div className="mt-8 pt-8 border-t border-gray-800">
                        <div className="text-gray-500 text-xs tracking-widest mb-2 font-bold">LIVE RISK SCORE</div>
                        <div className={`text-6xl font-mono font-bold transition-colors duration-500 ${riskColor}`}>
                            {riskPercent.toFixed(1)}%
                        </div>
                        <div className={`mt-5 px-4 py-2 rounded-full inline-block text-xs uppercase tracking-widest font-bold shadow-lg transition-colors duration-500 ${badgeColor}`}>
                            {badgeText}
                        </div>
                    </div>
                </div>

                {/* Center panel */}
                <div className="col-span-12 lg:col-span-6 bg-black p-6 flex flex-col min-h-[400px]">
                    <div className="text-cyan-400 uppercase tracking-widest text-xs mb-6 font-bold flex items-center">
                        <div className="w-2 h-2 bg-cyan-400 rounded-full mr-2 animate-pulse" />
                        Vital Signs Timeline
                    </div>
                    
                    <div className="flex-1 w-full relative">
                        {loadingPatient ? (
                            <div className="absolute inset-0 flex items-center justify-center">
                                <SkeletonBlock h="h-full" />
                            </div>
                        ) : (
                            <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#222" vertical={false} />
                                    <XAxis dataKey="time" stroke="#555" tick={{fill: '#888', fontSize: 12}} dy={10} />
                                    <YAxis stroke="#555" tick={{fill: '#888', fontSize: 12}} domain={['auto', 'auto']} dx={-5} />
                                    <Tooltip 
                                        contentStyle={{ backgroundColor: 'rgba(0,0,0,0.9)', borderColor: '#333', borderRadius: '8px', color: '#fff' }}
                                        itemStyle={{ fontSize: '14px', fontWeight: 'bold' }}
                                    />
                                    <ReferenceLine y={65} stroke="red" strokeDasharray="5 5" strokeWidth={1} label={{ position: 'insideTopLeft', value: 'MAP CRITICAL (65)', fill: 'red', fontSize: 10 }} />
                                    
                                    <Line type="monotone" dataKey="MAP" stroke="#00E5FF" strokeWidth={2} dot={false} isAnimationActive={false} />
                                    <Line type="monotone" dataKey="HR" stroke="#FFFFFF" strokeWidth={1.5} dot={false} isAnimationActive={false} opacity={0.6} />
                                    <Line type="monotone" dataKey="SpO2" stroke="#4ADE80" strokeWidth={1.5} dot={false} isAnimationActive={false} opacity={0.6} />
                                </LineChart>
                            </ResponsiveContainer>
                        )}
                    </div>
                </div>

                {/* Right panel */}
                <div className="col-span-12 lg:col-span-3 bg-gray-950 border-l border-gray-800 p-6 overflow-y-auto min-h-[300px]">
                    <div className="text-cyan-400 uppercase tracking-widest text-xs mb-6 font-bold flex items-center justify-between">
                        Risk Context
                        <span className="bg-gray-800 text-gray-400 px-2 py-0.5 rounded text-[10px]">SHAP</span>
                    </div>

                    <div className="flex flex-col gap-4 mt-2">
                        {loadingPatient ? (
                            <>
                                <SkeletonBlock h="h-8 mb-2" />
                                <SkeletonBlock h="h-8 mb-2" />
                                <SkeletonBlock h="h-8 mb-2" />
                                <SkeletonBlock h="h-8 mb-2" />
                            </>
                        ) : shapFeatures.length === 0 ? (
                            <div className="text-gray-600 text-xs italic mt-4">Computing real-time SHAP topology...</div>
                        ) : null}
                        
                        {!loadingPatient && shapFeatures.map(f => {
                            const isPos = f.impact > 0;
                            const colorClass = isPos ? 'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.5)]' : 'bg-cyan-500 shadow-[0_0_8px_rgba(6,182,212,0.5)]';
                            const maxImpact = Math.max(...shapFeatures.map(x => Math.abs(x.impact)), 0.001);
                            const widthPct = (Math.abs(f.impact) / maxImpact) * 100;
                            
                            return (
                                <div key={f.name} className="flex flex-col mb-1 group">
                                    <div className="flex items-center justify-between mb-1">
                                        <div className="text-gray-400 text-xs truncate mr-2 font-mono group-hover:text-white transition-colors" title={f.name}>
                                            {f.name.substring(0, 15)}
                                        </div>
                                        <div className="w-10 text-right text-xs font-bold font-mono text-gray-300">
                                            {isPos ? "+" : ""}{f.impact.toFixed(2)}
                                        </div>
                                    </div>
                                    <div className="w-full h-1.5 bg-black rounded overflow-hidden relative">
                                        <div className={`${colorClass} h-full rounded transition-all duration-300`} style={{ width: `${widthPct}%` }} />
                                    </div>
                                </div>
                            )
                        })}
                    </div>
                </div>
            </div>
                </>
            )}
        </div>
    );
}
