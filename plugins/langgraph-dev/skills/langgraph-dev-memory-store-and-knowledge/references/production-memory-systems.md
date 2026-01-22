# Production Memory Systems with LangGraph Store

Comprehensive guide to scaling, securing, and optimizing memory systems for production deployment.

## Contents

1. [PostgreSQL-Backed Store](#postgresql-backed-store)
2. [Multi-User Isolation](#multi-user-isolation)
3. [Memory Pruning Strategies](#memory-pruning-strategies)
4. [Performance Tuning](#performance-tuning)
5. [Monitoring and Observability](#monitoring-and-observability)
6. [Security and Privacy](#security-and-privacy)

---

## PostgreSQL-Backed Store

### Why PostgreSQL for Production

**InMemorySaver Limitations**:
- ❌ Data lost on restart
- ❌ Single-process only (no horizontal scaling)
- ❌ No backup/recovery
- ❌ Limited to available RAM

**PostgresSaver Benefits**:
- ✅ Persistent across restarts
- ✅ Multi-process safe (connection pooling)
- ✅ Backup and recovery with PostgreSQL tools
- ✅ Scales beyond memory limits
- ✅ ACID transactions

### Setup

**Prerequisites**:
```bash
# Install PostgreSQL
brew install postgresql  # macOS
# or apt-get install postgresql  # Linux

# Install Python dependencies
pip install langgraph langchain-core psycopg[binary]
```

**Database Configuration**:
```sql
-- Create database
CREATE DATABASE langgraph_memory;

-- Create user (optional, for security)
CREATE USER langgraph_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE langgraph_memory TO langgraph_user;
```

**Python Implementation**:
```python
from langgraph.store.postgres import PostgresStore
import psycopg

# Connection string
connection_string = "postgresql://langgraph_user:secure_password@localhost:5432/langgraph_memory"

# Create connection
connection = psycopg.connect(connection_string)

# IMPORTANT: Create tables on first run
# from langgraph.store.postgres import PostgresStore
# PostgresStore.create_tables(connection)

# Create store
store = PostgresStore(connection)

# Use exactly like InMemoryStore
store.put(("memories", "user_123"), "key_1", {"text": "..."})
results = store.search(("memories", "user_123"), query="...")
```

### Connection Pooling

**Problem**: Creating new connections is slow, limits concurrent requests

**Solution**: Use connection pooling

```python
from psycopg_pool import ConnectionPool

# Create connection pool
pool = ConnectionPool(
    conninfo=connection_string,
    min_size=2,  # Minimum connections
    max_size=10,  # Maximum connections
    timeout=30,  # Connection timeout (seconds)
)

# Get connection from pool
with pool.connection() as conn:
    store = PostgresStore(conn)
    # Use store...
    # Connection automatically returned to pool
```

**Configuration**:
- `min_size`: Keep warm connections (reduce latency)
- `max_size`: Limit concurrent queries (prevent overload)
- `timeout`: Fail fast if pool exhausted

**Production Settings**:
```python
pool = ConnectionPool(
    conninfo=connection_string,
    min_size=5,   # 5 warm connections
    max_size=50,  # Handle 50 concurrent requests
    timeout=10,   # Fail after 10s wait
)
```

### Backup and Recovery

**Automated Backups**:
```bash
# Daily backup (cron job)
pg_dump langgraph_memory > backup_$(date +%Y%m%d).sql

# Backup with compression
pg_dump langgraph_memory | gzip > backup_$(date +%Y%m%d).sql.gz
```

**Point-in-Time Recovery**:
```bash
# Enable WAL archiving in postgresql.conf
wal_level = replica
archive_mode = on
archive_command = 'cp %p /path/to/archive/%f'
```

**Restore**:
```bash
# Drop and recreate database
dropdb langgraph_memory
createdb langgraph_memory

# Restore from backup
psql langgraph_memory < backup_20260113.sql
```

---

## Multi-User Isolation

### Namespace Design Patterns

**Pattern 1: User-Scoped Namespaces**

```python
def get_user_namespace(user_id: str, category: str) -> tuple:
    """
    Namespace pattern: (category, user_id)

    Ensures complete isolation between users.
    """
    return (category, user_id)

# Usage
alice_facts = get_user_namespace("user_alice", "facts")
bob_facts = get_user_namespace("user_bob", "facts")

# Alice and Bob's data completely isolated
store.put(alice_facts, "fact_1", {"text": "Alice's data"})
store.put(bob_facts, "fact_1", {"text": "Bob's data"})

# Searches only return user's own data
alice_results = store.search(alice_facts, query="...")  # Only Alice's data
```

**Pattern 2: Organization + User Hierarchy**

```python
def get_org_user_namespace(org_id: str, user_id: str, category: str) -> tuple:
    """
    Namespace pattern: (category, org_id, user_id)

    Enables organization-level and user-level queries.
    """
    return (category, org_id, user_id)

# Usage
acme_alice = get_org_user_namespace("org_acme", "user_alice", "memories")
acme_bob = get_org_user_namespace("org_acme", "user_bob", "memories")

# Query all users in organization
all_acme_memories = store.search(("memories", "org_acme"), query="...")

# Query specific user
alice_only = store.search(acme_alice, query="...")
```

### Access Control

**Pattern 1: Namespace-Based Access Control**

```python
class MemoryAccessControl:
    """Enforce user isolation with namespace validation."""

    @staticmethod
    def can_access(user_id: str, namespace: tuple) -> bool:
        """
        Check if user can access namespace.

        Rules:
        - Users can only access their own namespaces
        - Admins can access any namespace
        """
        # Extract user from namespace
        # Namespace format: (category, user_id, ...)
        if len(namespace) < 2:
            return False  # Invalid namespace

        namespace_user = namespace[1]

        # Check ownership
        return namespace_user == user_id

    @staticmethod
    def validate_and_search(
        store: BaseStore,
        user_id: str,
        namespace: tuple,
        query: str
    ):
        """Validated search with access control."""
        if not MemoryAccessControl.can_access(user_id, namespace):
            raise PermissionError(f"User {user_id} cannot access {namespace}")

        return store.search(namespace, query=query)

# Usage in API
@app.post("/search")
def search_memories(user_id: str, namespace: tuple, query: str):
    return MemoryAccessControl.validate_and_search(
        store, user_id, namespace, query
    )
```

---

## Memory Pruning Strategies

### Pattern 1: Time-Based Pruning

**Purpose**: Delete old memories to prevent unbounded growth

```python
from datetime import datetime, timedelta

def prune_old_memories(
    store: BaseStore,
    namespace: tuple,
    retention_days: int = 90
):
    """
    Delete memories older than retention period.

    Run periodically (e.g., daily cron job).
    """
    cutoff_date = datetime.now() - timedelta(days=retention_days)

    # Get all memories in namespace
    all_memories = list(store.search(namespace, limit=10000))

    deleted_count = 0
    for item in all_memories:
        created_at = item.value.get("created_at")
        if created_at:
            created_date = datetime.fromisoformat(created_at)
            if created_date < cutoff_date:
                store.delete(namespace, item.key)
                deleted_count += 1

    return deleted_count

# Schedule with cron
# 0 2 * * * python prune_memories.py  # Daily at 2 AM
```

### Pattern 2: Capacity-Based Pruning

**Purpose**: Limit total memories per user

```python
def enforce_memory_limit(
    store: BaseStore,
    namespace: tuple,
    max_memories: int = 1000
):
    """
    Keep only most recent N memories.

    Prevents users from consuming unlimited storage.
    """
    # Get all memories, sorted by timestamp
    all_memories = list(store.search(namespace, limit=max_memories + 100))

    # Sort by timestamp (newest first)
    sorted_memories = sorted(
        all_memories,
        key=lambda x: x.value.get("created_at", ""),
        reverse=True
    )

    # Delete oldest memories beyond limit
    if len(sorted_memories) > max_memories:
        to_delete = sorted_memories[max_memories:]

        for item in to_delete:
            store.delete(namespace, item.key)

        return len(to_delete)

    return 0
```

### Pattern 3: Importance-Based Pruning

**Purpose**: Prioritize keeping high-value memories

```python
def prune_by_importance(
    store: BaseStore,
    namespace: tuple,
    target_count: int = 500
):
    """
    Keep most important memories, delete low-importance.

    Importance factors:
    - Recency
    - User-marked importance
    - Access frequency
    """
    all_memories = list(store.search(namespace, limit=10000))

    # Score each memory
    scored = []
    for item in all_memories:
        score = 0

        # Recency score (0-1)
        created_at = datetime.fromisoformat(item.value.get("created_at", "2020-01-01"))
        days_old = (datetime.now() - created_at).days
        recency_score = max(0, 1 - (days_old / 365))  # Decay over year

        # Importance score (0-1)
        importance = {"low": 0.25, "medium": 0.5, "high": 1.0}
        importance_score = importance.get(item.value.get("importance", "medium"), 0.5)

        # Access frequency (if tracked)
        access_count = item.value.get("access_count", 0)
        access_score = min(1.0, access_count / 10)  # Cap at 10 accesses

        # Combined score
        score = (recency_score * 0.3) + (importance_score * 0.5) + (access_score * 0.2)

        scored.append((score, item))

    # Sort by score (descending)
    scored.sort(key=lambda x: -x[0])

    # Delete lowest-scored memories
    if len(scored) > target_count:
        to_delete = scored[target_count:]

        for _, item in to_delete:
            store.delete(namespace, item.key)

        return len(to_delete)

    return 0
```

---

## Performance Tuning

### Database Indexing

**Create Indexes for Namespace Queries**:

```sql
-- Index on namespace for faster searches
CREATE INDEX idx_store_namespace ON store_table USING GIN (namespace);

-- Index on created_at for time-based queries
CREATE INDEX idx_store_created_at ON store_table (created_at);

-- Composite index for namespace + created_at
CREATE INDEX idx_store_ns_created ON store_table (namespace, created_at);
```

**Analyze Query Performance**:

```sql
-- Explain query plan
EXPLAIN ANALYZE
SELECT * FROM store_table
WHERE namespace = '{"memories", "user_123"}'
ORDER BY created_at DESC
LIMIT 10;
```

### Query Optimization

**Pattern 1: Limit Namespace Scope**

```python
# ❌ Bad: Search all users
results = store.search(("memories",), query="...")  # Slow on large datasets

# ✅ Good: Search specific user
results = store.search(("memories", user_id), query="...")  # Fast
```

**Pattern 2: Use Pagination**

```python
def paginated_search(
    store: BaseStore,
    namespace: tuple,
    query: str,
    page: int = 1,
    page_size: int = 10
):
    """
    Paginate search results.

    Note: Offset-based pagination in vector search is inefficient.
    Consider cursor-based pagination for production.
    """
    offset = (page - 1) * page_size

    # Get results
    # Note: LangGraph Store may not support offset directly
    # Workaround: retrieve (offset + page_size) and slice
    results = list(store.search(namespace, query=query, limit=offset + page_size))

    return results[offset:offset + page_size]
```

### Caching Strategy

**Pattern 1: Application-Level Cache**

```python
import redis
import json

class RedisMemoryCache:
    """Cache Store search results in Redis."""

    def __init__(self, redis_url: str, ttl: int = 300):
        self.client = redis.from_url(redis_url)
        self.ttl = ttl  # Cache TTL in seconds

    def get(self, namespace: tuple, query: str):
        """Get cached results."""
        cache_key = f"search:{namespace}:{query}"
        cached = self.client.get(cache_key)

        if cached:
            return json.loads(cached)

        return None

    def set(self, namespace: tuple, query: str, results):
        """Cache search results."""
        cache_key = f"search:{namespace}:{query}"
        self.client.setex(
            cache_key,
            self.ttl,
            json.dumps(results, default=str)
        )

    def invalidate(self, namespace: tuple):
        """Invalidate cache for namespace."""
        pattern = f"search:{namespace}:*"
        for key in self.client.scan_iter(pattern):
            self.client.delete(key)

# Usage
cache = RedisMemoryCache("redis://localhost:6379", ttl=300)

def cached_search(store, namespace, query):
    # Check cache
    cached = cache.get(namespace, query)
    if cached:
        return cached

    # Search
    results = list(store.search(namespace, query=query))

    # Cache results
    cache.set(namespace, query, results)

    return results
```

---

## Monitoring and Observability

### Key Metrics

**Storage Metrics**:
- Total memories per user
- Total memories across all users
- Storage growth rate
- Database size

**Performance Metrics**:
- Search latency (p50, p95, p99)
- Embedding time
- Database query time
- Cache hit rate

**Usage Metrics**:
- Searches per second
- Memories created per day
- Active users
- Most searched queries

### Implementation

```python
import time
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
search_requests = Counter("memory_search_requests_total", "Total search requests")
search_latency = Histogram("memory_search_latency_seconds", "Search latency")
memories_total = Gauge("memories_total", "Total memories", ["namespace"])

def monitored_search(store, namespace, query):
    """Search with monitoring."""
    search_requests.inc()

    start = time.time()
    try:
        results = list(store.search(namespace, query=query))
        return results
    finally:
        search_latency.observe(time.time() - start)

def update_memory_count(store, namespace):
    """Update memory count metric."""
    count = len(list(store.search(namespace, limit=100000)))
    memories_total.labels(namespace=str(namespace)).set(count)
```

---

## Security and Privacy

### Data Encryption

**Encrypt at Rest (PostgreSQL)**:

```sql
-- Enable transparent data encryption (TDE)
-- Requires PostgreSQL with TDE extension
ALTER DATABASE langgraph_memory SET encrypt = on;
```

**Encrypt in Application**:

```python
from cryptography.fernet import Fernet

class EncryptedStore:
    """Wrapper for Store with client-side encryption."""

    def __init__(self, store: BaseStore, encryption_key: bytes):
        self.store = store
        self.cipher = Fernet(encryption_key)

    def put(self, namespace, key, value):
        """Encrypt value before storing."""
        encrypted_value = {
            k: self.cipher.encrypt(v.encode()).decode()
            if isinstance(v, str) else v
            for k, v in value.items()
        }
        return self.store.put(namespace, key, encrypted_value)

    def search(self, namespace, query, limit=10):
        """Decrypt results after search."""
        results = self.store.search(namespace, query=query, limit=limit)

        decrypted = []
        for item in results:
            decrypted_value = {
                k: self.cipher.decrypt(v.encode()).decode()
                if isinstance(v, str) else v
                for k, v in item.value.items()
            }
            decrypted.append(type(item)(
                key=item.key,
                value=decrypted_value,
                # ... other fields
            ))

        return decrypted
```

### PII Handling

**Pattern: Anonymization**

```python
import hashlib

def anonymize_user_id(user_id: str) -> str:
    """Hash user ID for privacy."""
    return hashlib.sha256(user_id.encode()).hexdigest()[:16]

# Use anonymized IDs in namespaces
namespace = ("memories", anonymize_user_id("user@example.com"))
```

---

## Production Checklist

- [ ] PostgreSQL configured with connection pooling
- [ ] Backup and recovery tested
- [ ] Multi-user isolation validated
- [ ] Memory pruning scheduled (cron jobs)
- [ ] Database indexes created
- [ ] Caching layer implemented
- [ ] Monitoring and alerting configured
- [ ] Encryption at rest enabled
- [ ] PII handling reviewed
- [ ] Load testing completed

---

## References

- [PostgreSQL Best Practices](https://wiki.postgresql.org/wiki/Performance_Optimization)
- [LangGraph Store API](https://langchain-ai.github.io/langgraph/reference/store/)
- See `SKILL.md` for basic Store setup
- See `examples/04_persistent_knowledge_agent.py` for integration patterns
- See `vector-search-patterns.md` for search optimization
