-- Enum for spot status (idempotent)
DO $$ BEGIN
    CREATE TYPE spot_status AS ENUM ('open', 'closed');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Enum for bid status (idempotent)
DO $$ BEGIN
    CREATE TYPE bid_status AS ENUM ('pending_payment', 'paid', 'outbid_refunded', 'rejected_refunded', 'refund_failed');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Spots table
CREATE TABLE IF NOT EXISTS spots (
  id SERIAL PRIMARY KEY,
  position_name VARCHAR(100) NOT NULL UNIQUE,
  size VARCHAR(20) NOT NULL CHECK (size IN ('small', 'medium', 'large')),
  grid_area VARCHAR(50) NOT NULL,
  status spot_status NOT NULL DEFAULT 'open',
  closed_at TIMESTAMPTZ,
  winning_bid_id BIGINT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Bids table
CREATE TABLE IF NOT EXISTS bids (
  id BIGSERIAL PRIMARY KEY,
  spot_id INTEGER NOT NULL REFERENCES spots(id) ON DELETE CASCADE,
  bidder_name VARCHAR(100) NOT NULL,
  bidder_email VARCHAR(100) NOT NULL,
  logo_url VARCHAR(500),
  amount_ars INTEGER NOT NULL,
  status bid_status NOT NULL DEFAULT 'pending_payment',
  mp_preference_id VARCHAR(255),
  mp_payment_id VARCHAR(255) UNIQUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_bids_spot_id ON bids(spot_id);
CREATE INDEX IF NOT EXISTS idx_bids_mp_payment_id ON bids(mp_payment_id);
CREATE INDEX IF NOT EXISTS idx_bids_status ON bids(status);
CREATE INDEX IF NOT EXISTS idx_spots_status ON spots(status);

-- Lock down PostgREST (anon/authenticated). The backend connects as the table owner
-- over DATABASE_URL, which bypasses RLS, so no policies are needed.
ALTER TABLE spots ENABLE ROW LEVEL SECURITY;
ALTER TABLE bids ENABLE ROW LEVEL SECURITY;
