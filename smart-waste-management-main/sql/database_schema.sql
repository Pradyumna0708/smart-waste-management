-- ==========================================
-- SMART WASTE MANAGEMENT SYSTEM
-- Database Schema for SQLite (waste_management.db)
-- ==========================================

-- Table to store historical waste data from all simulated bins
CREATE TABLE IF NOT EXISTS waste_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bin_id TEXT NOT NULL,          -- Unique ID of the bin (e.g., BIN001)
    fill_level INTEGER NOT NULL,    -- Current fill percentage (0 to 100)
    weight INTEGER NOT NULL,        -- Weight of waste in kg
    latitude REAL NOT NULL,         -- GPS Latitude coordinate
    longitude REAL NOT NULL,        -- GPS Longitude coordinate
    timestamp TEXT NOT NULL,        -- Time when record was logged (YYYY-MM-DD HH:MM:SS)
    status TEXT NOT NULL            -- Calculated status (Normal, Warning, Critical)
);

-- Index to optimize historical searches and reporting by bin and time
CREATE INDEX IF NOT EXISTS idx_waste_data_bin_timestamp ON waste_data (bin_id, timestamp);
