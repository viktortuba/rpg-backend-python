# RPG Backend — Requirements

Game system for a fictional RPG video game done for entry test.

## Overview

In this project, you will develop a game system for a fictional RPG video game. In this game, players can create characters and venture into the world, where they can acquire gear and engage in combat with other players.

This system must be scalable to support a large number of players, so we will use a **microservice architecture**. During the analysis process, the following services were identified:

1. **Account Service**
2. **Character Service**
3. **Combat Service**

All services should be implemented using **Python** and **FastAPI**, each managing its own PostgreSQL database and schema. Define each schema using migrations, which should run at service startup.

## Tech Stack

- **Python**, **FastAPI**
- **PostgreSQL** for persistent storage
- **Redis** for caching
- **Docker Compose** for provisioning

> **Note:** No UI is required for this system, but example test scripts or Postman collection would be appreciated. You may structure the code in a single or multiple repositories.

---

## Services

### 1. Account Service

This service handles user registration and login. It provides an API that issues JWT tokens (via username/password). The JWT token should contain a user role (either **User** or **GameMaster**) and be required for requests to other services as a Bearer token.

---

### 2. Character Service

The Character Service allows registered users to create and manage their characters. This is where core game logic is implemented.

#### Entities

**1. Character:** Represents a character in the game world
- `id`: Unique identifier
- `name`: Unique string
- `health`, `mana`, `baseStrength`, `baseAgility`, `baseIntelligence`, `baseFaith`: Integers for stats
- `class`: Associated character class
- `items`: List of items held by the character
- `createdBy`: User ID of the character's owner

**2. Class:** Defines character classes (e.g., 'Warrior', 'Rogue')
- `id`: Unique identifier
- `name`: Unique string
- `description`: Description of the class

**3. Item:** Items that characters can wield to boost stats
- `id`: Unique identifier
- `name`, `description`: Strings (name should update based on largest stat bonus)
- `bonusStrength`, `bonusAgility`, `bonusIntelligence`, `bonusFaith`: Stat bonuses (integers)

> **Stats:** Strength, agility, intelligence, and faith. Players can hold multiple instances of the same item.

#### Implementations

**1. Database Initialization:** Apply migrations and seed the database with initial data.

**2. API Endpoints:**

- `GET /api/character` - Lists all characters with names, health, and mana (restricted to Game Masters)
- `GET /api/character/{id}` - Retrieves character details, including calculated stats and associated items (available to Game Masters and character owners). Cache the result, and invalidate it upon changes
- `POST /api/character` - Creates a new character with specified attributes (available to all users)
- `GET /api/items` - Lists all items (restricted to Game Masters)
- `POST /api/items` - Creates a new item
- `GET /api/items/{id}` - Retrieves item details. Determine item name suffix based on highest bonus stat
- `POST /api/items/grant` - Assigns an item to a character
- `POST /api/items/gift` - Transfers an item from one character to another

**3. Unit Tests:** Implement tests for a few operations (just to see some examples, no need for 100% code coverage)

**4. Bonus:**
- Validate user ID in the JWT during character creation
- Add logging

---

### 3. Combat Service

The Combat Service handles player duels, allowing characters created in the Character Service to battle and potentially win items.

#### Combat Logic

Players can choose one of three actions per turn:

- **Attack:** Inflicts damage based on `strength + agility`, available every second
- **Cast:** Inflicts damage based on `2 * intelligence`, available every two seconds
- **Heal:** Restores health based on `faith`, available every two seconds

Combat continues until a player's health reaches zero. If a duel exceeds 5 minutes, it ends in a draw. The winner receives a random item from the defeated player.

#### Implementations

**1. Database Initialization:** Sync with the Character Service to ensure characters are aligned.

**2. API Endpoints:**

- `POST /api/challenge` - Initiates a duel between two characters (only the character owner can initiate)
- `POST /api/{duel_id}/attack` - One character attacks another (restricted to duel participants)
- `POST /api/{duel_id}/cast` - One character casts a spell (restricted to duel participants)
- `POST /api/{duel_id}/heal` - One character heals (restricted to duel participants)

**3. Synchronization:** Ensure the database syncs with the Character Service when needed (e.g., on registration)

**4. Duel Outcome Notification:** Notify the Character Service to update items when a duel concludes

**5. Bonus:** Add logging

---

## General Requirements

1. **Docker:** Use Docker Compose for service provisioning, with configurations for PostgreSQL, Redis
2. **Caching:** Implement Redis-based caching where specified
3. **Testing:** Write unit tests for some endpoints
