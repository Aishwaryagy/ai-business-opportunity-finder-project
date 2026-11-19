"""
Global Location & Cascading Subdivision Service (services/location_service.py).
Provides countries worldwide, ISO-3166 country codes, ISO-4217 currency codes,
cost-of-living multipliers (relative to USD baseline for realistic local pricing),
and cascading State/Province -> City/Town -> Local Area/Neighbourhood hierarchies.
Also supports custom manual entry when a user's local neighbourhood is not pre-listed.
"""

from typing import List, Dict, Any, Optional

GLOBAL_LOCATIONS: List[Dict[str, Any]] = [
    {
        "country": "India",
        "iso_code": "IN",
        "currency": "INR",
        "currency_name": "Indian Rupee",
        "currency_symbol": "₹",
        "region": "South Asia",
        "cost_index_usd": 0.28,  # Local cost multiplier vs US baseline
        "states": {
            "Karnataka": {
                "Shivamogga": ["Gandhi Nagar", "Vinoba Nagar", "Gopi Circle", "Savalanga Road", "Tunga Nagar", "Kuvempu Road", "B.H. Road"],
                "Bangalore": ["Whitefield", "Koramangala", "Indiranagar", "Electronic City", "Yelahanka", "Jayanagar", "HSR Layout", "Malleshwaram"],
                "Mysore": ["Vijayanagar", "Kuvempunagar", "Saraswathipuram", "Hebbal", "Jayalakshmipuram", "Gokulam"],
                "Mangalore": ["Kankanady", "Bejai", "Kadri", "Surathkal", "Hampankatta", "Bendoorwell"],
                "Hubli-Dharwad": ["Vidyanagar", "Keshwapur", "Gokul Road", "Saptapur"],
            },
            "Maharashtra": {
                "Mumbai": ["Andheri West", "Bandra", "Powai", "Dadar", "Borivali", "Lower Parel", "Thane West"],
                "Pune": ["Kothrud", "Hinjewadi", "Viman Nagar", "Baner", "Wakad", "Hadapsar"],
                "Nagpur": ["Dharampeth", "Sadar", "Sitabuldi", "Wardha Road"],
            },
            "Telangana": {
                "Hyderabad": ["Hitech City", "Gachibowli", "Madhapur", "Kondapur", "Kukatpally", "Banjara Hills", "Secunderabad"],
                "Warangal": ["Hanamkonda", "Kazipet", "Subedari"],
            },
            "Tamil Nadu": {
                "Chennai": ["T Nagar", "Anna Nagar", "Velachery", "Adyar", "OMR", "Tambaram"],
                "Coimbatore": ["RS Puram", "Gandhipuram", "Peelamedu", "Saravanampatti"],
                "Madurai": ["Anna Nagar", "KK Nagar", "Goripalayam"],
            },
            "Delhi NCR": {
                "New Delhi": ["Connaught Place", "Lajpat Nagar", "Dwarka", "Rohini", "Saket", "Karol Bagh"],
                "Noida": ["Sector 18", "Sector 62", "Greater Noida West", "Sector 15"],
                "Gurugram": ["Cyber City", "Sector 29", "Sohna Road", "Golf Course Road"],
            },
            "Gujarat": {
                "Ahmedabad": ["Navrangpura", "Satellite", "Prahlad Nagar", "Maninagar", "Bopal"],
                "Surat": ["Adajan", "Vesu", "Varachha", "Piplod"],
            },
        },
    },
    {
        "country": "United States",
        "iso_code": "US",
        "currency": "USD",
        "currency_name": "United States Dollar",
        "currency_symbol": "$",
        "region": "North America",
        "cost_index_usd": 1.00,
        "states": {
            "Texas": {
                "Austin": ["Downtown", "South Congress", "Round Rock", "East Austin", "Cedar Park"],
                "Houston": ["Midtown", "The Heights", "Sugar Land", "Katy", "Montrose"],
                "Dallas": ["Deep Ellum", "Uptown", "Plano", "Frisco", "Oak Cliff"],
            },
            "California": {
                "Los Angeles": ["Santa Monica", "Silver Lake", "Pasadena", "Koreatown", "Culver City"],
                "San Diego": ["North Park", "La Jolla", "Gaslamp Quarter", "Chula Vista"],
                "San Jose": ["Willow Glen", "Downtown", "Sunnyvale", "Santa Clara"],
            },
            "New York": {
                "New York City": ["Astoria (Queens)", "Park Slope (Brooklyn)", "Upper West Side", "Harlem", "Flushing"],
                "Buffalo": ["Elmwood Village", "Allentown", "North Buffalo"],
            },
            "Illinois": {
                "Chicago": ["Logan Square", "Wicker Park", "Lincoln Park", "Hyde Park", "Naperville"],
            },
            "Florida": {
                "Miami": ["Wynwood", "Coral Gables", "Little Havana", "Brickell", "Doral"],
                "Orlando": ["Winter Park", "Lake Nona", "Downtown Orlando", "Kissimmee"],
            },
        },
    },
    {
        "country": "United Kingdom",
        "iso_code": "GB",
        "currency": "GBP",
        "currency_name": "British Pound Sterling",
        "currency_symbol": "£",
        "region": "Europe",
        "cost_index_usd": 0.95,
        "states": {
            "England": {
                "London": ["Shoreditch", "Camden", "Croydon", "Wembley", "Greenwich", "Brixton"],
                "Manchester": ["Northern Quarter", "Didsbury", "Salford", "Ancoats"],
                "Birmingham": ["Digbeth", "Edgbaston", "Jewellery Quarter", "Solihull"],
                "Leeds": ["Headingley", "Chapel Allerton", "City Centre"],
            },
            "Scotland": {
                "Edinburgh": ["Leith", "Stockbridge", "Morningside", "Old Town"],
                "Glasgow": ["West End", "Merchant City", "Shawlands", "Finnieston"],
            },
            "Wales": {
                "Cardiff": ["Cardiff Bay", "Pontcanna", "Roath", "Cathays"],
            },
        },
    },
    {
        "country": "Germany",
        "iso_code": "DE",
        "currency": "EUR",
        "currency_name": "Euro",
        "currency_symbol": "€",
        "region": "Europe",
        "cost_index_usd": 0.90,
        "states": {
            "Berlin": {
                "Berlin": ["Kreuzberg", "Prenzlauer Berg", "Mitte", "Neukölln", "Charlottenburg"],
            },
            "Bavaria": {
                "Munich": ["Schwabing", "Maxvorstadt", "Sendling", "Bogenhausen"],
                "Nuremberg": ["Altstadt", "Gostenhof", "St. Johannis"],
            },
            "North Rhine-Westphalia": {
                "Cologne": ["Ehrenfeld", "Belgisches Viertel", "Nippes", "Deutz"],
                "Düsseldorf": ["Bilk", "Flingern", "Oberkassel"],
            },
        },
    },
    {
        "country": "France",
        "iso_code": "FR",
        "currency": "EUR",
        "currency_name": "Euro",
        "currency_symbol": "€",
        "region": "Europe",
        "cost_index_usd": 0.88,
        "states": {
            "Île-de-France": {
                "Paris": ["11e Popincourt", "Montmartre (18e)", "Marais", "Quartier Latin", "Boulogne-Billancourt"],
            },
            "Auvergne-Rhône-Alpes": {
                "Lyon": ["Croix-Rousse", "Part-Dieu", "Confluence", "Villeurbanne"],
            },
            "Provence-Alpes-Côte d'Azur": {
                "Marseille": ["Vieux-Port", "Cours Julien", "Le Panier", "Prado"],
            },
        },
    },
    {
        "country": "Japan",
        "iso_code": "JP",
        "currency": "JPY",
        "currency_name": "Japanese Yen",
        "currency_symbol": "¥",
        "region": "East Asia",
        "cost_index_usd": 0.82,
        "states": {
            "Tokyo": {
                "Tokyo": ["Shibuya", "Shinjuku", "Setagaya", "Kichijoji", "Akihabara", "Asakusa"],
            },
            "Osaka": {
                "Osaka": ["Namba", "Umeda", "Tennoji", "Shinsaibashi", "Sakai"],
            },
            "Aichi": {
                "Nagoya": ["Sakae", "Meieki", "Osu", "Kanayama"],
            },
        },
    },
    {
        "country": "Canada",
        "iso_code": "CA",
        "currency": "CAD",
        "currency_name": "Canadian Dollar",
        "currency_symbol": "CA$",
        "region": "North America",
        "cost_index_usd": 0.86,
        "states": {
            "Ontario": {
                "Toronto": ["Kensington Market", "Scarborough", "North York", "Liberty Village", "Mississauga"],
                "Ottawa": ["ByWard Market", "glebe", "Kanata", "Centretown"],
            },
            "British Columbia": {
                "Vancouver": ["Kitsilano", "Mount Pleasant", "Richmond", "Burnaby", "Surrey"],
            },
            "Quebec": {
                "Montreal": ["Plateau-Mont-Royal", "Mile End", "Verdun", "Downtown"],
            },
        },
    },
    {
        "country": "Australia",
        "iso_code": "AU",
        "currency": "AUD",
        "currency_name": "Australian Dollar",
        "currency_symbol": "A$",
        "region": "Oceania",
        "cost_index_usd": 0.92,
        "states": {
            "New South Wales": {
                "Sydney": ["Parramatta", "Surry Hills", "Newtown", "Chatswood", "Bondi"],
            },
            "Victoria": {
                "Melbourne": ["Fitzroy", "Brunswick", "South Yarra", "Footscray", "Box Hill"],
            },
            "Queensland": {
                "Brisbane": ["Fortitude Valley", "West End", "South Bank", "Chermside"],
            },
        },
    },
    {
        "country": "United Arab Emirates",
        "iso_code": "AE",
        "currency": "AED",
        "currency_name": "UAE Dirham",
        "currency_symbol": "AED ",
        "region": "Middle East",
        "cost_index_usd": 0.78,
        "states": {
            "Dubai": {
                "Dubai": ["Business Bay", "Deira", "Jumeirah Lake Towers (JLT)", "Al Barsha", "Karama", "Dubai Marina"],
            },
            "Abu Dhabi": {
                "Abu Dhabi": ["Al Reem Island", "Khalifa City", "Hamdan Street", "Mussafah"],
            },
            "Sharjah": {
                "Sharjah": ["Al Nahda", "Al Majaz", "Muwaileh"],
            },
        },
    },
    {
        "country": "Singapore",
        "iso_code": "SG",
        "currency": "SGD",
        "currency_name": "Singapore Dollar",
        "currency_symbol": "S$",
        "region": "Southeast Asia",
        "cost_index_usd": 0.94,
        "states": {
            "Central Region": {
                "Singapore": ["Tanjong Pagar", "Bugis", "Toa Payoh", "Queenstown", "Orchard"],
            },
            "East Region": {
                "Singapore East": ["Tampines", "Bedok", "Pasir Ris", "Paya Lebar"],
            },
            "West Region": {
                "Singapore West": ["Jurong East", "Clementi", "Bukit Batok"],
            },
        },
    },
    {
        "country": "Nigeria",
        "iso_code": "NG",
        "currency": "NGN",
        "currency_name": "Nigerian Naira",
        "currency_symbol": "₦",
        "region": "Africa",
        "cost_index_usd": 0.25,
        "states": {
            "Lagos State": {
                "Lagos": ["Ikeja", "Yaba", "Lekki", "Surulere", "Victoria Island"],
            },
            "Federal Capital Territory": {
                "Abuja": ["Wuse", "Garki", "Maitama", "Gwarinpa"],
            },
        },
    },
    {
        "country": "Kenya",
        "iso_code": "KE",
        "currency": "KES",
        "currency_name": "Kenyan Shilling",
        "currency_symbol": "KSh ",
        "region": "Africa",
        "cost_index_usd": 0.28,
        "states": {
            "Nairobi County": {
                "Nairobi": ["Westlands", "Kilimani", "CBD", "Kasarani", "Embakasi"],
            },
            "Mombasa County": {
                "Mombasa": ["Nyali", "Mvita", "Bamburi"],
            },
        },
    },
    {
        "country": "South Africa",
        "iso_code": "ZA",
        "currency": "ZAR",
        "currency_name": "South African Rand",
        "currency_symbol": "R",
        "region": "Africa",
        "cost_index_usd": 0.42,
        "states": {
            "Gauteng": {
                "Johannesburg": ["Sandton", "Rosebank", "Soweto", "Midrand", "Braamfontein"],
                "Pretoria": ["Hatfield", "Menlyn", "Centurion"],
            },
            "Western Cape": {
                "Cape Town": ["Sea Point", "Woodstock", "Bellville", "Claremont"],
            },
        },
    },
    {
        "country": "Brazil",
        "iso_code": "BR",
        "currency": "BRL",
        "currency_name": "Brazilian Real",
        "currency_symbol": "R$",
        "region": "South America",
        "cost_index_usd": 0.45,
        "states": {
            "São Paulo": {
                "São Paulo": ["Pinheiros", "Vila Mariana", "Moema", "Itaim Bibi", "Tatuapé"],
                "Campinas": ["Cambuí", "Barão Geraldo", "Centro"],
            },
            "Rio de Janeiro": {
                "Rio de Janeiro": ["Botafogo", "Copacabana", "Tijuca", "Barra da Tijuca"],
            },
        },
    },
    {
        "country": "Mexico",
        "iso_code": "MX",
        "currency": "MXN",
        "currency_name": "Mexican Peso",
        "currency_symbol": "MX$",
        "region": "North America",
        "cost_index_usd": 0.46,
        "states": {
            "Mexico City (CDMX)": {
                "Mexico City": ["Roma Norte", "Condesa", "Polanco", "Coyoacán", "Del Valle"],
            },
            "Jalisco": {
                "Guadalajara": ["Zapopan", "Chapultepec", "Providencia", "Tlaquepaque"],
            },
            "Nuevo León": {
                "Monterrey": ["San Pedro Garza García", "Barrio Antiguo", "Cumbres"],
            },
        },
    },
    {
        "country": "Indonesia",
        "iso_code": "ID",
        "currency": "IDR",
        "currency_name": "Indonesian Rupiah",
        "currency_symbol": "Rp",
        "region": "Southeast Asia",
        "cost_index_usd": 0.30,
        "states": {
            "DKI Jakarta": {
                "Jakarta": ["Kebayoran Baru", "Menteng", "Kemang", "Kelapa Gading", "Tebet"],
            },
            "West Java": {
                "Bandung": ["Dago", "Braga", "Setiabudi", "buahbatu"],
            },
            "Bali": {
                "Denpasar": ["Canggu", "Ubud", "Seminyak", "Sanur"],
            },
        },
    },
    {
        "country": "Philippines",
        "iso_code": "PH",
        "currency": "PHP",
        "currency_name": "Philippine Peso",
        "currency_symbol": "₱",
        "region": "Southeast Asia",
        "cost_index_usd": 0.32,
        "states": {
            "Metro Manila (NCR)": {
                "Quezon City": ["Diliman", "Cubao", "Eastwood", "Katipunan"],
                "Makati": ["Poblacion", "Salcedo Village", "Legazpi Village"],
                "Taguig": ["Bonifacio Global City (BGC)", "McKinley Hill"],
            },
            "Central Visayas": {
                "Cebu City": ["IT Park", "Lahug", "Banilad", "Mabolo"],
            },
        },
    },
]


