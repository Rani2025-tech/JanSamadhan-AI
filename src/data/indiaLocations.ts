// Generated All-India locations, centroids and districts
export interface StateCentroid {
  name: string;
  lat: number;
  lng: number;
  capital?: string;
  districts: string[];
}

export interface DistrictCentroid {
  name: string;
  lat: number;
  lng: number;
  division?: string;
}

export const STATE_CENTROIDS: Record<string, { lat: number; lng: number; capital: string }> = {
  "Odisha": { lat: 20.95, lng: 85.1, capital: "Bhubaneswar" },
  "Maharashtra": { lat: 19.75, lng: 75.71, capital: "Mumbai" },
  "Delhi": { lat: 28.7, lng: 77.1, capital: "New Delhi" },
  "Karnataka": { lat: 15.31, lng: 75.71, capital: "Bengaluru" },
  "Tamil Nadu": { lat: 11.12, lng: 78.65, capital: "Chennai" },
  "West Bengal": { lat: 22.98, lng: 87.85, capital: "Kolkata" },
  "Telangana": { lat: 18.11, lng: 79.01, capital: "Hyderabad" },
  "Uttar Pradesh": { lat: 26.84, lng: 80.94, capital: "Lucknow" },
  "Rajasthan": { lat: 27.02, lng: 74.21, capital: "Jaipur" },
  "Bihar": { lat: 25.09, lng: 85.31, capital: "Patna" },
  "Gujarat": { lat: 22.25, lng: 71.19, capital: "Gandhinagar" },
  "Kerala": { lat: 10.85, lng: 76.27, capital: "Thiruvananthapuram" },
  "Madhya Pradesh": { lat: 22.97, lng: 78.65, capital: "Bhopal" },
  "Punjab": { lat: 31.14, lng: 75.34, capital: "Chandigarh" },
  "Haryana": { lat: 29.05, lng: 76.08, capital: "Chandigarh" },
  "Andhra Pradesh": { lat: 15.91, lng: 79.74, capital: "Amaravati" },
  "Assam": { lat: 26.2, lng: 92.93, capital: "Dispur" },
  "Chhattisgarh": { lat: 21.27, lng: 81.86, capital: "Raipur" },
  "Jharkhand": { lat: 23.61, lng: 85.27, capital: "Ranchi" },
  "Uttarakhand": { lat: 30.06, lng: 79.01, capital: "Dehradun" },
  "Himachal Pradesh": { lat: 31.1, lng: 77.17, capital: "Shimla" },
  "Goa": { lat: 15.29, lng: 74.12, capital: "Panaji" },
  "Jammu and Kashmir": { lat: 33.77, lng: 76.57, capital: "Srinagar / Jammu" },
  "Ladakh": { lat: 34.15, lng: 77.57, capital: "Leh" },
  "Chandigarh": { lat: 30.73, lng: 76.77, capital: "Chandigarh" },
  "Puducherry": { lat: 11.94, lng: 79.8, capital: "Puducherry" },
  "Tripura": { lat: 23.94, lng: 91.98, capital: "Agartala" },
  "Meghalaya": { lat: 25.46, lng: 91.36, capital: "Shillong" },
  "Manipur": { lat: 24.66, lng: 93.9, capital: "Imphal" },
  "Nagaland": { lat: 26.15, lng: 94.56, capital: "Kohima" },
  "Mizoram": { lat: 23.16, lng: 92.93, capital: "Aizawl" },
  "Arunachal Pradesh": { lat: 28.21, lng: 94.72, capital: "Itanagar" },
  "Sikkim": { lat: 27.53, lng: 88.51, capital: "Gangtok" },
  "Andaman and Nicobar Islands": { lat: 11.74, lng: 92.65, capital: "Port Blair" },
  "Dadra and Nagar Haveli and Daman and Diu": { lat: 20.42, lng: 72.83, capital: "Daman" },
  "Lakshadweep": { lat: 10.56, lng: 72.64, capital: "Kavaratti" },
};

