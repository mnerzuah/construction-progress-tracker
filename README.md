# Construction Progress Tracker

## Overview

Construction Progress Tracker is a lightweight web application designed to simplify schedule-based progress tracking on construction projects.

The application allows project teams to import schedule activities, record field progress, and compare actual completion against planned progress without requiring Primavera P6, BIM models, or complex project controls software.

The goal is to provide a simple, field-friendly solution for superintendents, subcontractors, project managers, commissioning teams, and owners.

---

## MVP Features

### Schedule Import

* Upload schedule exports from Excel or CSV files.
* Validate required schedule fields.
* Create project activities automatically from the schedule.

### Progress Capture

Users update progress through the following workflow:

1. Select Discipline
2. Select Package
3. Select Room / Location
4. Select Activity
5. Enter Percent Complete
6. Add Notes (optional)
7. Save Update

### Progress Tracking

Track:

* Actual Progress
* Planned Progress
* Activity Status
* Discipline Progress
* Package Progress
* Room Progress

### Verification Workflow

When an activity reaches 100% completion, it is not automatically considered complete.

Instead, it enters:

**Pending Verification**

This allows the General Contractor, Owner, or Project Administrator to verify completion before the dashboard reflects the activity as complete.

---

## Required Schedule Fields

The following fields are required:

| Field         |
| ------------- |
| Activity ID   |
| WBS Location  |
| Activity Name |
| Discipline    |
| Package       |
| Start         |
| Finish        |

Optional:

| Field    |
| -------- |
| Critical |

---

## Future Features

### Phase 2

* Progress Dashboard
* Planned vs Actual Reporting
* Critical Path Tracking
* Weekly Progress Reports

### Phase 3

* Photo Attachments
* Field Notes
* Mobile Interface
* User Permissions

### Phase 4

* Logistics Tracking
* Safety Tracking
* Commissioning Tracking

### Phase 5

* Primavera P6 Integration
* Microsoft Project Integration
* Procore Integration
* Autodesk Construction Cloud Integration

---

## Technology Stack

* Python
* Streamlit
* Pandas
* Plotly
* OpenPyXL

---

## Current Status

This project is currently in MVP development and is intended for testing, validation, and pilot deployment on active construction projects.

---

## License

All rights reserved.
