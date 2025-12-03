# Epic: Reserve Room

**As a** PTI, ADMIN  
**I want to** reserve rooms for activities  
**So that** I can ensure room availability and avoid scheduling conflicts

---

## Epic Summary

This epic covers the core room reservation functionality for the PTI Room Booking System. It enables PTI, ADMINs to view available rooms and their schedules, create new reservations, and manage existing bookings through modification or deletion. The system maintains data integrity through proper validation and prevents scheduling conflicts.

---

---

## Stories

### Story 1: View Room Calendar

**As a** PTI, ADMIN  
**I want to** view available rooms and their reservation schedules  
**So that** I can find a suitable room and time slot

#### Acceptance Criteria:
- Display weekly calendar view showing all rooms
- Show time slots from 06:00 to 18:00
- Display existing reservations on the calendar
- Color-code reservations by room type or status
- Navigate between weeks using Previous/Next buttons
- Switch between Weekly, Monthly, and List views
- Show room details (name, capacity, type) in calendar

#### Story Summary:
Provides users with a visual calendar interface to view room availability and existing reservations across all facilities.

---

### Story 2: Create Room Reservation

**As a** PTI, ADMIN  
**I want to** create a new room reservation  
**So that** I can book a room for my activity

#### Acceptance Criteria:
- Click "New Reservation" button to open booking form
- Select room from available rooms dropdown
- Choose date using date picker
- Select start time and end time
- Enter purpose/description of reservation
- Validate that room is available for selected time slot
- Prevent overlapping reservations for the same room
- Display confirmation message upon successful creation
- New reservation appears immediately on calendar

#### Story Summary:
Enables users to create new room reservations through a form with validation to prevent double-booking and ensure data completeness.

---

### Story 3: Delete Room Reservation

**As a** PTI, ADMIN  
**I want to** delete my room reservation  
**So that** I can free up the room when I no longer need it

#### Acceptance Criteria:
- Click on existing reservation in calendar to view details
- Display "Delete" button for reservations owned by current user
- Show confirmation dialog before deletion ("Are you sure you want to delete this reservation?")
- Remove reservation from database upon confirmation
- Update calendar view immediately after deletion
- Display success message after deletion
- Deleted slot becomes available for new bookings
- Admin users can delete any reservation

#### Story Summary:
Allows users to cancel their reservations through a simple deletion process with confirmation to prevent accidental cancellations.

---

### Story 4: View Reservation Details

**As a** PTI, ADMIN  
**I want to** view details of a reservation  
**So that** I can see who booked it and for what purpose

#### Acceptance Criteria:
- Click on any reservation block in the calendar
- Display modal/popup with reservation details:
  - Room name
  - Date and time (start - end)
  - Duration
  - Purpose/description
  - Created by (user name)
  - Created at (timestamp)
- Show "Delete" button if user owns the reservation or is admin
- Show "Close" button to dismiss the modal

#### Story Summary:
Provides detailed information about reservations when users click on calendar entries, enabling transparency and management actions.

---

## Stories Table

| Story ID | Story Name | Priority | Complexity | Dependencies |
|----------|------------|----------|------------|--------------|
| Story 1 | View Room Calendar | Must Have (P0) | Medium | None |
| Story 2 | Create Room Reservation | Must Have (P0) | Medium | Story 1 |
| Story 3 | Delete Room Reservation | Must Have (P0) | Low | Story 1, Story 4 |
| Story 4 | View Reservation Details | Must Have (P0) | Low | Story 1 |

---

## Technical Notes

**Database Schema:**
- Rooms table: id, name, capacity, type
- Reservations table: id, room_id, user_id, start_time, end_time, purpose, status, created_at

**Validation Rules:**
- Reservation duration: minimum 1 hour, maximum 8 hours
- Cannot create reservation in the past
- Cannot overlap with existing reservations for the same room
- Start time must be before end time

**Business Rules:**
- Users can only delete their own reservations (except admins)
- Admins can delete any reservation
- Deleted reservations are soft-deleted (status changed to 'cancelled')