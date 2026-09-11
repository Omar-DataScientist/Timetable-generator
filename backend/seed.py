"""
Seed script — populates the database with realistic sample data.

Run with:
    python seed.py

Entities created:
  - 8 Subjects (mix of theory-only, lab-included)
  - 4 Divisions (CS-A, CS-B, IT-A, IT-B)
  - 10 Faculty (each mapped to 2–3 subjects)
  - 6 Rooms (4 Theory, 2 Labs)
"""

import asyncio
import logging

from app.database import async_session, create_tables
from app.models import (
    Division,
    DivisionSubject,
    Faculty,
    FacultySubject,
    Room,
    RoomType,
    Subject,
)

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)


async def seed():
    await create_tables()
    async with async_session() as db:
        # ---------------------------------------------------------------
        # 1. Subjects
        # ---------------------------------------------------------------
        subjects_data = [
            ("Data Structures & Algorithms", "DSA",  3, 2),
            ("Database Management Systems",  "DBMS", 3, 2),
            ("Operating Systems",            "OS",   4, 0),
            ("Computer Networks",            "CN",   3, 2),
            ("Mathematics III",              "M3",   4, 0),
            ("Engineering Physics",          "PHY",  2, 2),
            ("Technical Communication",      "TC",   2, 0),
            ("Software Engineering",         "SE",   3, 0),
        ]

        subjects = []
        for name, code, t, l in subjects_data:
            s = Subject(name=name, code=code, theory_hours_per_week=t, lab_hours_per_week=l)
            db.add(s)
            subjects.append(s)
        await db.flush()
        log.info(f"✓ Created {len(subjects)} subjects")

        # Map name → subject for easy lookup
        subj_map = {s.code: s for s in subjects}

        # ---------------------------------------------------------------
        # 2. Rooms
        # ---------------------------------------------------------------
        rooms_data = [
            ("Room 101", RoomType.THEORY, 60),
            ("Room 102", RoomType.THEORY, 60),
            ("Room 201", RoomType.THEORY, 60),
            ("Room 202", RoomType.THEORY, 60),
            ("Lab A",    RoomType.LAB,    30),
            ("Lab B",    RoomType.LAB,    30),
        ]
        rooms = []
        for name, rtype, cap in rooms_data:
            r = Room(name=name, room_type=rtype, capacity=cap)
            db.add(r)
            rooms.append(r)
        await db.flush()
        log.info(f"✓ Created {len(rooms)} rooms (4 theory, 2 labs)")

        # ---------------------------------------------------------------
        # 3. Faculty (10 members)
        # ---------------------------------------------------------------
        faculty_data = [
            ("Dr. Alice Sharma",    "FAC001", ["DSA", "SE"]),
            ("Prof. Bob Mehta",     "FAC002", ["DBMS", "DSA"]),
            ("Dr. Carol Patel",     "FAC003", ["OS", "CN"]),
            ("Prof. David Kumar",   "FAC004", ["CN", "DBMS"]),
            ("Dr. Eva Reddy",       "FAC005", ["M3"]),
            ("Prof. Frank Singh",   "FAC006", ["PHY"]),
            ("Dr. Grace Iyer",      "FAC007", ["TC", "SE"]),
            ("Prof. Harish Nair",   "FAC008", ["OS", "SE"]),
            ("Dr. Iris Verma",      "FAC009", ["DSA", "M3"]),
            ("Prof. James Rao",     "FAC010", ["DBMS", "CN"]),
        ]
        faculty_objs = []
        for name, emp_id, subject_codes in faculty_data:
            f = Faculty(name=name, employee_id=emp_id)
            db.add(f)
            await db.flush()
            for code in subject_codes:
                if code in subj_map:
                    db.add(FacultySubject(faculty_id=f.id, subject_id=subj_map[code].id))
            faculty_objs.append(f)
        await db.flush()
        log.info(f"✓ Created {len(faculty_objs)} faculty members with subject mappings")

        # ---------------------------------------------------------------
        # 4. Divisions (4 divisions)
        # ---------------------------------------------------------------
        # CS divisions study all 8 subjects
        # IT divisions study a subset (DSA, DBMS, OS, CN, M3, PHY)
        cs_subjects = ["DSA", "DBMS", "OS", "CN", "M3", "PHY", "TC", "SE"]
        it_subjects = ["DSA", "DBMS", "OS", "CN", "M3", "PHY"]

        divisions_data = [
            ("CS Division A", "CS-A", cs_subjects),
            ("CS Division B", "CS-B", cs_subjects),
            ("IT Division A", "IT-A", it_subjects),
            ("IT Division B", "IT-B", it_subjects),
        ]
        for name, code, subject_codes in divisions_data:
            d = Division(name=name, code=code)
            db.add(d)
            await db.flush()
            for sc in subject_codes:
                if sc in subj_map:
                    db.add(DivisionSubject(division_id=d.id, subject_id=subj_map[sc].id))
        await db.flush()
        log.info(f"✓ Created {len(divisions_data)} divisions with curriculum mappings")

        await db.commit()
        log.info("\n✅ Seed complete! Database is ready for timetable generation.")
        log.info("   Run the backend server and POST /api/timetable/solve to generate a schedule.")


if __name__ == "__main__":
    asyncio.run(seed())
