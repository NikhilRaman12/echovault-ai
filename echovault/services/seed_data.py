"""Realistic historical oral history dataset seeder for EchoVault AI."""

import logging
from typing import List, Dict, Any
from echovault.database import db
from echovault.schemas import (
    MemoryRecord,
    MemorySource,
    SourceType,
    ProcessingStatus,
    ExtractedPerson,
    ExtractedPlace,
    ExtractedDate,
    ExtractedQuote,
    AuditEvent,
    AuditAction,
)
from echovault.services.storage_service import storage_service

logger = logging.getLogger(__name__)

REALISTIC_ORAL_HISTORIES: List[Dict[str, Any]] = [
    {
        "id": "mem-hist-001",
        "title": "The Silver Watch on the Savannah Porch",
        "narrator": "Grandmother Mary",
        "event_date_raw": "July 1944",
        "event_date_iso": "1944-07",
        "content": (
            "Right before William shipped out with the 101st Airborne in July 1944, we sat together on the front porch "
            "of the old stone cottage in Savannah. The jasmine was blooming thick and sweet in the evening heat. "
            "He reached into his uniform pocket and pressed his grandfather's silver pocket watch into my palms. "
            "He looked at me and said, 'Keep this ticking until I come through that wooden gate.' "
            "For three long years, I wound that spring every morning at six o'clock sharp before going to work at the telegraph office. "
            "I think the day he finally returned was a Tuesday in October 1947, though Aunt Sarah always swore it was a Wednesday afternoon."
        ),
        "summary": "William entrusts his grandfather's silver pocket watch to Mary on their Savannah porch before departing for Europe in July 1944. She winds it daily until his return in 1947.",
        "uncertainty_notes": "Narrator remembers William's return as a Tuesday in October 1947, whereas Aunt Sarah recalled Wednesday afternoon.",
        "people": [
            {"name": "William", "relationship": "Husband", "context": "Shipped out with the 101st Airborne"},
            {"name": "Mary", "relationship": "Self (Narrator)", "context": "Kept the watch wound and worked at telegraph office"},
            {"name": "Aunt Sarah", "relationship": "Aunt", "context": "Disagreed on the exact weekday of William's return"},
        ],
        "places": [
            {"name": "Savannah, Georgia", "location_type": "city", "context": "Location of the stone cottage with porch"},
            {"name": "Europe", "location_type": "continent", "context": "Military deployment theatre"},
        ],
        "dates": [
            {"raw_date": "July 1944", "iso_year": 1944, "is_approximate": False},
            {"raw_date": "October 1947", "iso_year": 1947, "is_approximate": False},
        ],
        "quotes": [
            {"quote_text": "Keep this ticking until I come through that wooden gate.", "speaker": "William"},
        ],
        "themes": ["military deployment", "homecoming", "wartime romance", "family heirloom"],
    },
    {
        "id": "mem-hist-002",
        "title": "Winter of the Cold Stove in Chicago",
        "narrator": "Great-Uncle Thomas",
        "event_date_raw": "January 1936",
        "event_date_iso": "1936-01",
        "content": (
            "During the deep frost of January 1936 in the Pilsen district of Chicago, the coal trains froze right on the tracks. "
            "Our cast-iron kitchen stove went ice cold for four days straight. My father Josef and mother Helena gathered all four "
            "of us boys in the central parlor under heavy wool blankets sewn from flour sacks. Josef told us, "
            "'As long as we have broth and each other's coats, nobody in this house complains.' "
            "He walked three miles through waist-high snow to the freight yard just to carry back a small sack of coal slag. "
            "Helena believed the merchant charged sixteen cents for that coal, but Josef remembered eighteen cents."
        ),
        "summary": "During the bitter Chicago winter of 1936, the frozen rail lines halted coal supplies. Josef walked through the blizzard to secure coal slag to keep his family warm in Pilsen.",
        "uncertainty_notes": "Helena recalled paying 16 cents for coal slag, whereas Josef remembered 18 cents.",
        "people": [
            {"name": "Josef", "relationship": "Father", "context": "Walked three miles to freight yard for coal"},
            {"name": "Helena", "relationship": "Mother", "context": "Sewed blankets from flour sacks"},
            {"name": "Thomas", "relationship": "Self (Narrator)", "context": "Child in the parlor during the 1936 freeze"},
        ],
        "places": [
            {"name": "Pilsen, Chicago", "location_type": "neighborhood", "context": "Family home during Great Depression"},
            {"name": "Chicago Freight Yard", "location_type": "industrial depot", "context": "Where Josef bought coal slag"},
        ],
        "dates": [
            {"raw_date": "January 1936", "iso_year": 1936, "is_approximate": False},
        ],
        "quotes": [
            {"quote_text": "As long as we have broth and each other's coats, nobody in this house complains.", "speaker": "Josef"},
        ],
        "themes": ["Great Depression", "winter hardship", "resilience", "fatherhood"],
    },
    {
        "id": "mem-hist-003",
        "title": "The Boeing Wing Apprentice on the Duwamish",
        "narrator": "Grandfather Arthur",
        "event_date_raw": "September 1954",
        "event_date_iso": "1954-09",
        "content": (
            "I arrived in Seattle from Idaho on a Greyhound bus with forty-two dollars in my jacket. "
            "In September 1954, I got hired on at Boeing Plant 2 along the Duwamish River as an apprentice riveter on the Model 377 Stratocruiser. "
            "My foreman was an old machinist named Frank Henderson. On my second day, after I ruined three aluminum rivets, "
            "Henderson tapped my shoulder and said, 'Measure with a micrometer, check with your fingers, and sign your work like a man.' "
            "I worked in that factory for thirty-one years until my retirement in 1985. "
            "I can't recall whether Henderson had served in the Navy or the Army Air Corps, but he ran that rivet line like a battleship."
        ),
        "summary": "Arthur moved from Idaho to Seattle in 1954 to apprentice as an aircraft riveter at Boeing Plant 2 under foreman Frank Henderson, beginning a 31-year aerospace career.",
        "uncertainty_notes": "Narrator uncertain whether foreman Frank Henderson served in the Navy or Army Air Corps.",
        "people": [
            {"name": "Arthur", "relationship": "Self (Narrator)", "context": "Boeing aircraft apprentice riveter"},
            {"name": "Frank Henderson", "relationship": "Foreman / Mentor", "context": "Lead machinist at Boeing Plant 2"},
        ],
        "places": [
            {"name": "Boeing Plant 2, Seattle", "location_type": "manufacturing plant", "context": "Aircraft production factory"},
            {"name": "Duwamish River", "location_type": "river", "context": "Waterway adjoining the Boeing airfield"},
            {"name": "Idaho", "location_type": "state", "context": "Arthur's hometown origin"},
        ],
        "dates": [
            {"raw_date": "September 1954", "iso_year": 1954, "is_approximate": False},
            {"raw_date": "1985", "iso_year": 1985, "is_approximate": False},
        ],
        "quotes": [
            {"quote_text": "Measure with a micrometer, check with your fingers, and sign your work like a man.", "speaker": "Frank Henderson"},
        ],
        "themes": ["aviation craftsmanship", "apprenticeship", "work ethic", "Pacific Northwest"],
    },
    {
        "id": "mem-hist-004",
        "title": "The Cedar Chest Journey from Munich",
        "narrator": "Aunt Miriam",
        "event_date_raw": "October 1923",
        "event_date_iso": "1923-10",
        "content": (
            "When Great-Grandmother Elise prepared to leave Bavaria in October 1923, her brother Karl built her a cedar chest "
            "from timber felled behind their workshop. In that chest, she packed three hand-stitched lace tablecloths, her mother's copper kettle, "
            "and a brass door key to their family cottage in Munich. Karl told her, 'The wood remembers the forest it came from.' "
            "She sailed through Ellis Island and settled in Milwaukee, Wisconsin. "
            "That same cedar chest sits in my hallway right now, and if you open the lid, it still smells of Bavarian cedarwood. "
            "The steamship was named either the SS Reliance or the SS Albert Ballin; the manifest paper was water-stained."
        ),
        "summary": "Great-Grandmother Elise carried a handmade Bavarian cedar chest containing family keepsakes through Ellis Island to Milwaukee in 1923.",
        "uncertainty_notes": "Steamship name uncertain due to water-stained manifest (either SS Reliance or SS Albert Ballin).",
        "people": [
            {"name": "Elise", "relationship": "Great-Grandmother", "context": "Emigrated from Bavaria to Wisconsin"},
            {"name": "Karl", "relationship": "Great-Great-Uncle", "context": "Crafted the cedar chest for Elise"},
            {"name": "Miriam", "relationship": "Self (Narrator)", "context": "Keeper of the heirloom chest today"},
        ],
        "places": [
            {"name": "Munich, Bavaria", "location_type": "city", "context": "Ancestral homeland"},
            {"name": "Ellis Island, New York", "location_type": "immigration station", "context": "Port of entry"},
            {"name": "Milwaukee, Wisconsin", "location_type": "city", "context": "Family settlement community"},
        ],
        "dates": [
            {"raw_date": "October 1923", "iso_year": 1923, "is_approximate": False},
        ],
        "quotes": [
            {"quote_text": "The wood remembers the forest it came from.", "speaker": "Karl"},
        ],
        "themes": ["immigration", "family heirlooms", "woodworking", "heritage preservation"],
    },
    {
        "id": "mem-hist-005",
        "title": "First Night Solo over the Blue Ridge",
        "narrator": "Father Robert",
        "event_date_raw": "May 1969",
        "event_date_iso": "1969-05",
        "content": (
            "On a clear night in May 1969, just two months before Apollo 11 landed on the moon, I flew my first night cross-country solo "
            "in a Cessna 172 over the Blue Ridge Mountains of Virginia. Uncle Samuel, who flew transport planes in Korea, gave me his flight goggles "
            "and warned me before takeoff: 'Trust your instruments when the black hills swallow the lights.' "
            "Coming across the ridge near Charlottesville, low valley fog covered the runway lights. I held the glide slope on the needles alone "
            "and touched down softly on runway 21. "
            "I believe the crosswind was roughly twelve knots from the northwest, though my logbook entry was smudged with fuel oil."
        ),
        "summary": "Robert completed his first solo night flight in a Cessna 172 across the Blue Ridge Mountains in May 1969, landing safely in valley fog using instrument navigation.",
        "uncertainty_notes": "Crosswind speed approximate (~12 knots) due to fuel oil smudge in original pilot logbook.",
        "people": [
            {"name": "Robert", "relationship": "Self (Narrator)", "context": "Young pilot completing night flight"},
            {"name": "Uncle Samuel", "relationship": "Uncle / Veteran Pilot", "context": "Korean War transport pilot and mentor"},
        ],
        "places": [
            {"name": "Blue Ridge Mountains, Virginia", "location_type": "mountain range", "context": "Night flight path"},
            {"name": "Charlottesville", "location_type": "city", "context": "Runway landing destination"},
        ],
        "dates": [
            {"raw_date": "May 1969", "iso_year": 1969, "is_approximate": False},
        ],
        "quotes": [
            {"quote_text": "Trust your instruments when the black hills swallow the lights.", "speaker": "Uncle Samuel"},
        ],
        "themes": ["aviation", "night flying", "mentorship", "courage"],
    },
    {
        "id": "mem-hist-006",
        "title": "Bitter Creek Homestead Reclamation",
        "narrator": "Uncle Donald",
        "event_date_raw": "Spring 1948",
        "event_date_iso": "1948-04",
        "content": (
            "Grandfather Benjamin staked eighty acres of hard sagebrush ground along Bitter Creek in Wyoming under the veterans reclamation program in 1948. "
            "We had an old John Deere Model B tractor with iron lugs that rattled your teeth loose. Benjamin dug irrigation ditches with a team of two draft horses "
            "named Prince and Barnaby. Neighbor Carl brought over a sourdough starter that had been kept alive since the 1890s gold rush. "
            "Benjamin stood at the headgate watching the first trickle of mountain water soak into the dry silt and told us, "
            "'The earth gives nothing for free, but it never lies to you.' "
            "We lost either two or three calves in the late April blizzard that first season; memory gets hazy after seventy years."
        ),
        "summary": "In spring 1948, Benjamin reclaimed eighty acres of sagebrush in Wyoming, digging irrigation ditches by hand and establishing the family homestead.",
        "uncertainty_notes": "Exact calf loss during the late April blizzard uncertain (two or three calves).",
        "people": [
            {"name": "Benjamin", "relationship": "Grandfather", "context": "Homestead founder and ditch builder"},
            {"name": "Donald", "relationship": "Self (Narrator)", "context": "Assisted grandfather on Bitter Creek farm"},
            {"name": "Neighbor Carl", "relationship": "Family Neighbor", "context": "Shared historic 1890s sourdough starter"},
        ],
        "places": [
            {"name": "Bitter Creek, Wyoming", "location_type": "homestead / creek", "context": "80-acre reclamation farm"},
        ],
        "dates": [
            {"raw_date": "Spring 1948", "iso_year": 1948, "is_approximate": False},
        ],
        "quotes": [
            {"quote_text": "The earth gives nothing for free, but it never lies to you.", "speaker": "Benjamin"},
        ],
        "themes": ["homesteading", "farming", "Wyoming frontier", "perseverance"],
    },
]


