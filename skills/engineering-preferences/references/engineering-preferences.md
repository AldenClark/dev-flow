# Rust + 前端工程偏好目录

> 维护日期：2026-08-09
> 用途：作为 Rust 服务、跨平台客户端、管理控制台和文档站的项目初始化参考。
> 权威说明：`preference-registry.json` 是当前机器可读策略源；本文是便于阅读的展开目录，冲突时以前者为准。

## 目录

- [1-2 核心倾向与使用原则](#1-核心倾向)
- [3-11 Rust 依赖、算法、原语、性能与治理](#3-rust-强默认依赖)
- [12-15 Web、文档、门禁与包管理](#12-web-控制台默认栈)
- [16-18 CI、部署与工程文档](#16-ci构建与发布)
- [19-21 边界、决策顺序与维护](#19-不应自动继承的依赖)

## 1. 核心倾向

### Rust

- Rust 2024 edition，工具链固定在当前 1.97.x 基线；workspace 使用 resolver 3。
- 异步默认 `tokio`，数据模型默认 `serde` + `serde_json`，类型化错误默认 `thiserror`。
- HTTP 服务默认 `axum` + `tower`；HTTP 客户端默认 `reqwest` + Rustls。
- 服务可观测性默认 `tracing` + `tracing-subscriber`；CLI 默认 `clap` derive/env。
- 配置热更新倾向 `arc-swap`，同步锁倾向 `parking_lot`。
- 普通无序 Map 默认 `hashbrown::HashMap`；只有明确存在 HashDoS 风险时使用安全 hasher。时间日期默认 Jiff，Chrono 进入彻底淘汰与迁移策略。
- SQLite 单机状态倾向 `rusqlite`；多数据库服务按需使用 `sqlx`；Postgres 专用场景可使用 `tokio-postgres`。
- 紧凑二进制协议倾向 `postcard`，但对外 HTTP API 仍以 JSON 为默认。
- 原生桌面 UI 默认 GPUI + `gpui-component`，Slint 作为备选；不引入 Tauri、egui，也不把 Iced 列为默认备选。

### 前端

- 管理控制台默认 React + TypeScript + Vite。
- UI 与数据层倾向 Mantine + TanStack Router/Query/Table。
- API 倾向 OpenAPI 生成类型 + `openapi-fetch`，运行时输入边界使用 Zod。
- 单元/组件测试使用 Vitest + Testing Library，端到端使用 Playwright，并增加 axe 可访问性检查。
- 文档/开发者站默认 Astro + Starlight，图片处理使用 Sharp。
- 所有新项目统一使用 pnpm 11，并保证单一包管理器、单一权威锁文件。

## 2. 使用原则

- 先确定项目形态、运行环境、兼容性和风险，再选择依赖；不要把整套目录机械复制到所有项目。
- 优先使用语言和平台的原生能力；只有稳定能力边界、显著维护收益或经过测量的性能收益才引入依赖。
- 版本号是初始化基线，不是永久锁定值。创建项目、升级和发布前都要重新核对官方版本、维护状态、许可证与安全公告。
- 现有项目优先保持兼容和局部一致；任何迁移都应单独设计、验证并获得批准。

## 3. Rust 强默认依赖

| 依赖/设置 | 版本基线 | 默认用途 |
|---|---|---|
| Rust edition | 2024 | 所有新项目。 |
| `tokio` | 1.52–1.53 | 异步运行时，只开启实际需要的 features。 |
| `serde` | 1.0 | 数据模型序列化，常用 `derive`。 |
| `serde_json` | 1.0 | API、事件和配置的默认文本格式。 |
| `thiserror` | 2.0 | 库与领域层的类型化错误。 |
| `reqwest` | 0.13 | 出站 HTTP；关闭默认 features 后显式选择 Rustls。 |
| `parking_lot` | 0.12 | 同步锁；异步临界区仍优先 Tokio 原语。 |
| `postcard` | 1.1 | IPC、设备协议和紧凑持久化格式。 |

最小异步应用基线：

```toml
[package]
edition = "2024"
rust-version = "1.97"

[dependencies]
serde = { version = "1", features = ["derive"] }
serde_json = "1"
thiserror = "2"
tokio = { version = "1.53", features = ["macros", "rt-multi-thread", "signal"] }
tracing = "0.1"
tracing-subscriber = { version = "0.3", features = ["env-filter", "json"] }
```

版本是当前兼容基线，不是长期冻结要求。应用可以精确锁定直接依赖；公共库更适合声明兼容范围并由 `Cargo.lock` 保证可复现构建。

## 4. Rust 服务端组合

| 能力 | 推荐依赖 | 选择边界 |
|---|---|---|
| HTTP API / WebSocket | `axum` 0.8 + `tower` 0.5 | 服务端默认组合，按需启用 JSON、WebSocket 和 HTTP/2。 |
| HTTP 客户端 | `reqwest` 0.13 + Rustls | 显式启用 `json`、`stream`、`http2` 等所需能力。 |
| 日志与追踪 | `tracing` 0.1 + `tracing-subscriber` 0.3 | 新服务默认；逐步避免同一服务混用 tracing 与 env_logger。 |
| CLI | `clap` 4 | 常用 `derive`、`env`，并提供稳定 exit code 与机器可读输出。 |
| 动态配置 | `arc-swap` 1.9 | 适合读多写少的无锁配置快照。 |
| TLS | `rustls` 0.23 + `tokio-rustls` 0.26 | 显式统一 crypto provider、root store 和协议 features。 |
| WebSocket 客户端 | `tokio-tungstenite` | TLS roots 必须显式选择，并定义重连、背压和关闭策略。 |

服务参考依赖：

```toml
[dependencies]
arc-swap = "1.9"
axum = { version = "0.8", features = ["http2", "json", "ws"] }
clap = { version = "4.6", features = ["derive", "env"] }
reqwest = { version = "0.13", default-features = false, features = ["json", "rustls", "stream"] }
tower = "0.5"
tracing = "0.1"
tracing-subscriber = { version = "0.3", features = ["env-filter", "json"] }
```

## 5. Rust 按需依赖

| 场景 | 倾向 | 选择规则 |
|---|---|---|
| 原生桌面 UI | 首选 `gpui` + `gpui-component`；备选 Slint | 不引入 Tauri、egui，不把 Iced 列为默认备选；GPUI pre-1.0 需精确锁定，并在目标平台验证输入法、无障碍和窗口行为。 |
| CLI | Clap derive/env + `miette` | stdout 只放结果，stderr 放诊断；自动化提供稳定 JSON/JSONL、exit code 和错误码。 |
| TUI | Ratatui + 配套 Crossterm backend | 只有真正需要全屏状态与键盘工作流时引入；使用集中 event loop、有界通道、取消和终端恢复。 |
| QUIC | `quinn` 0.11 | 隧道或高性能传输才引入。 |
| SQLite | `rusqlite` 0.37–0.40，常用 `bundled` | 本地状态、桌面客户端和单机网关。 |
| 异步多数据库 | `sqlx` 0.8 | 需要连接池或 Postgres/MySQL/SQLite 多后端时采用。 |
| Postgres 专用 | `tokio-postgres` 0.7 | 只面向 Postgres 且希望直接控制驱动时采用。 |
| 并发 Map | 首选 `scc` 3；`dashmap` 6 为迁移/易用性备选 | 先证明共享 Map 是瓶颈；不要无理由同时使用两套，guard 不跨 `.await`。 |
| 时间与标识 | `jiff` 0.2、`uuid` 1 | 时间日期默认 Jiff，淘汰 Chrono；UUID 常用 `serde` 与 v4/v7。 |
| 密钥与敏感数据 | `zeroize`、`secrecy`、`subtle` | 按威胁模型采用；密码哈希用 `argon2`，不自创密码学组合。 |
| 测试临时资源 | `tempfile` 3 | 文件、SQLite、配置和进程集成测试。 |
| Android 平台 API | Kotlin 壳；按需 `jni` / `ndk` | Kotlin 持有 Activity/Service/WorkManager/permission 生命周期；Rust 绑定只放在 Android 边界 crate。 |
| Apple 平台 API | Swift/ObjC 壳；按需 `objc2` | Swift/ObjC 持有 app/extension、entitlement、后台任务和 ServiceManagement 生命周期；Rust 绑定只放在 Apple 边界 crate。 |
| Windows FFI | `windows` / `windows-sys` | 只放在 Windows 平台层。 |
| Windows 长期 agent | SCM + `windows-service` | 正确上报 service 状态，支持 stop 与有截止时间的 drain；周期性短任务改用 Task Scheduler。 |
| Linux 长期服务 | 前台进程 + systemd/supervisor | 不默认自行 double-fork；只有明确需要 notify/watchdog/socket activation 时引入 `sd-notify`。 |

### FFI 边界选型

- 按边界而不是按仓库选择方案：低中频类型化控制面优先 UniFFI；Apple 高频数据面、Kotlin/Native 和长期稳定 ABI 使用版本化 C ABI + cbindgen/稳定头文件；Android 高频路径或直接平台调用使用 registered JNI + `jni`。
- Rust core 负责可移植业务、协议、状态机与数据处理；Swift/Kotlin 壳负责 UI、系统 API、权限和 app/extension/service 生命周期。跨进程只能使用版本化 IPC，不能传 pointer、JNI reference 或进程内 handle。
- C ABI 使用固定宽度整数、`repr(C)`、ABI major/minor、capability handshake 与 generation-checked opaque handle；Rust 分配由 Rust 释放，不暴露 Rust `String`、`Vec`、引用、trait object、`usize` 或默认布局类型。
- `close()` 显式且幂等，遵循 `OPEN -> CLOSING -> CLOSED`，等待 in-flight call、buffer lease 和 callback 静默后再销毁。异步完成、错误、取消、超时和 owner closed 必须 exactly once。
- 发布验证以最终 XCFramework/AAR/APK/AAB 为准，覆盖符号、架构、loader、R8、CheckJNI、sanitizer、竞态、进程恢复和真实设备；未执行项标记 `NOT RUN`。

## 6. 密码学、安全与通用算法

依赖按用途引入，不建立所有项目统一安装的“密码学包”或“算法工具包”。协议已经规定算法时，优先协议互操作性。

### 密码、KDF 与消息认证

| 用途 | 默认倾向 | 关键边界 |
|---|---|---|
| 密码存储 | `argon2` 0.5 / Argon2id + PHC string | 每条记录独立 CSPRNG salt；参数按目标硬件和并发测量，登录成功时按策略 rehash。 |
| 口令派生加密密钥 | Argon2id 的 key-derivation API | 与密码验证使用不同 salt、上下文和输出，不能复用密码哈希。 |
| 高熵材料派生子密钥 | `hkdf` 0.13 + SHA-256 | 使用稳定且唯一的 `info` 做 domain separation；不能替代密码拉伸。 |
| 共享密钥消息认证 | `hmac` 0.13 + SHA-256 | 使用库的常量时间 verify API，禁止普通 `==` 比较 tag。 |

PBKDF2、scrypt 只用于既有协议或平台兼容。pepper 仅在 KMS/HSM 独立保管且具备版本、轮换和灾备方案时采用。

### 加密、签名与密钥交换

- 无协议、FIPS 或硬件约束的应用内部封套优先 XChaCha20-Poly1305；需要标准互操作、硬件加速或 FIPS 路径时使用 AES-256-GCM；协议规定时采用标准 ChaCha20-Poly1305 等协议算法。
- 同一 key 下 nonce 绝不重复。密文携带 schema version、algorithm、key ID、nonce、ciphertext/tag；AAD 绑定 tenant、对象 ID、用途与 schema version。
- 新建应用级离线签名默认 `ed25519-dalek` 3；P-256/ECDSA 用于 WebAuthn、平台硬件、FIPS 或标准兼容；RSA 仅用于遗留互操作或验证既有签名。签名输入必须版本化、canonical 并带 domain tag。
- X25519 只在已认证的标准协议中采用，共享秘密经 HKDF。网络会话优先 TLS 1.3、Noise/HPKE 等成熟实现，不自行拼装握手协议。

### 随机数、token 与 secret

- 普通抽样用 `rand` 0.10；密钥、salt、nonce、重置码和 bearer token 使用 OS CSPRNG，由密码 crate 的安全生成 API 或 `getrandom` 0.4 提供。seeded RNG 只用于测试、模拟和非安全算法。
- opaque bearer token 默认 32 个随机字节，以 Base64 URL-safe no-padding 编码。服务端保存 SHA-256 摘要；需要抵抗数据库泄露后的离线枚举时保存带服务端密钥的 HMAC，并记录用途、主体、过期和撤销信息。
- `secrecy` 控制显式暴露，`zeroize` 清理可控缓冲区，敏感比较使用原语 verify 或 `subtle`。UUID、时间戳、递增 ID 和非密码哈希都不能作为 secret。
- secret 禁止进入 Debug、日志、trace baggage、metrics label、panic/error chain、URL/query、前端 bundle 和持久崩溃报告。

### 哈希、校验与标识符

| 用途 | 默认 | 禁止误用 |
|---|---|---|
| 协议互操作、制品完整性、安全摘要 | SHA-256 / `sha2` | 攻击者能同时修改内容和摘要时，必须改用签名或 HMAC。 |
| 内部内容寻址、去重和大文件 hash | `blake3` | 固化为跨系统协议前先确认互操作。 |
| 偶发损坏检测 | `crc32c` | 不防恶意篡改。 |
| 可信输入高速指纹、分片或缓存键 | `xxhash-rust` / XXH3 | 禁止用于密码、token、MAC、签名、安全完整性或不可碰撞 ID。 |
| 数据库时间有序 ID | UUIDv7 | 可泄露时间属性，不是 secret。 |
| 普通公开随机 ID | UUIDv4 | 授权凭证另用 256-bit opaque token。 |

普通 Map 默认 `hashbrown::HashMap`。只有能够被攻击者低成本、大量构造 key，且威胁模型确有 HashDoS 风险时，才改用 `std::HashMap` 的安全默认值或显式安全 hasher；安全选择必须在边界上可识别，不能依赖隐含约定。

### 编码、压缩与归档

- 二进制转文本用 `base64`：URL/cookie/token 使用 URL-safe no-padding；标准协议严格遵循其 alphabet/padding；面向人的短诊断值可用 hex。编码不是加密，解码前限制长度并使用 canonical representation。
- 内部文件、备份和大块传输优先 Zstd；HTTP/遗留互操作用 gzip；静态 Web 资源可预生成 Brotli 并保留 gzip fallback；低延迟且压缩率次要、经基准证明后才使用 LZ4 frame。
- Unix/内部制品优先 tar + Zstd；Windows 或终端用户交换包使用 ZIP 并关闭不需要的 features。ZIP 自带加密不作为通用安全封装。
- 不可信解包必须流式处理，限制输入/输出/单文件大小、条目数、压缩比、嵌套深度和时间；拒绝绝对路径、`..`、设备文件及危险链接，并使用隔离临时目录和原子提交。高风险场景额外使用 capability API 或 OS sandbox 防 TOCTOU。
- 不对混合攻击者可控内容与 secret 的响应启用动态压缩。

### 文本与常用数据算法

- 不可信文本正则默认 `regex`；多模式、DFA 或序列化 automata 才使用 `regex-automata`，并限制 pattern、DFA、文本和匹配数量。回溯型正则仅处理可信、有界 pattern，并设置时间/步数限制。
- Unicode 归一化由领域决定；通常明确选 NFC，只有产品语义允许兼容折叠时才用 NFKC/case folding。安全标识符禁止 locale-dependent lowercase 和显示层模糊等价。
- 模糊匹配和编辑距离只用于 UI 搜索、提示与排序，禁止用于认证、授权、签名主体、安全规则或主键去重。
- 标准库的排序、二分查找、heap 和 BTree 优先；普通 Map 优先 `hashbrown`。需要稳定插入序用 `indexmap`；已测得短序列占绝大多数才用 `smallvec`；密集 bit 用 `bitvec`，稀疏整数集合用 `roaring`，图算法用 `petgraph`，CPU-bound 数据并行用 `rayon`。异步 I/O 仍使用 Tokio。
- 特化数据结构和并行化必须有真实数据分布与基准，并明确内存上限、确定性、取消和错误传播。

## 7. Rust 基础类型、集合与系统原语

### 集合与 Map

- 顺序容器默认 `Vec`；队列/双端队列使用 `VecDeque`，优先队列使用 `BinaryHeap`，成员集合使用 `HashSet`，排序/范围集合使用 `BTreeSet`。`LinkedList` 不作为常规候选。
- `SmallVec` 只在小集合分配确为热点且基准有效时使用；协议或资源有固定硬上限时用 `ArrayVec` 并处理满容量；`heapless` 只用于 `no_std`、硬实时或禁止 allocator 的环境。
- 普通无序 Map 默认 `hashbrown::HashMap`；需要排序、范围或规范遍历时用 `BTreeMap`；插入顺序属于产品语义时用 `IndexMap`。需要 HashDoS 防护时使用 `std::HashMap` 或显式安全 hasher。
- 共享 Map 依次评估 owner task、`parking_lot::Mutex<hashbrown::HashMap<...>>`、经测量的 `RwLock`、`scc::HashMap`；`DashMap` 仅作迁移/易用性备选。使用 `entry` 避免双重查找，Map 中 key 的 `Eq`/`Hash` 不得改变。
- 所有容器定义容量、增长和超限策略；不信任外部长度提示，不在热路径无条件 `shrink_to_fit`。

### 稳定句柄、arena 与分配

- 不删除、不重排的局部句柄使用 `Vec + index`；内部短期可复用键用 `slab`；句柄逃逸且需防陈旧键/ABA 时用 `slotmap`，迭代密集时用 `DenseSlotMap`。
- `bumpalo` 只用于 AST、解析批次等阶段性整体释放对象；不能假定 reset 会为普通对象执行 `Drop`，文件、锁、secret 等 RAII 资源不放入裸 arena。
- 默认系统 allocator；mimalloc/jemalloc 等只有生产 profile 证明延迟、RSS 或碎片收益后按 binary/平台采用。跨 FFI 或动态库内存由分配它的模块释放。

### 共享状态、通道与异步流

- 所有权/借用优先；不可变共享用 `Arc`，复合不变量短同步更新用 `parking_lot::Mutex`。`RwLock` 仅在读多写少且测量胜出时采用；锁必须跨 `.await` 才使用 Tokio 锁。
- 原子只表达可独立证明的标量或状态机，并记录 ordering；多字段不变量使用锁或 owner task。读多写少不可变快照用 `ArcSwap`。
- Tokio owner-task 工作队列默认有界 `mpsc`；一次响应用 `oneshot`，最新状态用 `watch`，允许 lag 的多播用 `broadcast`，资源许可用 `Semaphore`，`Notify` 只负责唤醒。同步 MPMC/select 用有界 `crossbeam-channel`。
- 无界 channel 必须证明输入有界或具备落盘/丢弃策略；队列观测容量、深度、等待和丢弃。未知长度 `Stream` 禁止无上限 `collect`。

### 字节、字符串与 I/O

- 输入优先 `&str`/`&[u8]`；可变所有权用 `String`/`Vec<u8>`，不可变固定所有权用 `Box<str>`/`Box<[u8]>`，跨任务共享用 `Arc<str>`/`Arc<[u8]>`。`Cow` 只用于通常借用、偶尔转换的真实路径。
- 网络帧与协议缓冲使用 `Bytes/BytesMut`；长期保存巨大 backing buffer 的极小 slice 时先复制。文件/流式 I/O 默认 `BufReader/BufWriter`，所有读取、逐行与聚合有字节/条数上限。
- `smol_str` 只用于测得的小字符串 clone/hash 热点；`memmap2` 只映射生命周期内不会被截断或并发改写的受控大文件。

### 时间、路径与文件系统

- 耗时、超时和 deadline 使用 `Duration + Instant`；`SystemTime` 只用于 OS 时间戳和 epoch 转换。时间日期统一使用 Jiff，包括 timestamp、IANA 时区、民用日期、DST 和日历运算。
- Chrono 从新项目和新代码中彻底淘汰；旧代码迁移到 Jiff。第三方若只能提供 Chrono 类型，只允许在 adapter 边界即时转换，不进入 domain 或新公共 API。轻量 `no_std`/协议场景确有需要可用 `time`，但同一 domain 只保留一种日期类型。
- 持久化事件时间使用 UTC instant；未来民用时间语义还需保存本地值和 IANA zone ID。明确 DST 歧义、精度、舍入、epoch 与单位；异步 timer 用 `tokio::time`，测试使用 paused time 或可注入 clock。
- OS 路径默认 `Path/PathBuf`；明确 UTF-8 契约才用 `camino`。普通递归用 `walkdir`，仓库/ignore-aware 扫描用 `ignore`；限制根、深度、条目数、文件大小和符号链接。
- `notify` 事件仅作提示，debounce/coalesce 后重读真实状态，并有轮询/溢出恢复。临时文件用 `tempfile`；持久原子替换按需执行同目录 staging、file fsync、rename 和 directory fsync。`fs4` 只做同机合作进程 advisory lock，不当分布式锁。

### 解析、数值、所有权与系统接口

- 简单格式用 `FromStr`/标准库，结构化格式用 Serde；新建完整自定义解析器优先 Winnow，流式/partial/`no_std` 用 Nom，PEG/DSL 用 Pest，lexer 用 Logos。URL、HTTP、CIDR、MIME、ID、端口、字节数和持续时间使用强类型/newtype。
- 协议和持久化整数明确位宽，默认 checked arithmetic。固定精度金额用“最小货币单位整数 + currency newtype”；可变十进制、税率和利率用 `rust_decimal`，禁止通过浮点往返。浮点排序用 `total_cmp`，`NotNan`、BigInt、`uom` 按领域需要引入。
- 借用优先；`Box` 表达唯一堆所有权，`Rc<RefCell<_>>` 限单线程边界，跨线程共享用 `Arc`，环与订阅用 `Weak`。同步无参延迟初始化用 `LazyLock`，运行期参数用 `OnceLock`，异步用 Tokio `OnceCell`，避免隐藏式全局 service locator。
- 同步子进程用 `std::process::Command`，异步用 `tokio::process::Command`；参数不拼 shell，显式治理 cwd、环境、stdio、输出上限、超时、kill tree 和 reap。`xtask` 编排优先 `xshell`，复杂同步 pipeline 才用 `duct`；Unix/Windows 底层 API 分别隔离使用 `rustix` 与 `windows`/`windows-sys`。

## 8. Rust 高级性能与硬件能力

这些能力不是默认依赖包，而是 profile 证据驱动的升级阶梯。

### SIMD 与 CPU 指令集

- 优化顺序为：算法/数据布局/批量接口 → 已内置 SIMD 的成熟 crate → LLVM 自动向量化 → `pulp`/`wide` → `std::arch`。搜索、UTF-8、哈希等优先采用 `memchr`、`simdutf8`、BLAKE3 等已有运行时分派的实现。
- 跨 x86_64/AArch64 的新手写 SIMD 内核优先 `pulp`；固定宽度向量、接受编译期能力和标量 fallback 时可用 `wide`；依赖自动向量化的函数多版本使用 `multiversion`。同一 kernel 只保留一套分派框架。
- `std::simd`/portable SIMD 在稳定前不进入产品默认；`std::arch` 仅用于其他抽象无法表达且实测有收益的内部小模块，并保留 scalar reference path。
- 测试覆盖 tail、未对齐、所有指令集和 scalar 路径；浮点 SIMD/FMA/reduction 的精度与确定性必须显式，不能改变金额、协议和安全语义。
- 通用制品使用最低 CPU baseline + 函数级运行时分派；`target-cpu=native` 仅用于构建/运行机器一致或 CPU 受严格控制的部署，更推荐可复现的命名 CPU profile。全局 `target-feature` 不作为默认。

### 数据布局、并行与 NUMA

- profile 判断计算、分支或内存瓶颈后，再选择 AoS/SoA、hot/cold 分离、紧凑元素和批处理。`CachePadded`/显式 alignment 仅用于已测得的 false sharing，避免无谓增加 footprint/TLB 压力。
- 协议/文件 typed view 优先 `zerocopy` 受检 derive；GPU/数值 POD cast 优先 `bytemuck` derive；`rkyv` 仅用于 schema 受控的本地 cache/archive/mmap，并启用 `bytecheck`、格式版本和迁移。禁止不可信 unchecked access。
- CPU-bound 批处理使用容量受控的专用 Rayon pool，线程数取实际 quota；避免 Tokio、`spawn_blocking`、Rayon 和第三方库过度订阅。小任务保留串行路径，需要确定性时固定 reduction 顺序。
- CPU affinity、优先级和 NUMA 默认关闭；固定拓扑且硬件计数器证明需要时，简单场景使用平台 API/`core_affinity`，拓扑、cache、异构核心和 NUMA 感知才评估 `hwlocality`，并保留无法绑定时的正确 fallback。

### 无锁结构与高性能 I/O

- 并发原语优先 owner task、锁、`scc`/Crossbeam；自研 lock-free 仅在锁竞争已成为主瓶颈时允许，并定义 linearization、progress、ABA、reclamation、饥饿和 backoff。epoch 回收使用 `crossbeam-epoch` 专家 API；`portable-atomic` 仅用于目标原子能力不足、`no_std` 或所需 128-bit fallback。
- 自研 unsafe/无锁结构采用 Loom、Miri、TSAN、压力和故障注入组合验证，并接受独立安全审查；工具不能替代内存顺序与安全证明。
- 跨平台 I/O 默认 Tokio；先采用批量、缓冲、`Bytes`、vectored I/O 和平台 copy。`tokio-uring` 只用于固定 Linux 基线且 syscall/copy 已被 profile 证明为瓶颈的专用服务。
- 底层 `io-uring`、fixed buffers、SQPOLL 和 Direct I/O 仅限专家模块，处理 completion buffer ownership、短 I/O、队列饱和、取消竞态、fd 生命周期、对齐、内核 probe、seccomp 和 durability；保留普通 I/O fallback 或明确 Linux-only。

### GPU、LTO、PGO 与优化制品

- GPU 只用于可批量并行且能摊销传输/dispatch 的任务，并先建立 CPU SIMD/Rayon 基线。跨平台 compute 首选 `wgpu`；仅 NVIDIA 且需要 CUDA 专属库时采用隔离 CUDA adapter。必须有 CPU fallback、批量阈值、feature/limit 协商和 device-lost/OOM 处理。
- 普通 release 候选为 `opt-level = 3` + ThinLTO；fat LTO 与 `codegen-units = 1` 仅在基准证明收益且接受构建成本后采用。默认发布 `release-portable`，按需增加命名 CPU/`release-native` 制品。
- 稳定、高流量、具有代表性 workload 的二进制可用 rustc PGO/`cargo-pgo`；训练覆盖启动、正常、错误和长尾路径，并检查 stale/missing profile。BOLT 仅用于 PGO 后仍存在 code-layout/i-cache 瓶颈的 Linux/ELF 专项优化。
- 每个优化制品记录 source SHA、rustc/LLVM、target、CPU baseline、features、linker、PGO profile ID 和 benchmark；保留符号或独立 debug artifact，并与普通制品做正确性及性能 A/B。

## 9. Rust 扩展、IPC、资源治理与可验证执行

### 宏、build.rs 与代码生成

- 函数、trait、泛型和 const generic 优先，其次 `macro_rules!`；只有 derive/attribute、Rust syntax 检查或真正 DSL 才使用 proc macro。默认 `proc-macro2 + quote + syn`，薄 macro crate，解析/生成核心放普通 library，使用 `trybuild` 验证成功和失败诊断。
- `build.rs` 只用于原生编译/发现、链接或构建必需代码生成；仅写 `OUT_DIR`，精确声明 rerun 输入与 `rustc-check-cfg`，区分 HOST/TARGET，不联网、不读 secret、不改源码并遵循 Cargo jobserver。
- 提交生成代码时使用 `cargo xtask codegen`/独立工具，固定生成器版本和 schema/IDL，CI 重新生成并要求 clean diff。公共 macro 语法、生成项、诊断、feature 与 MSRV 均视为 API/SemVer 契约。

### 插件与 Wasm/WASI

- 插件选择顺序：编译期 feature/trait → 子进程 + 版本化 IPC → Wasm Component → 可信 native dynamic plugin。需要第三方/不可信及跨语言扩展时优先 Wasmtime + Component Model + WIT；浏览器 Rust/Wasm 使用 `wasm-bindgen`，不走嵌入式 Wasmtime。
- native plugin 使用版本化 C ABI、function table 和 capability handshake，不暴露 Rust ABI/trait object/`String`/`Vec`/allocator。`abi_stable` 只在接受其类型和生态约束时采用，`libloading` 仅为底层 loader。native library 默认不在进程生命周期内卸载。
- plugin manifest 记录 ID、接口版本、OS/arch、capabilities、publisher、digest/signature 和最低 host；加载使用可信绝对路径并防 search-path hijacking，调用有 timeout、取消、并发/内存预算与审计。
- Wasm guest 默认无 ambient authority，只注入获准的文件、网络、clock、random、env 和 host functions；同时限制 memory/table/instance、host allocation、fuel/epoch、wall timeout、async yield、并发和输出。host call 自身也有取消和超时。
- WIT world/resource/error 带版本，artifact cache 绑定 Wasmtime、target、CPU、WIT 和配置；Wasm 默认用于规则、转换和控制面，热数据面必须用 workload 基准证明。

### 本地 IPC 与共享内存

- 简单父子流程使用 stdin/stdout pipe；长期控制面使用 Unix domain socket/Windows named pipe，跨平台封装可选 `interprocess`。协议包含 length framing、magic/version、最大 frame、request ID、deadline、取消、稳定错误、heartbeat/reconnect 和背压。
- endpoint 放在权限受控 namespace，验证 ACL、ownership 和可用的 peer credentials/token；本机不等于可信。Payload 继续按 JSON/Postcard/Protobuf 边界选择，分配前先验证 frame 长度。
- 大型高频 payload 且复制成为瓶颈时才采用共享内存，优先 `iceoryx2` 而不是自建裸协议。共享数据只使用 offset/handle、固定 layout/endian/generation 与显式 ownership/reclamation，禁止共享 pointer、引用、普通 Rust layout、进程内 mutex 或 allocator 对象。
- 定义进程崩溃、lease、容量耗尽、版本不兼容与清理恢复，并保留 socket 控制面和可诊断 fallback。

### 资源治理、确定性与高级验证

- 长期进程为连接、请求、任务、队列、buffer/cache、文件、子进程、数据库和外部 API 设置预算。Tower 服务使用 `ConcurrencyLimit + bounded Buffer + LoadShed`，内部资源使用 Tokio `Semaphore`；时间速率配额才使用 `governor`，keyed limiter 必须回收 key。
- 不可信处理器优先低权限进程/容器，文件能力使用 `cap-std`；Linux 按需使用 Landlock/seccomp/cgroup，其他平台使用原生 sandbox adapter。必须验证实际 enforcement；不支持时 fail closed 或明确告警降级。
- 需要回放的逻辑注入 clock、RNG、ID 和外部结果。跨版本随机回放使用固定算法/seed 的 `rand_chacha`，不依赖 `StdRng`；bundle 记录 schema、输入顺序、clock、非敏感 seed、配置和 build ID，并治理 PII/secret、大小、保留、加密和审计。
- Property、fuzz、Miri、Loom 和 Kani 分层使用：Kani 只证明边界有限且价值高的纯逻辑、unsafe、整数/layout/状态性质；超时、不支持或达到资源上限不算通过。新 verifier 不设全局默认，unsafe 的 `SAFETY` 不变量必须链接到对应证据。

## 10. 正式领域能力包（按需启用）

下列六类已确认为正式选型分类，但不是所有项目的默认依赖；进入对应领域后才启用：

- 科学与数值计算：按小型几何矩阵、N 维数组、中大型线性代数、FFT/DSP 分开选型，候选为 `nalgebra`、`ndarray`、`faer`、`rustfft`。
- 图像与音视频：静态图像、音频解码/设备 I/O/重采样、通用视频管线、平台硬件媒体和浏览器媒体分层，候选为 `image`、`symphonia`、`cpal`、`rubato`、FFmpeg/GStreamer 与平台 API。
- 嵌入式与 `no_std`：以 `embedded-hal` 为 driver 边界，在 Embassy 与 RTIC 间按调度模型选择，使用静态有界内存、`probe-rs` 和 `defmt`。
- ML 推理与训练：按 ONNX 互操作、纯 Rust CPU、Hugging Face/生成式模型、Rust-native 训练选择 `ort`、tract、Candle 或 Burn；一个模型只保留一个主 runtime。
- Linux eBPF：Rust-first 候选 Aya，既有 C/libbpf CO-RE 生态候选 `libbpf-rs`；必须治理 verifier、内核/权限矩阵、map/event 生命周期和 userspace fallback。
- 共识与 CRDT：优先复用现有存储一致性；应用级 Raft 候选 OpenRaft/raft-rs，local-first 按 Loro/Yrs/Automerge 的数据类型和互操作需求选型，CRDT 不承担全局强不变量。

高级规则见本目录第 8 至 10 节。除非项目进入相应领域，这些依赖不得被基础脚手架自动安装。

## 11. Rust 工程治理倾向

- workspace 根集中声明共享依赖与 lint，成员使用 `workspace = true`。
- `rust-toolchain.toml` 使用 minimal profile，并安装 `rustfmt`、`clippy`。
- 所有产品仓库提交 `Cargo.lock`，CI 使用 `cargo ... --locked`。
- 普通 release 候选使用 `opt-level = 3` + ThinLTO；fat LTO、`codegen-units = 1`、PGO 和 allocator 调整必须由目标负载 profile/A-B 数据决定。
- `panic = abort` 只适用于不需要跨 FFI unwind 的最终二进制；JNI、Swift/Objective-C 回调和其他 FFI 边界必须单独制定 panic 策略。
- 严格 lint：unsafe 禁止或集中审计，Clippy correctness/perf/suspicious 提升等级。
- TLS provider、root store、协议版本和 features 必须显式选择。
- 领域 crate 不直接依赖 JNI、ObjC、Windows API 或具体 UI 框架。

## 12. Web 控制台默认栈

新的管理控制台默认采用：

| 层次 | 依赖倾向 | 当前基线 |
|---|---|---|
| 框架 | React + React DOM | 19.2 |
| 语言 | TypeScript | 5.9 |
| 构建 | Vite + React plugin | 7.3 / 5.1 |
| UI | Mantine Core/Hooks/Notifications | 8.3 |
| 图标 | Tabler Icons React | 3.36 |
| 路由 | TanStack Router | 1.x |
| 服务端状态 | TanStack Query | 5.x |
| 表格 | TanStack Table | 新项目默认 9.1 |
| API 类型 | OpenAPI TypeScript + `openapi-fetch` | 7.x / 0.15 |
| 运行时校验 | Zod | 4.x |
| 单元/组件测试 | Vitest + Testing Library + jsdom | 4.x / 16.x / 28.x |
| E2E | Playwright | 1.x |
| 可访问性 | axe-core Playwright | 4.x |
| 代码质量 | ESLint 9 + typescript-eslint | 9.x / 8.x |

参考依赖轮廓：

```json
{
  "dependencies": {
    "@mantine/core": "^8",
    "@mantine/hooks": "^8",
    "@mantine/notifications": "^8",
    "@tanstack/react-query": "^5",
    "@tanstack/react-router": "^1",
    "openapi-fetch": "^0.15",
    "react": "^19",
    "react-dom": "^19",
    "zod": "^4"
  },
  "devDependencies": {
    "@axe-core/playwright": "^4",
    "@playwright/test": "^1",
    "@testing-library/react": "^16",
    "@vitejs/plugin-react": "^5",
    "eslint": "^9",
    "openapi-typescript": "^7",
    "typescript": "~5.9",
    "vite": "^7",
    "vitest": "^4"
  }
}
```

该片段表达选型，不应直接当作 lockfile。初始化时应以目标 Node 版本解析依赖、完成测试后提交锁文件。

## 13. 文档站默认栈

新的文档站默认采用：

- `astro` 6：静态内容和文档站框架。
- `@astrojs/starlight` 0.39：开发者文档主题与信息架构。
- `sharp` 0.34：构建期图片处理。

适合产品文档、API 指南、下载说明和 SEO 内容。它不是管理控制台的替代方案；需要登录态、复杂表格和实时交互时仍使用 React 控制台栈。

## 14. 前端工程门禁

新控制台最低门禁：

1. `type-check`：TypeScript project build。
2. `lint`：ESLint 零 warning。
3. `test`：Vitest 单元/组件测试。
4. `e2e`：Playwright smoke，必要时拆分 read-only 与 writable 套件。
5. `accessibility`：Testing Library + axe/Playwright。
6. `build`：生产构建。
7. `api-contract`：OpenAPI 生成结果与代码同步检查。
8. 项目专用合同：本地化、数量/金额语义、UI 系统等检查脚本。

文档站最低门禁：内容/SEO 生成检查 + Astro build + 链接与发布验证。

## 15. 包管理与版本治理

- 所有新项目统一使用 pnpm 11，在 `package.json` 写明精确 `packageManager` 和 `engines.node`，提交 `pnpm-lock.yaml`。
- pnpm CI 使用 `pnpm install --frozen-lockfile`；现有 npm 项目在显式迁移前继续使用 `npm ci`，不在一次无关变更中混换包管理器。
- 每个独立 Git 根只保留一种包管理器和一个权威 lockfile。
- 编译器、API 生成器、协议工具等关键工具适合精确或窄范围锁定。
- 安全修复可使用 `overrides`，但应注明原因并在上游版本修复后清理。
- 创建项目时依据所选 Vite/Astro 的 engines 选择并固定 Node 主版本，不从传递依赖反推一个永久 Node 基线。

## 16. CI、构建与发布

- 默认 GitHub Actions，并把 PR 验证、release、deployment 分为不同信任域。workflow 默认只读权限，第三方 Action 固定完整 commit SHA；PR 取消同分支旧任务，release 不得被新任务中断。
- 应用使用锁定的当前 stable Rust；只有公开 library 或明确承诺 MSRV 时增加 MSRV job。Rust 使用 `--locked`/`--frozen`，pnpm 使用 frozen install；cache 仅用于加速，不允许不可信 PR 写入 release 会恢复的 cache。
- 容器默认 BuildKit named multi-stage + cache mount；不默认引入 cargo-chef，只有测得依赖重编译瓶颈时才采用。联网服务优先 glibc slim；完全静态且已验证运行需求时可用 scratch；Alpine/musl 必须有兼容性和性能依据。
- runtime 使用非 root 固定 UID/GID、最小文件、明确 writable volume 和 OCI source/version/revision 标签。release 路径固定 toolchain、关键工具及 builder/runtime image digest。
- 只构建产品承诺的架构；常见服务为 `linux/amd64` + `linux/arm64`。各架构分别测试后再组装 manifest；QEMU 不作为性能结论依据。
- 发布遵循 SemVer 和人工整理的 changelog/release notes。Rust crate 先执行 `cargo publish --dry-run`；pnpm 11.13+ workspace 优先原生 `pnpm change` + `pnpm version -r`，不默认增加 Changesets CLI。
- candidate 生成 checksum、SBOM、provenance、签名和最终制品验证记录；staging/production 晋级同一不可变 artifact/image digest，不按环境重新 build。签名与部署凭证优先 OIDC/trusted publishing，并只在受保护环境中提供。
- 自动更新按需引入。独立分发必须验证签名 manifest 和 artifact hash，支持原子替换、last-known-good、分批发布、暂停与回滚。

## 17. 部署默认阶梯

- 静态控制台/文档站：对象存储或静态托管 + CDN；hashed assets 长缓存，HTML/manifest 短缓存或 revalidate；整目录原子发布并保留上一版本。
- 单机 Rust 服务/agent：原生二进制 + hardened systemd unit。
- 多个紧密相关服务或本地交付包：Docker Compose，固定 image digest、持久卷、健康检查、资源限制、日志与备份；禁止把开发 bind mount 和默认 secret 带入生产。
- Kubernetes 只在多节点、高可用副本、自动伸缩、多租户或既有集群平台确有需要时采用；无状态用 Deployment，需要稳定身份/存储才评估 StatefulSet。普通 manifests/Kustomize 优先，Helm 只用于可复用产品 chart 或重参数化安装。
- 各环境晋级同一不可变制品。配置与 secret 外置；服务支持 startup/readiness/liveness、终止信号和有上限的 graceful drain；migration 使用独立受控 job、并发锁与 expand/contract。
- 默认 rolling update。只有具备真实流量切分、指标判定和快速回退时才采用 canary/blue-green；成功条件包含 rollout 收敛、关键 smoke、错误率/延迟与观测窗口。

## 18. 工程文档基线

- 最低信息包括 README、开发/贡献命令、架构与关键数据流、安全边界、CHANGELOG/RELEASE_NOTES；小项目可以合并文件，但不创建空文档。
- ADR 只记录长期影响架构、协议、数据、安全、部署或依赖策略的决定，包含状态、背景、决定、替代方案、后果和验证；新决策 supersede 旧 ADR，不静默改写历史。
- 文档按 tutorial、how-to、reference、explanation 分类。Rust 公共 API 使用 rustdoc 与 doctest；协议/API reference 从权威 schema 生成；少量内部文档优先仓库 Markdown，规模扩大后使用 Astro + Starlight。
- 生产服务维护部署/回滚、备份/恢复、migration、secret/证书轮换、容量、告警和常见故障 runbook，并记录 owner、适用版本和 last verified。
- 认证、网络协议、密钥、不可信输入、FFI、跨进程或敏感数据边界维护轻量 threat model。CI 检查链接、示例/schema 和文档站 build；同一事实只保留一个权威来源。

## 19. 不应自动继承的依赖

- 本地 patch crate、兼容 wrapper 和 fork：它们是项目级修复，不是通用默认。
- QUIC、VPN、JNI、Apple/Windows FFI、桌面 UI、SQLite、多数据库、加密算法，以及科学计算、媒体、嵌入式、ML、eBPF、共识/CRDT 领域包：仅在产品能力需要时引入。
- 同一模块内重复引入多套并发 Map、日志、TLS、UI 或状态管理方案。
- 没有明确能力需求、维护收益或测量依据的依赖不得自动加入脚手架。

## 20. 新项目决策顺序

1. 确定项目类型：Rust 服务、daemon/agent、后台任务、CLI/TUI、协议/FFI 库、原生客户端、Web 控制台或文档站；再判断是否进入科学计算、媒体、嵌入式、ML、eBPF、共识/CRDT 等领域。
2. 套用对应的最小强默认基线。
3. 只有出现明确能力需求时才加入数据库、QUIC、FFI、桌面 UI 等组件。
4. 固定工具链与 lockfile，建立 lint/type-check/test/build/API 合同门禁。
5. 选择最简单可满足需求的发布与部署阶梯，并在上线前验证升级、回滚、备份恢复和最终制品。
6. 上线前重新核对直接依赖版本、维护状态、许可证与安全公告。

## 21. 维护规则

本目录表达默认方向和选择边界，不替代当前事实核验。创建项目、升级依赖和准备发布时，应从官方文档、注册表、维护仓库和安全公告重新核对版本、兼容性、许可证与维护状态。

如果当前项目约束与目录冲突，优先满足正确性、安全、协议、平台和兼容性要求，并把偏离默认的理由记录在项目设计中。
