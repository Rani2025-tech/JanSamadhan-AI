export interface DistrictCentroid {
  name: string;
  lat: number;
  lng: number;
  division?: 'Northern' | 'Central' | 'Southern';
}

export const ODISHA_DISTRICTS: Record<string, DistrictCentroid> = {
  Angul: { name: 'Angul', lat: 20.84, lng: 85.10, division: 'Northern' },
  Balangir: { name: 'Balangir', lat: 20.72, lng: 83.48, division: 'Northern' },
  Balasore: { name: 'Balasore', lat: 21.49, lng: 86.93, division: 'Central' },
  Bargarh: { name: 'Bargarh', lat: 21.33, lng: 83.62, division: 'Northern' },
  Bhadrak: { name: 'Bhadrak', lat: 21.06, lng: 86.50, division: 'Central' },
  Boudh: { name: 'Boudh', lat: 20.84, lng: 84.32, division: 'Southern' },
  Cuttack: { name: 'Cuttack', lat: 20.46, lng: 85.88, division: 'Central' },
  Deogarh: { name: 'Deogarh', lat: 21.53, lng: 84.73, division: 'Northern' },
  Dhenkanal: { name: 'Dhenkanal', lat: 20.67, lng: 85.60, division: 'Northern' },
  Gajapati: { name: 'Gajapati', lat: 18.81, lng: 84.16, division: 'Southern' },
  Ganjam: { name: 'Ganjam', lat: 19.38, lng: 85.05, division: 'Southern' },
  Jagatsinghpur: { name: 'Jagatsinghpur', lat: 20.27, lng: 86.17, division: 'Central' },
  Jajpur: { name: 'Jajpur', lat: 20.85, lng: 86.33, division: 'Central' },
  Jharsuguda: { name: 'Jharsuguda', lat: 21.85, lng: 84.01, division: 'Northern' },
  Kalahandi: { name: 'Kalahandi', lat: 19.91, lng: 83.16, division: 'Southern' },
  Kandhamal: { name: 'Kandhamal', lat: 20.42, lng: 84.23, division: 'Southern' },
  Kendrapara: { name: 'Kendrapara', lat: 20.50, lng: 86.42, division: 'Central' },
  Kendujhar: { name: 'Kendujhar', lat: 21.63, lng: 85.58, division: 'Northern' },
  Khurda: { name: 'Khurda', lat: 20.19, lng: 85.62, division: 'Central' },
  Koraput: { name: 'Koraput', lat: 18.81, lng: 82.71, division: 'Southern' },
  Malkangiri: { name: 'Malkangiri', lat: 18.35, lng: 81.90, division: 'Southern' },
  Mayurbhanj: { name: 'Mayurbhanj', lat: 21.93, lng: 86.74, division: 'Central' },
  Nabarangpur: { name: 'Nabarangpur', lat: 19.23, lng: 82.55, division: 'Southern' },
  Nayagarh: { name: 'Nayagarh', lat: 20.13, lng: 85.10, division: 'Central' },
  Nuapada: { name: 'Nuapada', lat: 20.83, lng: 82.52, division: 'Southern' },
  Puri: { name: 'Puri', lat: 19.81, lng: 85.83, division: 'Central' },
  Rayagada: { name: 'Rayagada', lat: 19.17, lng: 83.42, division: 'Southern' },
  Sambalpur: { name: 'Sambalpur', lat: 21.47, lng: 83.97, division: 'Northern' },
  Subarnapur: { name: 'Subarnapur', lat: 20.84, lng: 83.92, division: 'Northern' },
  Sundargarh: { name: 'Sundargarh', lat: 22.12, lng: 84.04, division: 'Northern' },
};

// Aliases for matching variations in spellings
export const DISTRICT_ALIASES: Record<string, string> = {
  Bolangir: 'Balangir',
  Baleswar: 'Balasore',
  Keonjhar: 'Kendujhar',
  Debagarh: 'Deogarh',
  Sonepur: 'Subarnapur',
  Sonapur: 'Subarnapur',
  Bhubaneswar: 'Khurda',
  Berhampur: 'Ganjam',
  Rourkela: 'Sundargarh',
};

export function getDistrictCentroid(districtName: string): DistrictCentroid | null {
  if (!districtName) return null;
  const normalized = districtName.trim();
  if (ODISHA_DISTRICTS[normalized]) return ODISHA_DISTRICTS[normalized];
  const canonical = DISTRICT_ALIASES[normalized];
  if (canonical && ODISHA_DISTRICTS[canonical]) return ODISHA_DISTRICTS[canonical];
  
  // Case-insensitive fallback
  const lower = normalized.toLowerCase();
  for (const [key, val] of Object.entries(ODISHA_DISTRICTS)) {
    if (key.toLowerCase() === lower) return val;
  }
  for (const [key, val] of Object.entries(DISTRICT_ALIASES)) {
    if (key.toLowerCase() === lower) return ODISHA_DISTRICTS[val];
  }
  return null;
}

