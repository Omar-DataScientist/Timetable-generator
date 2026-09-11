"""
OR-Tools CP-SAT Timetable Solver
=================================
Implements all hard constraints and the day-minimization objective
using Google OR-Tools Constraint Programming SAT solver.

Decision Variable:
    X[d, s, type, f, r, t] = 1 if Division d studies Subject s
    (of type Theory/Lab) with Faculty f in Room r at Timeslot t.

Timeslot encoding: t = day * 10 + slot  (day ∈ [0..4], slot ∈ [0..9])
    → 50 total timeslots per week.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

from ortools.sat.python import cp_model

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

NUM_DAYS = 5
SLOTS_PER_DAY = 10
TOTAL_SLOTS = NUM_DAYS * SLOTS_PER_DAY  # 50

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
SLOT_TIMES = [
    "8:00 AM", "9:00 AM", "10:00 AM", "11:00 AM", "12:00 PM",
    "1:00 PM", "2:00 PM", "3:00 PM", "4:00 PM", "5:00 PM",
]


# ---------------------------------------------------------------------------
# Data classes for solver input
# ---------------------------------------------------------------------------

@dataclass
class DivisionData:
    id: int
    name: str
    code: str
    subject_ids: list[int] = field(default_factory=list)


@dataclass
class SubjectData:
    id: int
    name: str
    code: str
    theory_hours: int = 0
    lab_hours: int = 0


@dataclass
class FacultyData:
    id: int
    name: str
    subject_ids: list[int] = field(default_factory=list)


@dataclass
class RoomData:
    id: int
    name: str
    room_type: str  # "THEORY" or "LAB"


@dataclass
class SolverInput:
    divisions: list[DivisionData]
    subjects: list[SubjectData]
    faculty: list[FacultyData]
    rooms: list[RoomData]


@dataclass
class ScheduledClass:
    """A single class assignment in the solution."""
    division_id: int
    subject_id: int
    class_type: str  # "THEORY" or "LAB"
    faculty_id: int
    room_id: int
    day: int      # 0-4
    slot: int     # 0-9


@dataclass
class SolverResult:
    status: str  # "OPTIMAL", "FEASIBLE", "INFEASIBLE", "ERROR"
    assignments: list[ScheduledClass]
    objective_value: int | None = None
    total_active_days: int | None = None
    wall_time: float = 0.0
    log: str = ""


# ---------------------------------------------------------------------------
# Solver
# ---------------------------------------------------------------------------

class TimetableSolver:
    """
    CP-SAT based university timetable scheduler.

    Builds the model, adds all hard constraints, sets the objective,
    and solves to find the optimal (or feasible) schedule.
    """

    def __init__(self, data: SolverInput, time_limit: int = 120, num_workers: int = 8):
        self.data = data
        self.time_limit = time_limit
        self.num_workers = num_workers

        # Lookup maps
        self.subjects_by_id: dict[int, SubjectData] = {s.id: s for s in data.subjects}
        self.faculty_by_id: dict[int, FacultyData] = {f.id: f for f in data.faculty}
        self.rooms_by_id: dict[int, RoomData] = {r.id: r for r in data.rooms}

        # Pre-compute valid mappings
        self.faculty_for_subject: dict[int, list[int]] = {}
        for f in data.faculty:
            for sid in f.subject_ids:
                self.faculty_for_subject.setdefault(sid, []).append(f.id)

        self.theory_rooms = [r.id for r in data.rooms if r.room_type == "THEORY"]
        self.lab_rooms = [r.id for r in data.rooms if r.room_type == "LAB"]

        # Model & variables
        self.model = cp_model.CpModel()
        self.X: dict[tuple, cp_model.IntVar] = {}  # (d, s, type, f, r, t) → BoolVar
        self.Y: dict[tuple, cp_model.IntVar] = {}  # (d, day) → BoolVar (active day)

    def _create_variables(self):
        """Create pruned decision variables — only feasible combinations."""
        for div in self.data.divisions:
            for sid in div.subject_ids:
                subj = self.subjects_by_id.get(sid)
                if not subj:
                    continue

                faculty_ids = self.faculty_for_subject.get(sid, [])
                if not faculty_ids:
                    logger.warning(f"No faculty for subject {subj.code} — skipping")
                    continue

                # Theory variables
                if subj.theory_hours > 0:
                    for fid in faculty_ids:
                        for rid in self.theory_rooms:
                            for t in range(TOTAL_SLOTS):
                                key = (div.id, sid, "THEORY", fid, rid, t)
                                self.X[key] = self.model.new_bool_var(
                                    f"X_d{div.id}_s{sid}_T_f{fid}_r{rid}_t{t}"
                                )

                # Lab variables
                if subj.lab_hours > 0:
                    for fid in faculty_ids:
                        for rid in self.lab_rooms:
                            for t in range(TOTAL_SLOTS):
                                key = (div.id, sid, "LAB", fid, rid, t)
                                self.X[key] = self.model.new_bool_var(
                                    f"X_d{div.id}_s{sid}_L_f{fid}_r{rid}_t{t}"
                                )

        # Active-day boolean variables Y[d, day]
        for div in self.data.divisions:
            for day in range(NUM_DAYS):
                self.Y[(div.id, day)] = self.model.new_bool_var(
                    f"Y_d{div.id}_day{day}"
                )

        logger.info(f"Created {len(self.X)} X-variables and {len(self.Y)} Y-variables")

    def _get_vars_for(self, **filters) -> list[cp_model.IntVar]:
        """Get all X variables matching the given filter criteria."""
        result = []
        for (d, s, ctype, f, r, t), var in self.X.items():
            match = True
            if "div_id" in filters and d != filters["div_id"]:
                match = False
            if "subject_id" in filters and s != filters["subject_id"]:
                match = False
            if "class_type" in filters and ctype != filters["class_type"]:
                match = False
            if "faculty_id" in filters and f != filters["faculty_id"]:
                match = False
            if "room_id" in filters and r != filters["room_id"]:
                match = False
            if "timeslot" in filters and t != filters["timeslot"]:
                match = False
            if "day" in filters and (t // SLOTS_PER_DAY) != filters["day"]:
                match = False
            if "slot" in filters and (t % SLOTS_PER_DAY) != filters["slot"]:
                match = False
            if match:
                result.append(var)
        return result

    def _get_keyed_vars_for(self, **filters) -> list[tuple[tuple, cp_model.IntVar]]:
        """Like _get_vars_for but returns keys too."""
        result = []
        for (d, s, ctype, f, r, t), var in self.X.items():
            match = True
            if "div_id" in filters and d != filters["div_id"]:
                match = False
            if "subject_id" in filters and s != filters["subject_id"]:
                match = False
            if "class_type" in filters and ctype != filters["class_type"]:
                match = False
            if "faculty_id" in filters and f != filters["faculty_id"]:
                match = False
            if "room_id" in filters and r != filters["room_id"]:
                match = False
            if "timeslot" in filters and t != filters["timeslot"]:
                match = False
            if "day" in filters and (t // SLOTS_PER_DAY) != filters["day"]:
                match = False
            if "slot" in filters and (t % SLOTS_PER_DAY) != filters["slot"]:
                match = False
            if match:
                result.append(((d, s, ctype, f, r, t), var))
        return result

    # -------------------------------------------------------------------
    # Hard Constraints
    # -------------------------------------------------------------------

    def _add_faculty_clash_constraint(self):
        """C1: A faculty member can only teach at most 1 class per timeslot."""
        for f in self.data.faculty:
            for t in range(TOTAL_SLOTS):
                vars_ = self._get_vars_for(faculty_id=f.id, timeslot=t)
                if vars_:
                    self.model.add(sum(vars_) <= 1)

    def _add_division_clash_constraint(self):
        """C2: A division can attend at most 1 class per timeslot."""
        for div in self.data.divisions:
            for t in range(TOTAL_SLOTS):
                vars_ = self._get_vars_for(div_id=div.id, timeslot=t)
                if vars_:
                    self.model.add(sum(vars_) <= 1)

    def _add_room_clash_constraint(self):
        """C3: A room can host at most 1 class per timeslot.
        Room-type matching is enforced at variable creation (C4)."""
        all_rooms = [r.id for r in self.data.rooms]
        for rid in all_rooms:
            for t in range(TOTAL_SLOTS):
                vars_ = self._get_vars_for(room_id=rid, timeslot=t)
                if vars_:
                    self.model.add(sum(vars_) <= 1)

    def _add_curriculum_constraint(self):
        """C5: Exact number of weekly theory and lab hours must be scheduled."""
        for div in self.data.divisions:
            for sid in div.subject_ids:
                subj = self.subjects_by_id.get(sid)
                if not subj:
                    continue

                # Theory hours
                if subj.theory_hours > 0:
                    theory_vars = self._get_vars_for(
                        div_id=div.id, subject_id=sid, class_type="THEORY"
                    )
                    if theory_vars:
                        self.model.add(sum(theory_vars) == subj.theory_hours)
                    else:
                        logger.error(
                            f"Cannot schedule {subj.theory_hours} theory hours for "
                            f"div={div.code} subj={subj.code}: no variables"
                        )

                # Lab hours
                if subj.lab_hours > 0:
                    lab_vars = self._get_vars_for(
                        div_id=div.id, subject_id=sid, class_type="LAB"
                    )
                    if lab_vars:
                        self.model.add(sum(lab_vars) == subj.lab_hours)
                    else:
                        logger.error(
                            f"Cannot schedule {subj.lab_hours} lab hours for "
                            f"div={div.code} subj={subj.code}: no variables"
                        )

    def _add_daily_workload_constraint(self):
        """C6: No division can have more than 8 hours of classes per day."""
        for div in self.data.divisions:
            for day in range(NUM_DAYS):
                vars_ = self._get_vars_for(div_id=div.id, day=day)
                if vars_:
                    self.model.add(sum(vars_) <= 8)

    def _add_max_break_constraint(self):
        """C7: Gap between first and last class cannot contain > 1 hour of empty time.
        
        For each division+day: last_slot - first_slot + 1 - num_classes <= 1
        
        We model first_slot and last_slot as integer variables and link them
        to the boolean assignment variables.
        """
        for div in self.data.divisions:
            for day in range(NUM_DAYS):
                # Collect all slots that have any class for this division on this day
                slot_has_class: dict[int, list[cp_model.IntVar]] = {}
                for slot in range(SLOTS_PER_DAY):
                    vars_ = self._get_vars_for(div_id=div.id, day=day, slot=slot)
                    if vars_:
                        slot_has_class[slot] = vars_

                if not slot_has_class:
                    continue

                # B[slot] = 1 if this division has any class in this slot on this day
                B = {}
                for slot in range(SLOTS_PER_DAY):
                    B[slot] = self.model.new_bool_var(f"B_d{div.id}_day{day}_s{slot}")
                    vars_ = slot_has_class.get(slot, [])
                    if vars_:
                        # B[slot] = 1 iff any class scheduled
                        self.model.add_max_equality(B[slot], vars_)
                    else:
                        self.model.add(B[slot] == 0)

                # num_classes = sum of B[slot]
                num_classes = sum(B[slot] for slot in range(SLOTS_PER_DAY))

                # first_slot: integer variable [0..9]
                first_slot = self.model.new_int_var(0, SLOTS_PER_DAY - 1, f"first_d{div.id}_day{day}")
                # last_slot: integer variable [0..9]
                last_slot = self.model.new_int_var(0, SLOTS_PER_DAY - 1, f"last_d{div.id}_day{day}")

                # has_any_class on this day
                has_any = self.Y[(div.id, day)]

                # Link first_slot: first_slot <= slot for every active slot
                # first_slot >= slot for the earliest active slot
                for slot in range(SLOTS_PER_DAY):
                    # If B[slot] == 1, then first_slot <= slot
                    self.model.add(first_slot <= slot).only_enforce_if(B[slot])
                    # If B[slot] == 1, then last_slot >= slot
                    self.model.add(last_slot >= slot).only_enforce_if(B[slot])

                # first_slot must be an active slot (if any classes exist)
                # first_slot >= all inactive slots before it
                # We enforce: if B[slot]=0 then first_slot != slot (via: first_slot <= slot-1 OR first_slot >= slot+1)
                # Simpler: first_slot is the min of active slots
                # Use: for each slot, if first_slot == slot then B[slot] must be 1
                for slot in range(SLOTS_PER_DAY):
                    is_first = self.model.new_bool_var(f"isFirst_d{div.id}_day{day}_s{slot}")
                    self.model.add(first_slot == slot).only_enforce_if(is_first)
                    self.model.add(first_slot != slot).only_enforce_if(is_first.negated())
                    # If this is the first slot, it must have a class
                    self.model.add(B[slot] == 1).only_enforce_if(is_first, has_any)

                for slot in range(SLOTS_PER_DAY):
                    is_last = self.model.new_bool_var(f"isLast_d{div.id}_day{day}_s{slot}")
                    self.model.add(last_slot == slot).only_enforce_if(is_last)
                    self.model.add(last_slot != slot).only_enforce_if(is_last.negated())
                    self.model.add(B[slot] == 1).only_enforce_if(is_last, has_any)

                # Span = last_slot - first_slot + 1
                span = self.model.new_int_var(0, SLOTS_PER_DAY, f"span_d{div.id}_day{day}")
                self.model.add(span == last_slot - first_slot + 1).only_enforce_if(has_any)
                self.model.add(span == 0).only_enforce_if(has_any.negated())

                # Gap = span - num_classes <= 1 (when has_any)
                gap = self.model.new_int_var(0, SLOTS_PER_DAY, f"gap_d{div.id}_day{day}")
                self.model.add(gap == span - num_classes).only_enforce_if(has_any)
                self.model.add(gap == 0).only_enforce_if(has_any.negated())
                self.model.add(gap <= 1)

    def _add_double_theory_constraint(self):
        """C8: Double-theory subject limit.
        
        - At most ONE subject per day can have 2 theory classes for a division.
        - If a subject has 2 theory classes on the same day, they CANNOT be consecutive.
        - All other subjects: max 1 theory class per day.
        """
        for div in self.data.divisions:
            for day in range(NUM_DAYS):
                # Per-subject daily theory count
                subject_theory_count: dict[int, cp_model.IntVar] = {}
                subject_has_double: dict[int, cp_model.IntVar] = {}

                for sid in div.subject_ids:
                    subj = self.subjects_by_id.get(sid)
                    if not subj or subj.theory_hours <= 0:
                        continue

                    theory_vars = self._get_vars_for(
                        div_id=div.id, subject_id=sid, class_type="THEORY", day=day
                    )
                    if not theory_vars:
                        continue

                    # Count theory classes for this subject on this day
                    count_var = self.model.new_int_var(
                        0, min(subj.theory_hours, SLOTS_PER_DAY),
                        f"tc_d{div.id}_s{sid}_day{day}"
                    )
                    self.model.add(count_var == sum(theory_vars))
                    subject_theory_count[sid] = count_var

                    # Max 2 theory classes per subject per day
                    self.model.add(count_var <= 2)

                    # Boolean: does this subject have exactly 2 theory classes today?
                    has_double = self.model.new_bool_var(f"dbl_d{div.id}_s{sid}_day{day}")
                    self.model.add(count_var >= 2).only_enforce_if(has_double)
                    self.model.add(count_var <= 1).only_enforce_if(has_double.negated())
                    subject_has_double[sid] = has_double

                    # C8b: If double, they cannot be consecutive
                    # For each pair of adjacent slots, at most 1 theory class
                    for slot in range(SLOTS_PER_DAY - 1):
                        t1 = day * SLOTS_PER_DAY + slot
                        t2 = day * SLOTS_PER_DAY + slot + 1
                        vars_t1 = self._get_vars_for(
                            div_id=div.id, subject_id=sid, class_type="THEORY", timeslot=t1
                        )
                        vars_t2 = self._get_vars_for(
                            div_id=div.id, subject_id=sid, class_type="THEORY", timeslot=t2
                        )
                        if vars_t1 and vars_t2:
                            # At most 1 across both adjacent slots for this subject
                            self.model.add(sum(vars_t1) + sum(vars_t2) <= 1).only_enforce_if(has_double)

                # C8a: At most 1 subject can have double theory per day
                double_vars = list(subject_has_double.values())
                if double_vars:
                    self.model.add(sum(double_vars) <= 1)

    # -------------------------------------------------------------------
    # Objective function
    # -------------------------------------------------------------------

    def _add_objective(self):
        """Minimize total active days across all divisions.
        
        Y[d, day] = 1 if division d has any class on day.
        Link Y to X variables and minimize sum(Y).
        """
        for div in self.data.divisions:
            for day in range(NUM_DAYS):
                y = self.Y[(div.id, day)]
                day_vars = self._get_vars_for(div_id=div.id, day=day)

                if day_vars:
                    # Y >= any individual X (if any class is scheduled, day is active)
                    # Use add_max_equality: Y = max(all day_vars)
                    self.model.add_max_equality(y, day_vars)
                else:
                    self.model.add(y == 0)

        # Minimize total active days
        self.model.minimize(sum(self.Y.values()))

    # -------------------------------------------------------------------
    # Main solve method
    # -------------------------------------------------------------------

    def solve(self) -> SolverResult:
        """Build model, add all constraints, solve, and return results."""
        start_time = time.time()
        log_lines = []

        def log(msg: str):
            logger.info(msg)
            log_lines.append(msg)

        log("=== Timetable Solver Starting ===")
        log(f"Divisions: {len(self.data.divisions)}, Subjects: {len(self.data.subjects)}, "
            f"Faculty: {len(self.data.faculty)}, Rooms: {len(self.data.rooms)}")
        log(f"Theory rooms: {len(self.theory_rooms)}, Lab rooms: {len(self.lab_rooms)}")

        # 1. Create variables
        log("Creating decision variables (pruned)...")
        self._create_variables()
        log(f"  → {len(self.X)} assignment variables, {len(self.Y)} day variables")

        if not self.X:
            return SolverResult(
                status="ERROR",
                assignments=[],
                log="\n".join(log_lines) + "\nERROR: No valid assignment variables could be created.",
            )

        # 2. Add constraints
        log("Adding constraints...")

        log("  C1: Faculty clash...")
        self._add_faculty_clash_constraint()

        log("  C2: Division clash...")
        self._add_division_clash_constraint()

        log("  C3: Room clash (+ C4: type match enforced at var creation)...")
        self._add_room_clash_constraint()

        log("  C5: Curriculum fulfillment...")
        self._add_curriculum_constraint()

        log("  C6: Daily workload limit (≤ 8 hours)...")
        self._add_daily_workload_constraint()

        log("  C7: Maximum 1-hour break rule...")
        self._add_max_break_constraint()

        log("  C8: Double-theory subject limit...")
        self._add_double_theory_constraint()

        # 3. Objective
        log("Setting objective: minimize active days...")
        self._add_objective()

        # 4. Solve
        log(f"Solving with time limit {self.time_limit}s, {self.num_workers} workers...")
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = self.time_limit
        solver.parameters.num_workers = self.num_workers
        solver.parameters.log_search_progress = True

        status_code = solver.solve(self.model)
        wall_time = time.time() - start_time

        status_map = {
            cp_model.OPTIMAL: "OPTIMAL",
            cp_model.FEASIBLE: "FEASIBLE",
            cp_model.INFEASIBLE: "INFEASIBLE",
            cp_model.MODEL_INVALID: "ERROR",
            cp_model.UNKNOWN: "ERROR",
        }
        status = status_map.get(status_code, "ERROR")
        log(f"Solver status: {status} (wall time: {wall_time:.2f}s)")

        if status in ("OPTIMAL", "FEASIBLE"):
            obj_val = int(solver.objective_value)
            log(f"Objective value (total active division-days): {obj_val}")

            # Extract assignments
            assignments = []
            for (d, s, ctype, f, r, t), var in self.X.items():
                if solver.value(var) == 1:
                    assignments.append(ScheduledClass(
                        division_id=d,
                        subject_id=s,
                        class_type=ctype,
                        faculty_id=f,
                        room_id=r,
                        day=t // SLOTS_PER_DAY,
                        slot=t % SLOTS_PER_DAY,
                    ))

            # Count active days
            active_days = sum(
                1 for key, var in self.Y.items() if solver.value(var) == 1
            )
            log(f"Total scheduled classes: {len(assignments)}")
            log(f"Total active division-days: {active_days}")

            return SolverResult(
                status=status,
                assignments=assignments,
                objective_value=obj_val,
                total_active_days=active_days,
                wall_time=wall_time,
                log="\n".join(log_lines),
            )
        else:
            log("No feasible solution found.")
            return SolverResult(
                status=status,
                assignments=[],
                wall_time=wall_time,
                log="\n".join(log_lines),
            )
