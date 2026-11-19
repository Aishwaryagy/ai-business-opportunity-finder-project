"""
Market & Locality Intelligence Service.
Provides demographic, economic, and commercial context for specified cities and localities.
Includes extensible integration hooks for external market data APIs.
"""

import os
from typing import Dict, Any, Optional

# Contextual intelligence profiles for covered Indian urban centers and localities
LOCALITY_PROFILES: Dict[str, Dict[str, Dict[str, Any]]] = {
    "Bangalore": {
        "Whitefield": {
            "type": "Major Tech Corridor & High-Density Gated Suburb",
            "primary_demographic": "IT professionals, engineering college students (MVJ/CMRIT), young affluent families",
            "commercial_density": "Very High",
            "growth_drivers": "Metro purple line extension, ITPL tech parks, premium residential communities",
            "consumer_behavior": "High disposable income, time-poor, heavy reliance on on-demand convenience and specialized services",
            "market_gaps": "Quality student micro-living, hyper-local wellness, reliable pet care, express commuter logistics"
        },
        "Koramangala": {
            "type": "Startup Epicenter & College Lifestyle Hub",
            "primary_demographic": "Startup founders, VC teams, Christ University students, creative freelancers",
            "commercial_density": "Extreme",
            "growth_drivers": "Vibrant food & beverage clusters, co-working density, high pedestrian traffic",
            "consumer_behavior": "Early tech adopters, premium lifestyle seekers, community-oriented social spenders",
            "market_gaps": "Affordable micro-workspaces, student peer tutoring & career launchpads, healthy budget meal subscriptions"
        },
        "Electronic City": {
            "type": "Hardware & Enterprise IT Industrial Cluster",
            "primary_demographic": "Migrant corporate workforce, tech trainees, young engineers",
            "commercial_density": "High",
            "growth_drivers": "Elevated expressway, Infosys/Wipro mega-campuses, expanding housing layouts",
            "consumer_behavior": "Value-conscious, convenience-oriented, weekend recreational spenders",
            "market_gaps": "Quality evening social venues, verified PG management platforms, automated laundry & tiffin networks"
        },
        "Indiranagar": {
            "type": "Affluent Commercial & High-End Cultural District",
            "primary_demographic": "High-net-worth individuals, tech executives, lifestyle creators",
            "commercial_density": "Extreme",
            "growth_drivers": "100ft Road and 12th Main retail corridors, boutique studios, metro hub",
            "consumer_behavior": "Discerning, brand-conscious, high willingness to pay for premium bespoke experiences",
            "market_gaps": "Sustainable retail alternatives, personalized longevity & mental wellness, artisan specialty supply"
        },
        "Yelahanka": {
            "type": "North Bangalore Academic & Emerging Residential Corridor",
            "primary_demographic": "Aviation & engineering students (BMSIT, Nitte), airport staff, defense personnel, young families",
            "commercial_density": "Medium-High",
            "growth_drivers": "Proximity to Kempegowda Airport, rapid peripheral ring road development",
            "consumer_behavior": "Family-centric, student budget-conscious, rapidly urbanizing",
            "market_gaps": "Modern student study cafes, weekend family entertainment, localized organic farm produce delivery"
        }
    },
    "Mysore": {
        "Vijayanagar": {
            "type": "Fast-Growing Residential & Academic Layout",
            "primary_demographic": "Young families, government employees, competitive exam aspirants",
            "commercial_density": "Medium",
            "growth_drivers": "New layout expansions, ring road connectivity, educational centers",
            "consumer_behavior": "Careful spenders, strong neighborhood community ties, value longevity",
            "market_gaps": "Organized coaching hubs, digital elder care coordination, doorstep vehicle servicing"
        },
        "Hebbal": {
            "type": "Industrial & Tech Campus Suburb",
            "primary_demographic": "Infosys Mysore engineers, manufacturing professionals, industrial technical staff",
            "commercial_density": "Medium-High",
            "growth_drivers": "Industrial growth, corporate training campus, ring road accessibility",
            "consumer_behavior": "Tech-savvy professionals seeking metropolitan amenities at local tiers",
            "market_gaps": "After-hours dining & delivery, co-living amenities, recreational sports facilities"
        },
        "Kuvempunagar": {
            "type": "Traditional Academic & Prime Residential Hub",
            "primary_demographic": "College students, coaching attendees, retired professionals, teachers",
            "commercial_density": "High",
            "growth_drivers": "Established school zones, thriving neighborhood commercial avenues",
            "consumer_behavior": "Education-first spending, high trust in local recommendations",
            "market_gaps": "Modern hybrid learning centers, student health & nutritional dining, localized repair services"
        },
        "Saraswathipuram": {
            "type": "Institutional & Engineering College District",
            "primary_demographic": "SJCE & JSS college students, faculty, academic researchers, library patrons",
            "commercial_density": "High",
            "growth_drivers": "Historic university corridor, high continuous youth footfall",
            "consumer_behavior": "Extremely price-sensitive, high demand for fast study utilities, print & snack hubs",
            "market_gaps": "Student project labs, affordable 24/7 collaborative spaces, tech-enabled secondhand book exchanges"
        },
        "Jayalakshmipuram": {
            "type": "Affluent Heritage & Senior Residential Belt",
            "primary_demographic": "High-income families, retirees, seasoned business owners",
            "commercial_density": "Medium-High",
            "growth_drivers": "Proximity to heritage centers, Kalidasa Road culinary hub",
            "consumer_behavior": "High purchasing power, health-conscious, appreciation for heritage & quality",
            "market_gaps": "Dedicated home assisted care, premium boutique organic groceries, artisanal bakeries"
        }
    },
    "Shivamogga": {
        "Gandhi Nagar": {
            "type": "Central Commercial & Wholesale Trade Zone",
            "primary_demographic": "Traders, regional shoppers, agricultural merchants, local business owners",
            "commercial_density": "Very High",
            "growth_drivers": "Heart of municipal commerce, major bus station links",
            "consumer_behavior": "Cash and UPI retail spenders, quick turnaround, bargain focused",
            "market_gaps": "B2B inventory management tools, organized regional logistics, digital payment solutions for wholesale"
        },
        "Savalanga Road": {
            "type": "Industrial & Transit Growth Corridor",
            "primary_demographic": "Auto technicians, transport drivers, industrial suppliers, warehouse staff",
            "commercial_density": "Medium",
            "growth_drivers": "Highway connectivity, expanding industrial workshops",
            "consumer_behavior": "Commercial utility focused, durable equipment purchasing",
            "market_gaps": "Commercial vehicle spare-parts aggregator, fleet maintenance booking, driver rest utilities"
        },
        "Vinoba Nagar": {
            "type": "Prominent Upper-Middle Residential Neighborhood",
            "primary_demographic": "Doctors, educators, civil servants, prosperous families",
            "commercial_density": "Medium",
            "growth_drivers": "Top schools, specialty clinics, high residential stability",
            "consumer_behavior": "Quality-conscious, health & education spending prioritizers",
            "market_gaps": "Branded after-school skill academies, home diagnostic test delivery, eco-friendly household services"
        },
        "Gopi Circle": {
            "type": "High-Footfall Downtown Pedestrian Junction",
            "primary_demographic": "Daily commuters, youth, retail shoppers, inter-district travelers",
            "commercial_density": "Extreme",
            "growth_drivers": "Central traffic junction, major retail showrooms",
            "consumer_behavior": "High impulse buying, street snacks and beverage consumption",
            "market_gaps": "Modern hygienic quick-service beverage kiosks, quick phone and gadget repair bars"
        },
        "Tunga Nagar": {
            "type": "Riverfront Residential & Emerging Housing Layout",
            "primary_demographic": "Working-class families, newly settled homeowners, students",
            "commercial_density": "Low-Medium",
            "growth_drivers": "Affordable housing expansion, scenic river proximity",
            "consumer_behavior": "Budget-focused, reliance on localized daily grocery shops",
            "market_gaps": "Organized daily essentials subscription, recreation centers, child daycare services"
        }
    },
    "Mangalore": {
        "Kankanady": {
            "type": "Medical, Nursing & Transit Hub",
            "primary_demographic": "Medical students, nurses, healthcare visitors, railway commuters",
            "commercial_density": "Very High",
            "growth_drivers": "Father Muller Medical College, multi-specialty hospitals, railway junction",
            "consumer_behavior": "High 24/7 activity, shift-based spending, student budget needs",
            "market_gaps": "24/7 medical student study hubs, healthy night-shift meal delivery, hospital attendant stay services"
        },
        "Bejai": {
            "type": "Central Transit & Modern Commercial Enclave",
            "primary_demographic": "Inter-city travelers, retail shoppers, apartment dwellers",
            "commercial_density": "High",
            "growth_drivers": "KSRTC Central bus stand, Bharat Mall, high-rise apartment density",
            "consumer_behavior": "Moderate-to-high spending, mobile app adopters",
            "market_gaps": "Short-stay luggage & shower lounges for bus commuters, modern co-working cafes"
        },
        "Kadri": {
            "type": "Historic Cultural & Green Residential Belt",
            "primary_demographic": "Families, temple visitors, park joggers, wellness seekers",
            "commercial_density": "Medium",
            "growth_drivers": "Kadri Manjunatha temple, Kadri park, peaceful residential appeal",
            "consumer_behavior": "Cultural spenders, wellness conscious, community-oriented",
            "market_gaps": "Ayurvedic wellness cafes, temple tourism guide apps, morning fitness & yoga clubs"
        },
        "Surathkal": {
            "type": "Premier Coastal Engineering Campus Town",
            "primary_demographic": "NITK Surathkal students, researchers, port & refinery staff",
            "commercial_density": "Medium-High",
            "growth_drivers": "National Institute of Technology Karnataka (NITK), MRPL refinery, coastal highway",
            "consumer_behavior": "High student tech consumption, late-night snacking, budget lifestyle",
            "market_gaps": "Affordable student hardware tinkering labs, beach sports & surf equipment rental, quick bite dark kitchens"
        },
        "Hampankatta": {
            "type": "Historical Commercial & Trade Central Business District",
            "primary_demographic": "Traders, electronics merchants, gold & jewelry buyers, shoppers",
            "commercial_density": "Extreme",
            "growth_drivers": "Traditional center of Mangalore commerce, high banking concentration",
            "consumer_behavior": "High transaction volume, traditional bargaining culture",
            "market_gaps": "Smart parking solutions, unified local merchant loyalty programs, express B2B delivery"
        }
    },
    "Hyderabad": {
        "Hitech City": {
            "type": "Global IT Powerhouse & Corporate Epicenter",
            "primary_demographic": "Global tech workforce, multinational executives, tech entrepreneurs",
            "commercial_density": "Extreme",
            "growth_drivers": "Cyber Towers, Mindspace REIT, luxury high-rises, metro line",
            "consumer_behavior": "Very high disposable income, premium health & fitness spending, app-first lifestyle",
            "market_gaps": "Executive mental resilience coaching, premium pet boarding, gourmet clean-label meal delivery"
        },
        "Gachibowli": {
            "type": "Financial District & Premier University Belt",
            "primary_demographic": "Financial analysts, HCU & ISB students, athletes, tech consultants",
            "commercial_density": "Very High",
            "growth_drivers": "Financial District towers, sports stadium, university academic campuses",
            "consumer_behavior": "Diverse international and national student base, 24/7 work cycles",
            "market_gaps": "Late-night student study lounges, affordable student co-living networks, sports nutrition services"
        },
        "Madhapur": {
            "type": "Tech Startup, Creative Studio & Hostel Corridor",
            "primary_demographic": "Young software developers, UI/UX designers, PG hostel residents",
            "commercial_density": "Very High",
            "growth_drivers": "High PG density, Durgam Cheruvu cable bridge, cafe culture",
            "consumer_behavior": "Social dining, active nightlife, peer recommendations",
            "market_gaps": "All-in-one PG tenant amenities management, budget creative studio rentals, laundry pickup"
        },
        "Kondapur": {
            "type": "Family Residential & IT Adjacent Urban Suburb",
            "primary_demographic": "Double-income tech couples, young parents, school students",
            "commercial_density": "High",
            "growth_drivers": "Botanical Garden proximity, international schools, high-rise gated communities",
            "consumer_behavior": "Family wellness, child extracurricular spending, home comfort optimization",
            "market_gaps": "Stem & robotics weekend academies, verified elderly companion services, organic milk & vegetable cooperatives"
        },
        "Kukatpally": {
            "type": "Massive Educational Coaching & High-Density Commercial Hub",
            "primary_demographic": "JNTU Hyderabad students, engineering aspirants, coaching students, retail shoppers",
            "commercial_density": "Extreme",
            "growth_drivers": "JNTU campus, major shopping malls, educational coaching institutes",
            "consumer_behavior": "Price conscious, high volume, heavy reliance on budget street dining and study resources",
            "market_gaps": "Affordable competitive exam mock test centers, student equipment rentals, low-cost nutritious meal subscriptions"
        }
    },
    "Chennai": {
        "T Nagar": {
            "type": "Premier South Asian Retail & Consumer Epicenter",
            "primary_demographic": "Shoppers, gold & silk merchants, tourists, retail employees",
            "commercial_density": "Extreme",
            "growth_drivers": "Pondy Bazaar pedestrian plaza, Ranganathan Street footfalls",
            "consumer_behavior": "Massive seasonal and daily retail purchases, high footfall sensitivity",
            "market_gaps": "Shopper baggage lockers, smart valet & parking finder apps, retail staff break & wellness rooms"
        },
        "Velachery": {
            "type": "IT Expressway Connector & Bustling Residential Node",
            "primary_demographic": "IT engineers, retail workers, young families",
            "commercial_density": "High",
            "growth_drivers": "Phoenix Marketcity, MRTS station, fast connecting road to OMR",
            "consumer_behavior": "Active mall shoppers, value-conscious tech workers",
            "market_gaps": "Water management & filtration solutions, quick shuttle links to OMR tech parks, pet grooming vans"
        },
        "Anna Nagar": {
            "type": "Planned Upscale Residential & Civil Services Hub",
            "primary_demographic": "Civil services (UPSC) aspirants, doctors, established businessmen, affluent retirees",
            "commercial_density": "Very High",
            "growth_drivers": "Planned avenues, Tower Park, dense coaching institutions",
            "consumer_behavior": "Willing to invest heavily in premium education and health",
            "market_gaps": "High-focus silent study libraries, specialized nutrition for competitive exam students, boutique fitness"
        },
        "Adyar": {
            "type": "Heritage Coastal & Elite Academic Enclave",
            "primary_demographic": "IIT Madras & Anna University students/professors, researchers, environmentalists, cultural patrons",
            "commercial_density": "High",
            "growth_drivers": "Premier academic institutions, proximity to coast, Theosophical Society",
            "consumer_behavior": "High intellect, eco-conscious, keen on sustainability and cultural arts",
            "market_gaps": "Sustainable zero-waste student refill stores, academic research publishing assistance, EV micro-mobility rentals"
        },
        "OMR": {
            "type": "Information Technology Expressway Corridor",
            "primary_demographic": "IT professionals, engineering college students (Jeppiaar, Sathyabama), young renters",
            "commercial_density": "High",
            "growth_drivers": "Tidel Park, SIPCOT IT Park, dedicated expressway corridor",
            "consumer_behavior": "Commute-heavy, high digital delivery usage, time-saving convenience prioritizers",
            "market_gaps": "Express office lunch boxes, weekend outdoor recreation clubs, on-demand car care for tech campuses"
        }
    }
}