def seed_realistic_archive() -> int:
    """Ingest realistic historical oral histories into EchoVault database."""
    count = 0
    for item in REALISTIC_ORAL_HISTORIES:
        content_hash = storage_service.compute_sha256(item["content"])
        
        # Check duplicate
        if db.find_duplicate_by_hash(content_hash):
            continue

        record = MemoryRecord(
            id=item["id"],
            title=item["title"],
            content=item["content"],
            summary=item["summary"],
            narrator=item["narrator"],
            event_date_raw=item["event_date_raw"],
            event_date_iso=item["event_date_iso"],
            uncertainty_notes=item.get("uncertainty_notes"),
            processing_status=ProcessingStatus.COMPLETED,
            content_hash=content_hash,
            source_type=SourceType.MANUAL_TEXT,
            people=[ExtractedPerson(**p) for p in item.get("people", [])],
            places=[ExtractedPlace(**pl) for pl in item.get("places", [])],
            dates=[ExtractedDate(**d) for d in item.get("dates", [])],
            quotes=[ExtractedQuote(**q) for q in item.get("quotes", [])],
            themes=item.get("themes", []),
        )

        entities = []
        for p in record.people:
            entities.append({"type": "person", "name": p.name, "secondary_value": p.relationship, "context": p.context})
        for pl in record.places:
            entities.append({"type": "place", "name": pl.name, "secondary_value": pl.location_type, "context": pl.context})

        source = MemorySource(
            id=record.id,
            memory_id=record.id,
            source_type=SourceType.MANUAL_TEXT,
            content_sha256=content_hash,
            file_size_bytes=len(item["content"].encode("utf-8")),
        )

        db.insert_memory_record(
            record=record,
            source=source,
            entities=entities,
            themes=record.themes,
            quotes=record.quotes,
        )

        db.record_audit_event(AuditEvent(
            memory_id=record.id,
            action=AuditAction.ARCHIVED,
            agent_name="SeedService",
            details={"title": record.title, "historical_era": record.event_date_raw},
        ))
        count += 1

    return count


if __name__ == "__main__":
    imported = seed_realistic_archive()
    print(f"Successfully seeded {imported} realistic historical oral histories into EchoVault.")
