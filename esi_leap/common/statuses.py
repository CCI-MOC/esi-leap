# lease request statuses
PENDING = 'pending'      # requested but not fulfilled
FULFILLED = 'fulfilled'  # fulfilled and lease timer is running
DEGRADED = 'degraded'    # fulfilled but node(s) have been reclaimed by owner
EXPIRED = 'expired'      # fulfilled and has reached its expiration date
CANCELLED = 'cancelled'  # ended prematurely
DELETED = 'deleted'      # deleted