export const INDIA_STATES: Record<string, StateCentroid> = {
  "Odisha": {
    name: "Odisha",
    lat: 20.95,
    lng: 85.1,
    capital: "Bhubaneswar",
    districts: ["Angul", "Balasore", "Bargarh", "Bhadrak", "Bolangir", "Boudh", "Cuttack", "Deogarh", "Dhenkanal", "Gajapati", "Ganjam", "Jagatsinghpur", "Jajpur", "Jharsuguda", "Kalahandi", "Kandhamal", "Kendrapara", "Kendujhar", "Khurda", "Koraput", "Malkangiri", "Mayurbhanj", "Nabarangpur", "Nayagarh", "Nuapada", "Puri", "Rayagada", "Sambalpur", "Subarnapur", "Sundargarh"]
  },
  "Maharashtra": {
    name: "Maharashtra",
    lat: 19.75,
    lng: 75.71,
    capital: "Mumbai",
    districts: ["Ahmednagar", "Akola", "Amravati", "Aurangabad", "Beed", "Bhandara", "Buldhana", "Chandrapur", "Dhule", "Gadchiroli", "Gondia", "Hingoli", "Jalgaon", "Jalna", "Kolhapur", "Latur", "Mumbai City", "Mumbai Suburban", "Nagpur", "Nanded", "Nandurbar", "Nashik", "Osmanabad", "Palghar", "Parbhani", "Pune", "Raigad", "Ratnagiri", "Sangli", "Satara", "Sindhudurg", "Solapur", "Thane", "Wardha", "Washim", "Yavatmal"]
  },
  "Delhi": {
    name: "Delhi",
    lat: 28.7,
    lng: 77.1,
    capital: "New Delhi",
    districts: ["Central Delhi", "East Delhi", "New Delhi", "North Delhi", "North East Delhi", "North West Delhi", "Shahdara", "South Delhi", "South East Delhi", "South West Delhi", "West Delhi"]
  },
  "Karnataka": {
    name: "Karnataka",
    lat: 15.31,
    lng: 75.71,
    capital: "Bengaluru",
    districts: ["Bagalkot", "Ballari", "Belagavi", "Bengaluru Rural", "Bengaluru Urban", "Bidar", "Chamarajanagar", "Chikkaballapura", "Chikkamagaluru", "Chitradurga", "Dakshina Kannada", "Davanagere", "Dharwad", "Gadag", "Hassan", "Haveri", "Kalaburagi", "Kodagu", "Kolar", "Koppal", "Mandya", "Mysuru", "Raichur", "Ramanagara", "Shivamogga", "Tumakuru", "Udupi", "Uttara Kannada", "Vijayapura", "Yadgir"]
  },
  "Tamil Nadu": {
    name: "Tamil Nadu",
    lat: 11.12,
    lng: 78.65,
    capital: "Chennai",
    districts: ["Ariyalur", "Chengalpattu", "Chennai", "Coimbatore", "Cuddalore", "Dharmapuri", "Dindigul", "Erode", "Kallakurichi", "Kanchipuram", "Kanyakumari", "Karur", "Krishnagiri", "Madurai", "Mayiladuthurai", "Nagapattinam", "Namakkal", "Nilgiris", "Perambalur", "Pudukkottai", "Ramanathapuram", "Ranipet", "Salem", "Sivaganga", "Tenkasi", "Thanjavur", "Theni", "Thoothukudi", "Tiruchirappalli", "Tirunelveli", "Tirupathur", "Tiruppur", "Tiruvallur", "Tiruvannamalai", "Tiruvarur", "Vellore", "Viluppuram", "Virudhunagar"]
  },
  "West Bengal": {
    name: "West Bengal",
    lat: 22.98,
    lng: 87.85,
    capital: "Kolkata",
    districts: ["Alipurduar", "Bankura", "Birbhum", "Cooch Behar", "Dakshin Dinajpur", "Darjeeling", "Hooghly", "Howrah", "Jalpaiguri", "Jhargram", "Kalimpong", "Kolkata", "Malda", "Murshidabad", "Nadia", "North 24 Parganas", "Paschim Bardhaman", "Paschim Medinipur", "Purba Bardhaman", "Purba Medinipur", "Purulia", "South 24 Parganas", "Uttar Dinajpur"]
  },
  "Telangana": {
    name: "Telangana",
    lat: 18.11,
    lng: 79.01,
    capital: "Hyderabad",
    districts: ["Adilabad", "Bhadradri Kothagudem", "Hyderabad", "Jagtial", "Jangaon", "Jayashankar Bhupalpally", "Jogulamba Gadwal", "Kamareddy", "Karimnagar", "Khammam", "Kumuram Bheem Asifabad", "Mahabubabad", "Mahabubnagar", "Mancherial", "Medak", "Medchal Malkajgiri", "Mulugu", "Nagarkurnool", "Nalgonda", "Narayanpet", "Nirmal", "Nizamabad", "Peddapalli", "Rajanna Sircilla", "Ranga Reddy", "Sangareddy", "Siddipet", "Suryapet", "Vikarabad", "Wanaparthy", "Warangal", "Yadadri Bhuvanagiri"]
  },
  "Uttar Pradesh": {
    name: "Uttar Pradesh",
    lat: 26.84,
    lng: 80.94,
    capital: "Lucknow",
    districts: ["Agra", "Aligarh", "Ambedkar Nagar", "Amethi", "Amroha", "Auraiya", "Ayodhya", "Azamgarh", "Baghpat", "Bahraich", "Ballia", "Balrampur", "Banda", "Barabanki", "Bareilly", "Basti", "Bhadohi", "Bijnor", "Budaun", "Bulandshahr", "Chandauli", "Chitrakoot", "Deoria", "Etah", "Etawah", "Farrukhabad", "Fatehpur", "Firozabad", "Gautam Buddha Nagar", "Ghaziabad", "Ghazipur", "Gonda", "Gorakhpur", "Hamirpur", "Hapur", "Hardoi", "Hathras", "Jalaun", "Jaunpur", "Jhansi", "Kannauj", "Kanpur Dehat", "Kanpur Nagar", "Kasganj", "Kaushambi", "Kheri", "Kushinagar", "Lalitpur", "Lucknow", "Maharajganj", "Mahoba", "Mainpuri", "Mathura", "Mau", "Meerut", "Mirzapur", "Moradabad", "Muzaffarnagar", "Pilibhit", "Pratapgarh", "Prayagraj", "Raebareli", "Rampur", "Saharanpur", "Sambhal", "Sant Kabir Nagar", "Shahjahanpur", "Shamli", "Shravasti", "Siddharthnagar", "Sitapur", "Sonbhadra", "Sultanpur", "Unnao", "Varanasi"]
  },
  "Rajasthan": {
    name: "Rajasthan",
    lat: 27.02,
    lng: 74.21,
    capital: "Jaipur",
    districts: ["Ajmer", "Alwar", "Banswara", "Baran", "Barmer", "Bharatpur", "Bhilwara", "Bikaner", "Bundi", "Chittorgarh", "Churu", "Dausa", "Dholpur", "Dungarpur", "Hanumangarh", "Jaipur", "Jaisalmer", "Jalore", "Jhalawar", "Jhunjhunu", "Jodhpur", "Karauli", "Kota", "Nagaur", "Pali", "Pratapgarh", "Rajsamand", "Sawai Madhopur", "Sikar", "Sirohi", "Sri Ganganagar", "Tonk", "Udaipur"]
  },
  "Bihar": {
    name: "Bihar",
    lat: 25.09,
    lng: 85.31,
    capital: "Patna",
    districts: ["Araria", "Arwal", "Aurangabad", "Banka", "Begusarai", "Bhagalpur", "Bhojpur", "Buxar", "Darbhanga", "East Champaran", "Gaya", "Gopalganj", "Jamui", "Jehanabad", "Kaimur", "Katihar", "Khagaria", "Kishanganj", "Lakhisarai", "Madhepura", "Madhubani", "Munger", "Muzaffarpur", "Nalanda", "Nawada", "Patna", "Purnia", "Rohtas", "Saharsa", "Samastipur", "Saran", "Sheikhpura", "Sheohar", "Sitamarhi", "Siwan", "Supaul", "Vaishali", "West Champaran"]
  },
  "Gujarat": {
    name: "Gujarat",
    lat: 22.25,
    lng: 71.19,
    capital: "Gandhinagar",
    districts: ["Ahmedabad", "Amreli", "Anand", "Aravalli", "Banaskantha", "Bharuch", "Bhavnagar", "Botad", "Chhota Udaipur", "Dahod", "Dang", "Devbhoomi Dwarka", "Gandhinagar", "Gir Somnath", "Jamnagar", "Junagadh", "Kheda", "Kutch", "Mahisagar", "Mehsana", "Morbi", "Narmada", "Navsari", "Panchmahal", "Patan", "Porbandar", "Rajkot", "Sabarkantha", "Surat", "Surendranagar", "Tapi", "Vadodara", "Valsad"]
  },
  "Kerala": {
    name: "Kerala",
    lat: 10.85,
    lng: 76.27,
    capital: "Thiruvananthapuram",
    districts: ["Alappuzha", "Ernakulam", "Idukki", "Kannur", "Kasaragod", "Kollam", "Kottayam", "Kozhikode", "Malappuram", "Palakkad", "Pathanamthitta", "Thiruvananthapuram", "Thrissur", "Wayanad"]
  },
  "Madhya Pradesh": {
    name: "Madhya Pradesh",
    lat: 22.97,
    lng: 78.65,
    capital: "Bhopal",
    districts: ["Agar Malwa", "Alirajpur", "Anuppur", "Ashoknagar", "Balaghat", "Barwani", "Betul", "Bhind", "Bhopal", "Burhanpur", "Chhatarpur", "Chhindwara", "Damoh", "Datia", "Dewas", "Dhar", "Dindori", "Guna", "Gwalior", "Harda", "Hoshangabad", "Indore", "Jabalpur", "Jhabua", "Katni", "Khandwa", "Khargone", "Mandla", "Mandsaur", "Morena", "Narsinghpur", "Neemuch", "Panna", "Raisen", "Rajgarh", "Ratlam", "Rewa", "Sagar", "Satna", "Sehore", "Seoni", "Shahdol", "Shajapur", "Sheopur", "Shivpuri", "Sidhi", "Singrauli", "Tikamgarh", "Ujjain", "Umaria", "Vidisha"]
  },
  "Punjab": {
    name: "Punjab",
    lat: 31.14,
    lng: 75.34,
    capital: "Chandigarh",
    districts: ["Amritsar", "Barnala", "Bathinda", "Faridkot", "Fatehgarh Sahib", "Fazilka", "Ferozepur", "Gurdaspur", "Hoshiarpur", "Jalandhar", "Kapurthala", "Ludhiana", "Mansa", "Moga", "Mohali", "Muktsar", "Pathankot", "Patiala", "Rupnagar", "Sangrur", "Shaheed Bhagat Singh Nagar", "Tarn Taran"]
  },
  "Haryana": {
    name: "Haryana",
    lat: 29.05,
    lng: 76.08,
    capital: "Chandigarh",
    districts: ["Ambala", "Bhiwani", "Charkhi Dadri", "Faridabad", "Fatehabad", "Gurugram", "Hisar", "Jhajjar", "Jind", "Kaithal", "Karnal", "Kurukshetra", "Mahendragarh", "Nuh", "Palwal", "Panchkula", "Panipat", "Rewari", "Rohtak", "Sirsa", "Sonipat", "Yamunanagar"]
  },
  "Andhra Pradesh": {
    name: "Andhra Pradesh",
    lat: 15.91,
    lng: 79.74,
    capital: "Amaravati",
    districts: ["Alluri Sitharama Raju", "Anakapalli", "Ananthapuramu", "Annamayya", "Bapatla", "Chittoor", "Dr. B.R. Ambedkar Konaseema", "East Godavari", "Eluru", "Guntur", "Kakinada", "Krishna", "Kurnool", "Nandyal", "NTR", "Palnadu", "Parvathipuram Manyam", "Prakasam", "Srikakulam", "Sri Potti Sriramulu Nellore", "Sri Sathya Sai", "Tirupati", "Visakhapatnam", "Vizianagaram", "West Godavari", "YSR"]
  },
  "Assam": {
    name: "Assam",
    lat: 26.2,
    lng: 92.93,
    capital: "Dispur",
    districts: ["Baksa", "Barpeta", "Biswanath", "Bongaigaon", "Cachar", "Charaideo", "Chirang", "Darrang", "Dhemaji", "Dhubri", "Dibrugarh", "Dima Hasao", "Goalpara", "Golaghat", "Hailakandi", "Hojai", "Jorhat", "Kamrup", "Kamrup Metropolitan", "Karbi Anglong", "Karimganj", "Kokrajhar", "Lakhimpur", "Majuli", "Morigaon", "Nagaon", "Nalbari", "Sivasagar", "Sonitpur", "South Salmara-Mankachar", "Tinsukia", "Udalguri", "West Karbi Anglong"]
  },
  "Chhattisgarh": {
    name: "Chhattisgarh",
    lat: 21.27,
    lng: 81.86,
    capital: "Raipur",
    districts: ["Balod", "Baloda Bazar", "Balrampur", "Bastar", "Bemetara", "Bijapur", "Bilaspur", "Dantewada", "Dhamtari", "Durg", "Gariaband", "Gaurela Pendra Marwahi", "Janjgir-Champa", "Jashpur", "Kabirdham", "Kanker", "Kondagaon", "Korba", "Koriya", "Mahasamund", "Mungeli", "Narayanpur", "Raigarh", "Raipur", "Rajnandgaon", "Sukma", "Surajpur", "Surguja"]
  },
  "Jharkhand": {
    name: "Jharkhand",
    lat: 23.61,
    lng: 85.27,
    capital: "Ranchi",
    districts: ["Bokaro", "Chatra", "Deoghar", "Dhanbad", "Dumka", "East Singhbhum", "Garhwa", "Giridih", "Godda", "Gumla", "Hazaribagh", "Jamtara", "Khunti", "Koderma", "Latehar", "Lohardaga", "Pakur", "Palamu", "Ramgarh", "Ranchi", "Sahibganj", "Seraikela Kharsawan", "Simdega", "West Singhbhum"]
  },
  "Uttarakhand": {
    name: "Uttarakhand",
    lat: 30.06,
    lng: 79.01,
    capital: "Dehradun",
    districts: ["Almora", "Bageshwar", "Chamoli", "Champawat", "Dehradun", "Haridwar", "Nainital", "Pauri Garhwal", "Pithoragarh", "Rudraprayag", "Tehri Garhwal", "Udham Singh Nagar", "Uttarkashi"]
  },
  "Himachal Pradesh": {
    name: "Himachal Pradesh",
    lat: 31.1,
    lng: 77.17,
    capital: "Shimla",
    districts: ["Bilaspur", "Chamba", "Hamirpur", "Kangra", "Kinnaur", "Kullu", "Lahaul and Spiti", "Mandi", "Shimla", "Sirmaur", "Solan", "Una"]
  },
  "Goa": {
    name: "Goa",
    lat: 15.29,
    lng: 74.12,
    capital: "Panaji",
    districts: ["North Goa", "South Goa"]
  },
  "Jammu and Kashmir": {
    name: "Jammu and Kashmir",
    lat: 33.77,
    lng: 76.57,
    capital: "Srinagar / Jammu",
    districts: ["Anantnag", "Bandipora", "Baramulla", "Budgam", "Doda", "Ganderbal", "Jammu", "Kathua", "Kishtwar", "Kulgam", "Kupwara", "Poonch", "Pulwama", "Rajouri", "Ramban", "Reasi", "Samba", "Shopian", "Srinagar", "Udhampur"]
  },
  "Ladakh": {
    name: "Ladakh",
    lat: 34.15,
    lng: 77.57,
    capital: "Leh",
    districts: ["Leh", "Kargil"]
  },
  "Chandigarh": {
    name: "Chandigarh",
    lat: 30.73,
    lng: 76.77,
    capital: "Chandigarh",
    districts: ["Chandigarh"]
  },
  "Puducherry": {
    name: "Puducherry",
    lat: 11.94,
    lng: 79.8,
    capital: "Puducherry",
    districts: ["Karaikal", "Mahe", "Puducherry", "Yanam"]
  },
  "Tripura": {
    name: "Tripura",
    lat: 23.94,
    lng: 91.98,
    capital: "Agartala",
    districts: ["Dhalai", "Gomati", "Khowai", "North Tripura", "Sepahijala", "South Tripura", "Unakoti", "West Tripura"]
  },
  "Meghalaya": {
    name: "Meghalaya",
    lat: 25.46,
    lng: 91.36,
    capital: "Shillong",
    districts: ["East Garo Hills", "East Jaintia Hills", "East Khasi Hills", "North Garo Hills", "Ri Bhoi", "South Garo Hills", "South West Garo Hills", "South West Khasi Hills", "West Garo Hills", "West Jaintia Hills", "West Khasi Hills"]
  },
  "Manipur": {
    name: "Manipur",
    lat: 24.66,
    lng: 93.9,
    capital: "Imphal",
    districts: ["Bishnupur", "Chandel", "Churachandpur", "Imphal East", "Imphal West", "Jiribam", "Kakching", "Kamjong", "Kangpokpi", "Noney", "Pherzawl", "Senapati", "Tamenglong", "Tengnoupal", "Thoubal", "Ukhrul"]
  },
  "Nagaland": {
    name: "Nagaland",
    lat: 26.15,
    lng: 94.56,
    capital: "Kohima",
    districts: ["Ch\u00fcmoukedima", "Dimapur", "Kiphire", "Kohima", "Longleng", "Mokokchung", "Mon", "Niuland", "Noklak", "Peren", "Phek", "Shamator", "Tseminy\u00fc", "Tuensang", "Wokha", "Z\u00fcnheboto"]
  },
  "Mizoram": {
    name: "Mizoram",
    lat: 23.16,
    lng: 92.93,
    capital: "Aizawl",
    districts: ["Aizawl", "Champhai", "Hnahthial", "Khawzawl", "Kolasib", "Lawngtlai", "Lunglei", "Mamit", "Saitual", "Serchhip", "Siaha"]
  },
  "Arunachal Pradesh": {
    name: "Arunachal Pradesh",
    lat: 28.21,
    lng: 94.72,
    capital: "Itanagar",
    districts: ["Anjaw", "Changlang", "Dibang Valley", "East Kameng", "East Siang", "Kamle", "Kra Daadi", "Kurung Kumey", "Lepa Rada", "Lohit", "Longding", "Lower Dibang Valley", "Lower Siang", "Lower Subansiri", "Namsai", "Pakke Kessang", "Papum Pare", "Shi Yomi", "Siang", "Tawang", "Tirap", "Upper Siang", "Upper Subansiri", "West Kameng", "West Siang"]
  },
  "Sikkim": {
    name: "Sikkim",
    lat: 27.53,
    lng: 88.51,
    capital: "Gangtok",
    districts: ["Gangtok", "Gyalshing", "Mangan", "Namchi", "Pakyong", "Soreng"]
  },
  "Andaman and Nicobar Islands": {
    name: "Andaman and Nicobar Islands",
    lat: 11.74,
    lng: 92.65,
    capital: "Port Blair",
    districts: ["Nicobar", "North and Middle Andaman", "South Andaman"]
  },
  "Dadra and Nagar Haveli and Daman and Diu": {
    name: "Dadra and Nagar Haveli and Daman and Diu",
    lat: 20.42,
    lng: 72.83,
    capital: "Daman",
    districts: ["Dadra and Nagar Haveli", "Daman", "Diu"]
  },
  "Lakshadweep": {
    name: "Lakshadweep",
    lat: 10.56,
    lng: 72.64,
    capital: "Kavaratti",
    districts: ["Lakshadweep"]
  },
};

