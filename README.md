# Society Event Management System

The Society Event Management System is a web-based application designed to help societies and club manage their events efficiently.  
It supports **user** and **admin** modules for ticket booking, event management, and user administration, with features to prevent overbooking and enforce event-specific cancellation policies.

<img width="629" height="464" alt="image" src="https://github.com/user-attachments/assets/3ccf6469-5d51-435a-b6d9-44f571a88e0c" />

## Project Scope
- View Upcoming Events: Check event status, available capacity, and take actions as a member, non-member, or admin.
- User Module:
  - Register/Login/Logout
  - View & Edit Profile
  - Book Event Tickets
  - Cancel Tickets (within 24 hours for each event)
- Admin Module:
  - Login/Logout
  - Add, Edit, Delete Events
  - View Bookings
  - Manage Users
  - Prevent Overbooking
  - Remove Completed Events
  - Contact Us page for communication
  - Ticket Availability & Cancellation
  - Enforce 24-hour cancellation policy for each event

## Technology Stack

### Database System
- PostgreSQL: Stores data related to users, events, bookings, and artists.
#### ERD: 
<img width="316" height="570" alt="image" src="https://github.com/user-attachments/assets/3fa8eb2b-5a8b-434b-a3c4-34b1a7c6d7dc" />

### Backend Framework
- Python (Flask)
- Handling business logic, database connectivity, and API endpoints.

### Frontend Interface
- HTML, CSS, JavaScript
- Bootstrap for responsive UI design.

## Functional Hierarchy

### View Upcoming Events
- Check event status
- Available capacity
- Action buttons for booking/cancellation

### User Module
- Register/Login/Logout
- Book Ticket
- Cancel Ticket (within 24 hours)
- Edit Profile

### Admin Module
- Login/Logout
- Manage Events (Add/Edit/Delete)
- View Bookings
- Manage Users
- Remove Completed Events
- Contact Us page

## Installation

### 1. Setup Backend
```
python app.py
```
### 2. Setup Frontend
Simply open the index.html file in a browser, or serve via a local server.

### 3. Setup Database

- Install PostgreSQL.
- Create a new database.
- Import SQL schema from /database/schema.sql.

Developed complete workflow of the Project on Asana.
Can view it from here,
```
https://app.asana.com/1/1115985917195023/project/1210137583449009/timeline/1210137650611202
```
## Screenshots
<img width="620" height="404" alt="image" src="https://github.com/user-attachments/assets/a7f3dd56-6860-41c4-b4a3-9cd6843df747" />

<img width="620" height="404" alt="image" src="https://github.com/user-attachments/assets/352f5bff-1335-4d79-827c-67214a6b755e" />