def get_all_countries(search_query: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Returns list of supported countries with ISO codes, official currencies,
    and cascading state/city/area hierarchy. Supports optional search filtering.
    """
    if not search_query or not search_query.strip():
        return GLOBAL_LOCATIONS

    q = search_query.strip().lower()
    return [
        c for c in GLOBAL_LOCATIONS
        if q in c["country"].lower()
        or q in c["iso_code"].lower()
        or q in c["currency"].lower()
        or q in c["region"].lower()
    ]


def get_country_record(country_or_iso: str) -> Dict[str, Any]:
    """Looks up a country by name or ISO-3166 alpha-2 code. Falls back to India if not found."""
    clean = (country_or_iso or "").strip().lower()
    for item in GLOBAL_LOCATIONS:
        if item["country"].lower() == clean or item["iso_code"].lower() == clean:
            return item
    # If user enters a custom country not in the list, return a dynamic profile
    if clean:
        return {
            "country": country_or_iso.strip(),
            "iso_code": country_or_iso.strip()[:2].upper(),
            "currency": "USD",
            "currency_name": "United States Dollar",
            "currency_symbol": "$",
            "region": "Global",
            "cost_index_usd": 0.60,
            "states": {},
        }
    return GLOBAL_LOCATIONS[0]


def get_subdivisions_for_country(country_or_iso: str) -> Dict[str, Any]:
    """
    Returns the cascading subdivisions (States -> Cities -> Neighbourhoods)
    for a given country or ISO code.
    """
    record = get_country_record(country_or_iso)
    states_map = record.get("states", {})
    return {
        "country": record["country"],
        "iso_code": record["iso_code"],
        "currency": record["currency"],
        "currency_name": record["currency_name"],
        "currency_symbol": record["currency_symbol"],
        "cost_index_usd": record["cost_index_usd"],
        "states": list(states_map.keys()),
        "hierarchy": states_map,
    }


def get_legacy_city_areas_mapping() -> Dict[str, List[str]]:
    """
    Returns flat city -> areas mapping for backward compatibility with `/api/locations`.
    Includes all Indian cities from Karnataka, Telangana, Tamil Nadu, Maharashtra, etc.
    """
    flat: Dict[str, List[str]] = {}
    for country in GLOBAL_LOCATIONS:
        for state_cities in country.get("states", {}).values():
            for city_name, areas in state_cities.items():
                flat[city_name] = areas
    return flat