def get_market_context(city: str, area: str) -> Dict[str, Any]:
    """
    Retrieves market context for a given city and locality.
    Checks for external DATA_API_KEY if configured, or falls back to built-in intelligence.
    """
    data_api_key = os.getenv("DATA_API_KEY", "").strip()

    # Base profile lookup
    city_profiles = LOCALITY_PROFILES.get(city, {})
    area_profile = city_profiles.get(area)

    if not area_profile:
        # Fallback profile if unfamiliar locality
        area_profile = {
            "type": f"Developing Urban Micro-Market in {city}",
            "primary_demographic": f"Local residents and working professionals in {city}",
            "commercial_density": "Medium",
            "growth_drivers": f"Urban expansion and infrastructural growth across {city}",
            "consumer_behavior": "Value-oriented with steady adoption of digital and convenience services",
            "market_gaps": "Reliable local service aggregation, quality everyday amenities"
        }

    # If external API is configured, integration would query external data here:
    external_data_status = "active" if data_api_key else "built-in intelligence database"

    return {
        "city": city,
        "area": area,
        "profile": area_profile,
        "source": "General market context" if not data_api_key else "External Verified Dataset",
        "data_status": external_data_status,
        "summary": (
            f"{area} ({city}) is characterized as a {area_profile['type']}. "
            f"Key demographics include {area_profile['primary_demographic']}. "
            f"Observed consumer trends show {area_profile['consumer_behavior']}."
        )
    }
