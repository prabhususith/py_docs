<!--
Enterprise Architectural Comparison Matrix
==========================================
Description: Cross-ecosystem technical matrix comparing Python against Node.js/TypeScript
             and PHP across concurrency models, type systems, memory management, and frameworks.
Enterprise Mapping: Primary reference for Principal Architects transitioning from Fullstack
                    TypeScript or Enterprise PHP ecosystems.

Official Documentation References:
- Python Data Model: https://docs.python.org/3/reference/datamodel.html
- Python Concurrency Models: https://docs.python.org/3/library/concurrency.html
- Python Typing (PEP 484): https://peps.python.org/pep-0484/
- Node.js Architecture: https://nodejs.org/en/learn/asynchronous-work/event-loop-timers-and-nexttick
- PHP Runtime Architecture: https://www.php.net/manual/en/features.gc.php
-->

# Enterprise Architectural Matrix: Python vs TypeScript/Node.js vs PHP

This document provides a high-density, technical comparison across the three dominant enterprise backend environments.

---

## 1. Core Architectural Matrix

| Dimension | Modern Python (3.11+) | TypeScript / Node.js (20+) | Modern PHP (8.2+) |
|---|---|---|---|
| **Primary Execution Model** | Bytecode interpreted via CPython VM with optional JIT (3.13+) | JIT-compiled bytecode via Google V8 engine | Opcode cached (OPcache) executed via Zend VM |
| **Concurrency Core** | Single-threaded cooperative event loop (`asyncio`) + OS Threads (`threading`) + OS Processes (`multiprocessing`) | Single-threaded cooperative event loop (`libuv`) + Worker Threads (`worker_threads`) | Historically shared-nothing per-request process (PHP-FPM); modern coroutines via Swoole / RoadRunner |
| **Thread Locking** | Global Interpreter Lock (GIL) serializes bytecode (free-threading PEP 703 experimental in 3.13+) | Single execution thread per isolate; no shared memory lock needed; workers use `SharedArrayBuffer` with `Atomics` | Shared-nothing architecture; processes do not share state or require thread locks |
| **I/O Multiplexing** | OS native selectors (`epoll` on Linux, `kqueue` on BSD/macOS, `IOCP` on Windows) | Libuv cross-platform event loop abstraction | Handled by Web Server / FastCGI (Nginx/Apache), or event loop in Swoole |
| **Memory Management** | Immediate Reference Counting + Generational Cyclic Garbage Collector (3 generations) | Generational Tracing Mark-Sweep-Compact Garbage Collector (Scavenger + Mark-Sweep) | Request-scoped Arena Allocator (`Zend MM`), freed entirely upon request termination + cyclic GC |
| **Static Typing Mechanism** | Type hints (PEP 484, PEP 604) analyzed ahead-of-time via static linters (`mypy`, `pyright`, `ruff`); zero runtime overhead | Ahead-of-time compiler erased at transpile time (`tsc`); runtime reflection via `reflect-metadata` | Nominal, gradual runtime-enforced typing built into Zend engine (PHP 7/8) |
| **Interface / Contract Protocol** | Structural subtyping via `typing.Protocol` (PEP 544); duck typing with compile-time verification | Structural typing via `interface` / `type` | Nominal typing via explicit `interface` implementation (`class implements Interface`) |
| **Data Validation Standard** | Pydantic v2 (Rust-compiled `pydantic-core` executing RFC-compliant schema validation) | `zod`, `valibot`, `class-validator`, or `ajv` | Laravel FormRequests, Symfony Validator, or `webmozart/assert` |
| **Dominant Web Framework** | FastAPI (ASGI), Django Ninja, Starlette | NestJS, Express, Fastify, Hono | Symfony, Laravel (FPM or Octane), Slim |
| **ORM / Persistence Paradigm** | SQLAlchemy 2.0 (Data Mapper), Tortoise-ORM | Prisma, TypeORM, MikroORM, Drizzle | Doctrine ORM (Data Mapper), Eloquent (Active Record) |
| **Distributed Task Processing** | Celery + Redis / RabbitMQ, ARQ, Dramatiq | BullMQ (Redis streams), BeeQueue, Temporal | Laravel Queues (Redis/SQS), Symfony Messenger |
| **Package & Workspace Management** | `pip`, `venv`, `uv`, `poetry`, `pip-tools` | `npm`, `pnpm`, `yarn`, `bun` | `composer` |

---

## 2. In-Depth Concurrency Mental Model Mapping

### Scenario: Running 100 Concurrent HTTP Requests

#### 1. In TypeScript / Node.js
```typescript
// Promises execute immediately upon instantiation on the libuv event loop
const results = await Promise.all(urls.map(url => fetch(url)));
```
- **Execution Mechanism**: `Promise.all` registers non-blocking I/O callbacks in libuv's poll phase.
- **Backpressure**: Unbounded by default; requires third-party packages like `p-limit`.
- **Failure Mode**: If one rejects, `Promise.all` immediately rejects, but orphan requests continue running in the background unless paired with `AbortController`.

#### 2. In Modern Python (3.11+)
```python
# Structured Concurrency with TaskGroup
async with asyncio.TaskGroup() as tg:
    tasks = [tg.create_task(client.get(url)) for url in urls]
# Guarantees all tasks completed or cancelled cleanly before proceeding
results = [t.result() for t in tasks]
```
- **Execution Mechanism**: Coroutines scheduled as tasks on the active `asyncio` event loop.
- **Backpressure**: Controlled natively via `asyncio.Semaphore(10)`.
- **Failure Mode**: If one task raises an exception, **all sibling tasks are immediately cancelled**, preventing orphan microservice socket leaks.

#### 3. In PHP
- **Traditional PHP-FPM**: Each request runs sequentially within an isolated worker process. 100 requests require 100 PHP-FPM processes, consuming substantial memory.
- **Modern PHP with Swoole / Fiber**:
```php
$batch = [];
foreach ($urls as $url) {
    $batch[] = \Swoole\Coroutine\Http\get($url);
}
```

---

## 3. Structural Interfaces vs Nominal Interfaces

### TypeScript (Structural Subtyping)
```typescript
interface UserRepository {
  findById(id: string): Promise<User | null>;
}
// Any class with findById automatically satisfies UserRepository
class SqlUserRepository {
  async findById(id: string) { /* ... */ }
}
```

### Python (PEP 544 Structural Protocols)
```python
from typing import Protocol

class UserRepositoryProtocol(Protocol):
    async def find_by_id(self, user_id: str) -> User | None:
        ...

# No explicit inheritance needed! MyPy confirms compliance statically.
class SqlUserRepository:
    async def find_by_id(self, user_id: str) -> User | None:
        # Implementation satisfies the Protocol contract
        return None
```

### PHP (Nominal Typing)
```php
interface UserRepositoryInterface {
    public function findById(string $id): ?User;
}

// MUST explicitly declare 'implements'
class SqlUserRepository implements UserRepositoryInterface {
    public function findById(string $id): ?User { /* ... */ }
}
```