export const ALL_STATE_NAMES: string[] = Object.keys(INDIA_STATES).sort();

export const ODISHA_DISTRICTS: Record<string, DistrictCentroid> = {
  "Angul": { name: "Angul", lat: 20.84, lng: 85.1, division: "Northern" },
  "Balangir": { name: "Balangir", lat: 20.72, lng: 83.48, division: "Northern" },
  "Balasore": { name: "Balasore", lat: 21.49, lng: 86.93, division: "Central" },
  "Bargarh": { name: "Bargarh", lat: 21.33, lng: 83.62, division: "Northern" },
  "Bhadrak": { name: "Bhadrak", lat: 21.06, lng: 86.5, division: "Central" },
  "Boudh": { name: "Boudh", lat: 20.84, lng: 84.32, division: "Southern" },
  "Cuttack": { name: "Cuttack", lat: 20.46, lng: 85.88, division: "Central" },
  "Deogarh": { name: "Deogarh", lat: 21.53, lng: 84.73, division: "Northern" },
  "Dhenkanal": { name: "Dhenkanal", lat: 20.67, lng: 85.6, division: "Northern" },
  "Gajapati": { name: "Gajapati", lat: 18.81, lng: 84.16, division: "Southern" },
  "Ganjam": { name: "Ganjam", lat: 19.38, lng: 85.05, division: "Southern" },
  "Jagatsinghpur": { name: "Jagatsinghpur", lat: 20.27, lng: 86.17, division: "Central" },
  "Jajpur": { name: "Jajpur", lat: 20.85, lng: 86.33, division: "Central" },
  "Jharsuguda": { name: "Jharsuguda", lat: 21.85, lng: 84.01, division: "Northern" },
  "Kalahandi": { name: "Kalahandi", lat: 19.91, lng: 83.16, division: "Southern" },
  "Kandhamal": { name: "Kandhamal", lat: 20.42, lng: 84.23, division: "Southern" },
  "Kendrapara": { name: "Kendrapara", lat: 20.5, lng: 86.42, division: "Central" },
  "Kendujhar": { name: "Kendujhar", lat: 21.63, lng: 85.58, division: "Northern" },
  "Khurda": { name: "Khurda", lat: 20.19, lng: 85.62, division: "Central" },
  "Koraput": { name: "Koraput", lat: 18.81, lng: 82.71, division: "Southern" },
  "Malkangiri": { name: "Malkangiri", lat: 18.35, lng: 81.9, division: "Southern" },
  "Mayurbhanj": { name: "Mayurbhanj", lat: 21.93, lng: 86.74, division: "Central" },
  "Nabarangpur": { name: "Nabarangpur", lat: 19.23, lng: 82.55, division: "Southern" },
  "Nayagarh": { name: "Nayagarh", lat: 20.13, lng: 85.1, division: "Central" },
  "Nuapada": { name: "Nuapada", lat: 20.83, lng: 82.52, division: "Southern" },
  "Puri": { name: "Puri", lat: 19.81, lng: 85.83, division: "Central" },
  "Rayagada": { name: "Rayagada", lat: 19.17, lng: 83.42, division: "Southern" },
  "Sambalpur": { name: "Sambalpur", lat: 21.47, lng: 83.97, division: "Northern" },
  "Subarnapur": { name: "Subarnapur", lat: 20.84, lng: 83.92, division: "Northern" },
  "Sundargarh": { name: "Sundargarh", lat: 22.12, lng: 84.04, division: "Northern" },
};

export function getStateCentroid(stateName: string): { lat: number; lng: number } | null {
  if (!stateName) return null;
  const normalized = stateName.trim();
  if (STATE_CENTROIDS[normalized]) return STATE_CENTROIDS[normalized];
  const lower = normalized.toLowerCase();
  for (const [key, val] of Object.entries(STATE_CENTROIDS)) {
    if (key.toLowerCase() === lower) return val;
  }
  return null;
}
