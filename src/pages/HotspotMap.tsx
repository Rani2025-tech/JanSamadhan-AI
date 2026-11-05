import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import {
  MapPin,
  AlertTriangle,
  Layers,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  Filter,
  Flame,
  Clock,
  ArrowUpDown,
  Building,
  ArrowLeft,
  Compass,
} from 'lucide-react';
import { api } from '../services/api';
import { HotspotRecord } from '../types';
import { getDistrictCentroid } from '../data/odishaDistricts';
import { getStateCentroid } from '../data/indiaLocations';

// Fix Leaflet's default icon URL issue with bundlers (Vite/Webpack)
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

const INDIA_CENTER: [number, number] = [22.5, 82.0];
const INDIA_ZOOM = 4;
const ODISHA_CENTER: [number, number] = [20.95, 85.1];
const ODISHA_ZOOM = 7;

function MapViewController({ center, zoom }: { center: [number, number]; zoom: number }) {
  const map = useMap();
  useEffect(() => {
    map.setView(center, zoom, { animate: true });
  }, [center, zoom, map]);
  return null;
}

export const HotspotMap: React.FC = () => {
  const navigate = useNavigate();
  const [viewMode, setViewMode] = useState<'national' | 'district'>('national');
  const [activeState, setActiveState] = useState<string | null>(null);

  const [hotspots, setHotspots] = useState<HotspotRecord[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [severityFilter, setSeverityFilter] = useState<string>('All');
  const [selectedRecord, setSelectedRecord] = useState<HotspotRecord | null>(null);
  const [isTableCollapsed, setIsTableCollapsed] = useState<boolean>(false);
  const [sortField, setSortField] = useState<'district' | 'total_complaints' | 'open_count' | 'critical_count' | 'average_urgency'>('total_complaints');
  const [sortAsc, setSortAsc] = useState<boolean>(false);

  const fetchHotspots = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getHotspots({
        view: viewMode,
        state: activeState || undefined,
      });
      setHotspots(data);
      if (data.length > 0) {
        setSelectedRecord(data[0]);
      } else {
        setSelectedRecord(null);
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to load grievance hotspot data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHotspots();
  }, [viewMode, activeState]);

  const handleDrillDownToDistrict = (stateName: string) => {
    setActiveState(stateName);
    setViewMode('district');
  };

  const handleBackToIndia = () => {
    setActiveState(null);
    setViewMode('national');
  };

  // Filter hotspots based on severity
  const filteredHotspots = hotspots.filter(h => {
    if (severityFilter === 'All') return true;
    return h.severity.toLowerCase() === severityFilter.toLowerCase();
  });

  // Sort hotspots for table view
  const sortedHotspots = [...filteredHotspots].sort((a, b) => {
    let cmp = 0;
    if (sortField === 'district') {
      cmp = (a.district || a.state || '').localeCompare(b.district || b.state || '');
    } else {
      cmp = (a[sortField] as number) - (b[sortField] as number);
    }
    return sortAsc ? cmp : -cmp;
  });

  const handleSort = (field: typeof sortField) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(false);
    }
  };

  const getMarkerColors = (severity: 'green' | 'amber' | 'red') => {
    switch (severity) {
      case 'red':
        return { fill: '#DC2626', stroke: '#991B1B' };
      case 'amber':
        return { fill: '#F59E0B', stroke: '#B45309' };
      case 'green':
      default:
        return { fill: '#16A34A', stroke: '#15803D' };
    }
  };

  const currentCenter = viewMode === 'national' ? INDIA_CENTER : ODISHA_CENTER;
  const currentZoom = viewMode === 'national' ? INDIA_ZOOM : ODISHA_ZOOM;

  return (
    <div className="space-y-6 animate-in fade-in duration-300 pb-16">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider bg-maroon-100 text-maroon-900 border border-maroon-200">
              <Compass className="w-3 h-3 text-maroon-700" />
              <span>{viewMode === 'national' ? 'All-India National Telemetry' : `${activeState || 'Odisha'} District Telemetry`}</span>
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900 tracking-tight flex items-center gap-2.5">
            <MapPin className="w-8 h-8 text-maroon-800" />
            <span>Civic Grievance Hotspot Map</span>
          </h1>
          <p className="text-sm text-gray-600 mt-1">
            {viewMode === 'national'
              ? 'Real-time geospatial intelligence across India states showing grievance volume, urgency levels, and drill-down clusters.'
              : `Deep-dive district geospatial intelligence for ${activeState || 'Odisha'}, showing ward-level grievance density and SLA bottlenecks.`}
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex flex-wrap items-center gap-3">
          {viewMode === 'district' && (
            <button
              onClick={handleBackToIndia}
              className="flex items-center gap-1.5 px-4 py-2 rounded-full bg-maroon-800 hover:bg-maroon-900 text-white text-xs font-bold shadow-md transition-all focus-ring"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Back to India</span>
            </button>
          )}

          <div className="inline-flex items-center p-1 rounded-full bg-cream-200 border border-maroon-200 text-xs font-bold">
            <button
              onClick={() => setViewMode('national')}
              className={`px-3 py-1 rounded-full transition-all ${
                viewMode === 'national' ? 'bg-maroon-800 text-white shadow-xs' : 'text-gray-700 hover:text-maroon-900'
              }`}
            >
              National View
            </button>
            <button
              onClick={() => handleDrillDownToDistrict('Odisha')}
              className={`px-3 py-1 rounded-full transition-all ${
                viewMode === 'district' ? 'bg-maroon-800 text-white shadow-xs' : 'text-gray-700 hover:text-maroon-900'
              }`}
            >
              Odisha View
            </button>
          </div>

          <button
            onClick={fetchHotspots}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-maroon-200 bg-white hover:bg-cream-100 text-maroon-900 text-xs font-bold shadow-xs transition-colors focus-ring"
            title="Refresh Map Data"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>

          {/* Severity Filter */}
          <div className="flex items-center gap-2 bg-white px-3 py-1.5 rounded-full border border-maroon-100 shadow-xs">
            <Filter className="w-4 h-4 text-gray-400" />
            <span className="text-xs font-bold text-gray-600">Severity:</span>
            <select
              value={severityFilter}
              onChange={e => setSeverityFilter(e.target.value)}
              className="text-xs font-bold text-maroon-800 bg-transparent focus:outline-none cursor-pointer"
            >
              <option value="All">All Levels</option>
              <option value="red">Critical (Red)</option>
              <option value="amber">Attention (Amber)</option>
              <option value="green">Normal (Green)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Loading & Error States */}
      {loading && hotspots.length === 0 && (
        <div className="bg-white rounded-3xl p-12 border border-maroon-100 shadow-soft text-center space-y-3">
          <div className="w-10 h-10 border-4 border-maroon-800 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-sm font-semibold text-gray-700">Loading geospatial grievance telemetry...</p>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-3xl p-6 text-red-900 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-6 h-6 text-red-600 flex-shrink-0" />
            <div>
              <h3 className="font-bold text-sm">Failed to retrieve GIS hotspot data</h3>
              <p className="text-xs text-red-700 mt-0.5">{error}</p>
            </div>
          </div>
          <button
            onClick={fetchHotspots}
            className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-xs font-bold rounded-xl transition-colors shadow-xs"
          >
            Retry
          </button>
        </div>
      )}

      {/* Main Map & Detail Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        
        {/* Left: Real Leaflet Map Container (8 cols) */}
        <div className="lg:col-span-8 bg-white rounded-3xl p-5 border border-maroon-100 shadow-soft space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <Layers className="w-4 h-4 text-maroon-800" />
              <h2 className="text-base font-extrabold text-gray-900">
                {viewMode === 'national' ? 'National State Telemetry Map' : `${activeState || 'Odisha'} District GIS Map`}
              </h2>
            </div>
            <div className="flex items-center gap-2">
              {viewMode === 'district' && (
                <button
                  onClick={handleBackToIndia}
                  className="inline-flex items-center gap-1 text-xs font-bold text-maroon-800 hover:text-maroon-900 underline"
                >
                  <ArrowLeft className="w-3 h-3" />
                  <span>Back to India</span>
                </button>
              )}
              <span className="text-xs text-gray-500 font-medium">
                {viewMode === 'national'
                  ? 'Centred on India (22.5°N, 82.0°E)'
                  : 'Centred on Odisha (20.95°N, 85.1°E)'} • Click marker to inspect
              </span>
            </div>
          </div>

          {/* Leaflet Map Frame */}
          <div className="relative rounded-2xl overflow-hidden border border-maroon-100/80 shadow-inner h-[520px] z-0">
            <MapContainer
              center={currentCenter}
              zoom={currentZoom}
              scrollWheelZoom={true}
              style={{ height: '100%', width: '100%' }}
              className="z-0"
            >
              <MapViewController center={currentCenter} zoom={currentZoom} />
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />

              {/* Markers for National or District */}
              {filteredHotspots.map(h => {
                const label = h.district || h.state || 'Unknown';
                let lat: number | undefined;
                let lng: number | undefined;

                if (viewMode === 'national') {
                  const stateCentroid = getStateCentroid(label);
                  if (stateCentroid) {
                    lat = stateCentroid.lat;
                    lng = stateCentroid.lng;
                  }
                } else {
                  const districtCentroid = getDistrictCentroid(label);
                  if (districtCentroid) {
                    lat = districtCentroid.lat;
                    lng = districtCentroid.lng;
                  }
                }

                if (lat === undefined || lng === undefined) return null;

                const colors = getMarkerColors(h.severity);
                // Radius scales dynamically with complaint count
                const radius = Math.max(9, Math.min(32, 8 + Math.sqrt(h.total_complaints) * 3.5));
                const canDrillDown = (viewMode === 'national' && (label === 'Odisha' || (h as any).has_district_data));

                return (
                  <CircleMarker
                    key={label}
                    center={[lat, lng]}
                    radius={radius}
                    pathOptions={{
                      color: colors.stroke,
                      fillColor: colors.fill,
                      fillOpacity: 0.85,
                      weight: 2.5,
                    }}
                    eventHandlers={{
                      click: () => {
                        setSelectedRecord(h);
                      },
                    }}
                  >
                    <Popup>
                      <div className="p-2 min-w-[220px] space-y-2 text-gray-800">
                        <div className="flex items-center justify-between gap-2 border-b border-gray-200 pb-1.5">
                          <strong className="text-sm font-black text-maroon-900">{label}</strong>
                          <span
                            className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                              h.severity === 'red'
                                ? 'bg-red-100 text-red-800'
                                : h.severity === 'amber'
                                ? 'bg-amber-100 text-amber-800'
                                : 'bg-green-100 text-green-800'
                            }`}
                          >
                            {h.severity === 'red' ? 'Critical' : h.severity === 'amber' ? 'Attention' : 'Normal'}
                          </span>
                        </div>

                        <div className="space-y-1 text-xs">
                          <div className="flex justify-between">
                            <span className="text-gray-500 font-medium">Total Grievances:</span>
                            <span className="font-extrabold text-gray-900">{h.total_complaints}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-500 font-medium">Open Count:</span>
                            <span className="font-bold text-amber-700">{h.open_count}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-500 font-medium">Critical Items:</span>
                            <span className="font-bold text-red-700">{h.critical_count}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-500 font-medium">Top Category:</span>
                            <span className="font-semibold text-maroon-800">{h.top_category}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-500 font-medium">Avg Urgency:</span>
                            <span className="font-bold text-gray-800">{h.average_urgency} / 4.0</span>
                          </div>
                        </div>

                        {canDrillDown ? (
                          <button
                            type="button"
                            onClick={() => handleDrillDownToDistrict(label)}
                            className="mt-2 w-full py-1.5 px-2 bg-maroon-800 hover:bg-maroon-700 text-white rounded-lg text-xs font-bold transition-colors text-center flex items-center justify-center gap-1"
                          >
                            <span>Inspect {label} Districts</span>
                            <span>&rarr;</span>
                          </button>
                        ) : (
                          <button
                            type="button"
                            onClick={() => navigate(`/admin/complaints?${viewMode === 'national' ? 'state' : 'district'}=${encodeURIComponent(label)}`)}
                            className="mt-2 w-full py-1.5 px-2 bg-cream-200 hover:bg-cream-300 text-maroon-900 rounded-lg text-xs font-bold transition-colors text-center"
                          >
                            View {label} Tickets &rarr;
                          </button>
                        )}
                      </div>
                    </Popup>
                  </CircleMarker>
                );
              })}
            </MapContainer>
          </div>

          {/* Compact Legend */}
          <div className="flex flex-wrap items-center justify-between gap-3 p-3 bg-cream-100/70 rounded-2xl border border-maroon-100/70 text-xs">
            <div className="flex items-center gap-1.5 font-bold text-gray-700">
              <span>Severity Legend:</span>
            </div>

            <div className="flex flex-wrap items-center gap-4">
              <div className="flex items-center gap-1.5">
                <span className="w-3.5 h-3.5 rounded-full bg-red-600 border border-red-800 inline-block" />
                <span className="text-gray-700 font-medium">Critical / High (Score ≥ 2.8 or Critical ≥ 2)</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-3.5 h-3.5 rounded-full bg-amber-500 border border-amber-700 inline-block" />
                <span className="text-gray-700 font-medium">Attention (Score ≥ 2.0 or Open ≥ 2)</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-3.5 h-3.5 rounded-full bg-green-600 border border-green-800 inline-block" />
                <span className="text-gray-700 font-medium">Normal / Resolved</span>
              </div>
              <div className="flex items-center gap-1.5 text-gray-500 border-l border-maroon-200 pl-3">
                <span className="italic">Marker radius scales with grievance volume</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right: Selected Region Details Card (4 cols) */}
        <div className="lg:col-span-4 space-y-4">
          <div className="bg-white rounded-3xl p-6 border border-maroon-100 shadow-soft space-y-5">
            <div className="flex items-center justify-between pb-3 border-b border-gray-100">
              <div>
                <span className="text-[11px] font-bold text-gray-400 uppercase tracking-wider">
                  {viewMode === 'national' ? 'State Inspection' : 'District Inspection'}
                </span>
                <h2 className="text-xl font-black text-maroon-900">
                  {selectedRecord?.district || selectedRecord?.state || 'Select a Location'}
                </h2>
              </div>
              {selectedRecord && (
                <span
                  className={`text-xs font-extrabold px-3 py-1 rounded-full ${
                    selectedRecord.severity === 'red'
                      ? 'bg-red-100 text-red-800 border border-red-200'
                      : selectedRecord.severity === 'amber'
                      ? 'bg-amber-100 text-amber-800 border border-amber-200'
                      : 'bg-green-100 text-green-800 border border-green-200'
                  }`}
                >
                  {selectedRecord.severity.toUpperCase()}
                </span>
              )}
            </div>

            {selectedRecord ? (
              <>
                <div className="grid grid-cols-3 gap-2 text-center">
                  <div className="bg-cream-100 p-3 rounded-2xl border border-maroon-100/60">
                    <span className="text-[11px] text-gray-500 font-semibold block">Total</span>
                    <span className="text-xl font-black text-gray-900">{selectedRecord.total_complaints}</span>
                  </div>
                  <div className="bg-amber-50 p-3 rounded-2xl border border-amber-200">
                    <span className="text-[11px] text-amber-800 font-semibold block">Open</span>
                    <span className="text-xl font-black text-amber-700">{selectedRecord.open_count}</span>
                  </div>
                  <div className="bg-emerald-50 p-3 rounded-2xl border border-emerald-200">
                    <span className="text-[11px] text-emerald-800 font-semibold block">Resolved</span>
                    <span className="text-xl font-black text-emerald-700">{selectedRecord.resolved_count}</span>
                  </div>
                </div>

                <div className="space-y-3 pt-2 text-xs">
                  <div className="flex items-center justify-between p-3 rounded-2xl bg-cream-100/80 border border-maroon-100">
                    <div className="flex items-center gap-2">
                      <Flame className="w-4 h-4 text-maroon-800" />
                      <span className="font-bold text-gray-700">Top Problem Category</span>
                    </div>
                    <span className="font-black text-maroon-900">{selectedRecord.top_category}</span>
                  </div>

                  <div className="flex items-center justify-between p-3 rounded-2xl bg-red-50/80 border border-red-100">
                    <div className="flex items-center gap-2">
                      <AlertTriangle className="w-4 h-4 text-red-600" />
                      <span className="font-bold text-red-900">Critical Priority Items</span>
                    </div>
                    <span className="font-black text-red-700 text-sm">{selectedRecord.critical_count}</span>
                  </div>

                  <div className="flex items-center justify-between p-3 rounded-2xl bg-cream-100/80 border border-maroon-100">
                    <div className="flex items-center gap-2">
                      <Clock className="w-4 h-4 text-amber-700" />
                      <span className="font-bold text-gray-700">Urgency Severity Score</span>
                    </div>
                    <span className="font-black text-gray-900 text-sm">
                      {selectedRecord.average_urgency} / 4.0
                    </span>
                  </div>
                </div>

                {viewMode === 'national' && (selectedRecord.district === 'Odisha' || selectedRecord.state === 'Odisha' || (selectedRecord as any).has_district_data) ? (
                  <button
                    onClick={() => handleDrillDownToDistrict(selectedRecord.district || 'Odisha')}
                    className="w-full py-3 px-4 bg-maroon-800 hover:bg-maroon-900 text-white font-bold rounded-2xl text-xs shadow-md transition-all flex items-center justify-center gap-2"
                  >
                    <span>Inspect {selectedRecord.district || selectedRecord.state} Districts</span>
                    <span>&rarr;</span>
                  </button>
                ) : (
                  <button
                    onClick={() => navigate(`/admin/complaints?${viewMode === 'national' ? 'state' : 'district'}=${encodeURIComponent(selectedRecord.district || selectedRecord.state || '')}`)}
                    className="w-full py-3 px-4 bg-cream-200 hover:bg-cream-300 text-maroon-900 font-bold rounded-2xl text-xs transition-colors text-center"
                  >
                    Filter All {selectedRecord.district || selectedRecord.state} Tickets in Registry &rarr;
                  </button>
                )}
              </>
            ) : (
              <div className="py-8 text-center text-xs text-gray-500">
                Click any marker on the map to inspect metrics.
              </div>
            )}
          </div>

          {/* Quick Summary Pill */}
          <div className="bg-white rounded-3xl p-5 border border-maroon-100 shadow-soft space-y-2">
            <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider">
              {viewMode === 'national' ? 'National Operational Scope' : `${activeState || 'Odisha'} Coverage`}
            </h3>
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="p-3 bg-cream-100 rounded-2xl border border-maroon-100/60">
                <span className="text-gray-500 block">Active Locations</span>
                <span className="text-lg font-black text-gray-900">{hotspots.length}</span>
              </div>
              <div className="p-3 bg-cream-100 rounded-2xl border border-maroon-100/60">
                <span className="text-gray-500 block">Hotspot Alerts</span>
                <span className="text-lg font-black text-amber-700">
                  {hotspots.filter(h => h.severity !== 'green').length}
                </span>
              </div>
            </div>
          </div>
        </div>

      </div>

      {/* Grievance Matrix Table */}
      <div className="bg-white rounded-3xl border border-maroon-100 shadow-soft overflow-hidden">
        <div
          onClick={() => setIsTableCollapsed(!isTableCollapsed)}
          className="p-5 flex items-center justify-between cursor-pointer hover:bg-cream-100/50 transition-colors select-none"
        >
          <div className="flex items-center gap-3">
            <Building className="w-5 h-5 text-maroon-800" />
            <h2 className="text-base font-extrabold text-gray-900">
              {viewMode === 'national' ? 'National State Matrix' : `${activeState || 'Odisha'} District Matrix`} ({sortedHotspots.length} Regions)
            </h2>
          </div>
          <div className="flex items-center gap-2 text-xs font-bold text-maroon-800">
            <span>{isTableCollapsed ? 'Expand Table' : 'Collapse Table'}</span>
            {isTableCollapsed ? <ChevronDown className="w-4 h-4" /> : <ChevronUp className="w-4 h-4" />}
          </div>
        </div>

        {!isTableCollapsed && (
          <div className="overflow-x-auto border-t border-maroon-100">
            <table className="w-full text-left text-xs text-gray-700">
              <thead className="bg-cream-200/70 text-maroon-900 font-bold border-b border-maroon-100">
                <tr>
                  <th
                    onClick={() => handleSort('district')}
                    className="p-3.5 pl-6 cursor-pointer hover:bg-cream-300/60 transition-colors"
                  >
                    <div className="flex items-center gap-1.5">
                      <span>{viewMode === 'national' ? 'State / UT' : 'District'}</span>
                      <ArrowUpDown className="w-3 h-3 text-maroon-700" />
                    </div>
                  </th>
                  <th
                    onClick={() => handleSort('total_complaints')}
                    className="p-3.5 cursor-pointer hover:bg-cream-300/60 transition-colors"
                  >
                    <div className="flex items-center gap-1.5">
                      <span>Total Grievances</span>
                      <ArrowUpDown className="w-3 h-3 text-maroon-700" />
                    </div>
                  </th>
                  <th
                    onClick={() => handleSort('open_count')}
                    className="p-3.5 cursor-pointer hover:bg-cream-300/60 transition-colors"
                  >
                    <div className="flex items-center gap-1.5">
                      <span>Open</span>
                      <ArrowUpDown className="w-3 h-3 text-maroon-700" />
                    </div>
                  </th>
                  <th className="p-3.5">Resolved</th>
                  <th className="p-3.5">Top Category</th>
                  <th
                    onClick={() => handleSort('critical_count')}
                    className="p-3.5 cursor-pointer hover:bg-cream-300/60 transition-colors"
                  >
                    <div className="flex items-center gap-1.5">
                      <span>Critical Items</span>
                      <ArrowUpDown className="w-3 h-3 text-maroon-700" />
                    </div>
                  </th>
                  <th
                    onClick={() => handleSort('average_urgency')}
                    className="p-3.5 cursor-pointer hover:bg-cream-300/60 transition-colors"
                  >
                    <div className="flex items-center gap-1.5">
                      <span>Avg Urgency</span>
                      <ArrowUpDown className="w-3 h-3 text-maroon-700" />
                    </div>
                  </th>
                  <th className="p-3.5 pr-6">Severity Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {sortedHotspots.map(h => {
                  const label = h.district || h.state || 'Unknown';
                  const isSelected = (selectedRecord?.district === label || selectedRecord?.state === label);
                  return (
                    <tr
                      key={label}
                      onClick={() => setSelectedRecord(h)}
                      className={`cursor-pointer transition-colors ${
                        isSelected
                          ? 'bg-cream-200/80 font-bold'
                          : 'hover:bg-cream-100/60'
                      }`}
                    >
                      <td className="p-3.5 pl-6 font-bold text-gray-900 flex items-center gap-2">
                        <MapPin className="w-3.5 h-3.5 text-maroon-700 flex-shrink-0" />
                        <span>{label}</span>
                      </td>
                      <td className="p-3.5 font-bold text-gray-900">{h.total_complaints}</td>
                      <td className="p-3.5 text-amber-700 font-bold">{h.open_count}</td>
                      <td className="p-3.5 text-emerald-700 font-bold">{h.resolved_count}</td>
                      <td className="p-3.5 text-gray-700">{h.top_category}</td>
                      <td className="p-3.5 font-bold text-red-600">{h.critical_count}</td>
                      <td className="p-3.5">{h.average_urgency} / 4.0</td>
                      <td className="p-3.5 pr-6">
                        <span
                          className={`text-[11px] font-bold px-2.5 py-0.5 rounded-full inline-block ${
                            h.severity === 'red'
                              ? 'bg-red-100 text-red-800'
                              : h.severity === 'amber'
                              ? 'bg-amber-100 text-amber-800'
                              : 'bg-green-100 text-green-800'
                          }`}
                        >
                          {h.severity === 'red' ? 'Critical' : h.severity === 'amber' ? 'Moderate' : 'Normal'}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

    </div>
  );
};

export default HotspotMap;
